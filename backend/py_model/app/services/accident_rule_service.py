from collections import defaultdict

# =========================
# 사고 관련 클래스
# =========================
ACCIDENT_RELATED_CLASSES = {
    "Bumper",
    "Fender",
    "Light",
    "Bonnet",
    "Windshield",
    "Door",
    "CAR_TRUNK-KP48",
    "Dickey",
}

MIN_CONF_FOR_ACCIDENT = 0.2

# 사고 유형
FRONT = "FRONT_COLLISION"
REAR = "REAR_COLLISION"
SIDE = "SIDE_COLLISION"
COMPLEX = "COMPLEX_DAMAGE"
UNKNOWN = "UNKNOWN"

# =========================
# region + part 점수 규칙 (현실 보정)
# =========================
SCORE_RULES = {
    # REAR (약화)
    ("rear", "Trunk"): {REAR: 1.2},
    ("rear", "Bumper"): {REAR: 1.5},
    ("rear", "Light"): {REAR: 0.8},
    ("rear", "Fender"): {REAR: 0.8},

    # SIDE (강화)
    ("side", "Door"): {SIDE: 2.2},
    ("side", "Fender"): {SIDE: 2.0},
    ("side", "Bumper"): {SIDE: 1.5},
    ("side", "Light"): {SIDE: 1.2},

    # FRONT (유지)
    ("front", "Bumper"): {FRONT: 1.2},
    ("front", "Fender"): {FRONT: 1.5},
    ("front", "Light"): {FRONT: 1.2},
}

# =========================
# part 단독 증거 (후방 확정 제거)
# =========================
PART_ONLY_RULES = {
    "Bonnet": {FRONT: 3.5},
    "Windshield": {FRONT: 3.5},
    "Door": {SIDE: 2.5},
}

SIDE_PART_BONUS = {
    "Door": 1.5,
    "Fender": 1.2,
}


def normalize_part_name(part: str) -> str:
    if part in {"CAR_TRUNK-KP48", "Dickey"}:
        return "Trunk"
    return part


# =========================
# 점수 계산
# =========================
def estimate_accident_scores(detections: list) -> dict:
    scores = defaultdict(float)

    for d in detections:
        part = normalize_part_name(d.get("class_name"))
        region = d.get("region")
        conf = d.get("confidence", 0.0)

        if not part or not region:
            continue

        # part 단독 규칙
        if part in PART_ONLY_RULES:
            for t, base in PART_ONLY_RULES[part].items():
                scores[t] += base * conf

        # region + part 규칙
        key = (region, part)
        if key in SCORE_RULES:
            for t, base in SCORE_RULES[key].items():
                scores[t] += base * conf

        # SIDE 보너스
        if part in SIDE_PART_BONUS and region == "side":
            scores[SIDE] += SIDE_PART_BONUS[part] * conf

    return dict(scores)


# =========================
# 방향 결정 가능 여부 (강화)
# =========================
def can_decide_direction(scores: dict) -> bool:
    if not scores:
        return False

    values = sorted(scores.values(), reverse=True)

    # 최소 증거 기준 상향
    if values[0] < 2.5:
        return False

    # 점수 차이 기준 강화
    if len(values) >= 2 and (values[0] - values[1]) < 1.5:
        return False

    return True


# =========================
# 최종 사고 유형 판단
# =========================
def estimate_accident_type(
    detections: list,
    mode: str = "single"  # "single" | "multi"
) -> dict:
    valid_detections = [
        d for d in detections
        if d.get("class_name") in ACCIDENT_RELATED_CLASSES
        and d.get("confidence", 0.0) >= MIN_CONF_FOR_ACCIDENT
    ]

    damage_count = len(valid_detections)

    if damage_count == 0:
        return {
            "accident_detected": False,
            "accident_state": "NO_ACCIDENT",
            "accident_type": UNKNOWN,
            "confidence_level": "LOW",
            "scores": {},
            "message": "파손이 명확하게 탐지되지 않았습니다."
        }

    scores = estimate_accident_scores(valid_detections)

    regions = {d.get("region") for d in valid_detections if d.get("region")}
    has_front = "front" in regions
    has_rear = "rear" in regions

    # =========================
    # 사고 상태 (현실 보정)
    # =========================
    if damage_count >= 3 or len(regions) >= 2:
        state = "CONFIRMED_ACCIDENT"
    else:
        state = "SUSPECTED_ACCIDENT"

    # =========================
    # 사고 유형 판단
    # =========================
    if state != "CONFIRMED_ACCIDENT":
        accident_type = UNKNOWN

    elif mode == "multi" and has_front and has_rear:
        accident_type = COMPLEX

    elif can_decide_direction(scores):
        top = max(scores, key=scores.get)

        # SIDE 증거가 충분하면 REAR 단독 확정 방지
        if (
            top == REAR
            and SIDE in scores
            and scores[SIDE] >= scores[REAR] * 0.7
        ):
            accident_type = SIDE
        else:
            accident_type = top

    else:
        accident_type = UNKNOWN

    # =========================
    # 신뢰도
    # =========================
    if damage_count >= 4:
        confidence_level = "HIGH"
    elif damage_count >= 2:
        confidence_level = "MEDIUM"
    else:
        confidence_level = "LOW"

    # =========================
    # 메시지
    # =========================
    if state == "CONFIRMED_ACCIDENT":
        if accident_type == COMPLEX:
            message = "동일 차량에서 여러 방향의 파손이 확인되어 복합 파손 사고로 판단됩니다."
        elif accident_type != UNKNOWN:
            message = "사고 방향이 비교적 명확하게 확인되었습니다."
        else:
            message = "사고는 확인되었으나 방향 판단에는 추가 정보가 필요합니다."
    else:
        message = "파손은 확인되었으나 사고 여부는 불확실합니다."

    return {
        "accident_detected": state == "CONFIRMED_ACCIDENT",
        "accident_state": state,
        "accident_type": accident_type,
        "confidence_level": confidence_level,
        "scores": scores,
        "message": message
    }
