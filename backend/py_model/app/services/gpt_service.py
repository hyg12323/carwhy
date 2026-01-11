import os
from dotenv import load_dotenv
from openai import OpenAI

# ======================================================
# 🔒 GPT 사용 토글
# ======================================================
GPT_ENABLED = True # 충전 전 False 권장

load_dotenv()


def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY가 설정되지 않았습니다.")
    return OpenAI(api_key=api_key)


# ======================================================
# 🔧 내부 유틸: YOLO 파손 부위 정규화
# ======================================================
def extract_damaged_parts(yolo: dict):
    """
    프론트 YoloTab / DamageTab 에서 쓰는 구조 그대로 파손 부위 추출
    """
    if not yolo:
        return []

    vehicles = yolo.get("vehicles", [])
    parts = set()

    for v in vehicles:
        for d in v.get("damages", []):
            name = d.get("class_name")
            if name:
                parts.add(name)

    return list(parts)


# ======================================================
# 1️⃣ GPT 결과 설명 (탭별)
# ======================================================
def generate_gpt_solution(
    accident: dict = None,
    yolo: dict = None,
    drivable: dict = None,
    mode: str = "OVERALL",  # ACCIDENT | YOLO | DRIVABLE | OVERALL
):
    if not GPT_ENABLED:
        return {"gpt_summary": "[GPT OFF - 테스트 모드]"}

    client = get_openai_client()

    accident = accident or {}
    yolo = yolo or {}
    drivable = drivable or {}

    # ==================================================
    # 🚦 사고판단 탭
    # ==================================================
    if mode == "ACCIDENT":
        accident_detected = accident.get("accident_detected", False)
        accident_type = accident.get("accident_type", "UNKNOWN")
        confidence = accident.get("confidence_level", "LOW")
        scores = accident.get("scores", {})

        system_prompt = (
            "너는 차량 사고 분석 결과를 사용자에게 "
            "사람처럼 차분하게 설명해주는 AI다."
        )

        prompt = f"""
이번 차량 이미지 분석 결과를 바탕으로 사고 여부를 설명해줘.

- 사고 여부: {"사고로 인식됨" if accident_detected else "사고로 인식되지 않음"}
- 사고 유형: {accident_type}
- 판단 신뢰도: {confidence}

사고 유형별 점수 분포는 다음과 같아:
{scores}

이 점수들이 왜 이런 판단으로 이어졌는지,
전문가가 설명하듯 자연스럽게 풀어서 말해줘.
"""

    # ==================================================
    # 🛠 YOLO 파손부위 탭
    # ==================================================
    elif mode == "YOLO":
        damaged_parts = extract_damaged_parts(yolo)

        system_prompt = (
            "너는 차량 외관 파손 분석 결과를 "
            "사진을 보며 설명해주는 전문가다."
        )

        prompt = f"""
외관 파손 분석 결과를 설명해줘.

감지된 파손 부위는 다음과 같아:
{", ".join(damaged_parts) if damaged_parts else "뚜렷하게 감지된 파손 부위는 없음"}

이 부위들이 왜 파손으로 인식되었는지,
형태 변화나 시각적 특징을 중심으로
사람이 이해하기 쉽게 설명해줘.
"""

    # ==================================================
    # 🚗 주행 가능 탭 (CNN)
    # ==================================================
    elif mode == "DRIVABLE":
        drivable_flag = drivable.get("drivable")
        reason = drivable.get("drivable_reason", "unknown")

        if drivable_flag is None:
            drivable_flag = False

        system_prompt = (
            "너는 차량 이미지 전체를 입력으로 사용하는 "
            "CNN 기반 주행 가능 판별 모델의 판단 근거를 "
            "사용자에게 설명해주는 AI다."
        )

        prompt = f"""
다음은 CNN 모델의 주행 가능 판별 결과다.

- 최종 판별 결과: {"주행 불가" if not drivable_flag else "주행 가능"}
- 모델 내부 판단 코드: {reason}

이 CNN 모델은 다음과 같은 특징을 가진다:
- 사고 유형이나 충돌 방향을 판단하지 않는다
- 파손 부위를 구분하지 않는다
- 차량 이미지 전체에서 학습된 시각적 패턴을 기준으로 판단한다

아래 기준으로만 설명해줘:

1️⃣ 이미지에서 정상 주행 차량과 다른 시각적 특징이 무엇이었는지  
2️⃣ 차체 형태, 구조적 왜곡, 비정상적인 윤곽이 어떻게 감지되었는지  
3️⃣ 이러한 시각적 패턴이 왜 주행 위험 신호로 해석되었는지  
    그리고 결론을 내줘 주행가능 주행불가

❗ 사고 위치, 충돌 방향, 특정 부위 명칭은 절대 언급하지 마라.  
❗ CNN 모델의 판단 관점에서만 설명해라.
"""

    # ==================================================
    # 📊 종합 탭 (OVERALL)  ✅ 여기만 수정됨
    # ==================================================
    else:
        accident_detected = accident.get("accident_detected", False)
        accident_type = accident.get("accident_type", "UNKNOWN")
        confidence = accident.get("confidence_level", "LOW")

        damaged_parts = extract_damaged_parts(yolo)

        # ✅ FIX 1: drivable_flag 정확히 추출
        drivable_flag = drivable.get("drivable")
        if drivable_flag is None:
            vehicles = drivable.get("vehicles", [])
            if vehicles:
                drivable_flag = vehicles[0].get("drivable")

        if drivable_flag is None:
            drivable_flag = "UNKNOWN"

        system_prompt = (
            "너는 차량 사고 분석 결과를 종합해 "
            "운전자에게 종합 리포트를 설명해주는 전문가다."
        )

        # ✅ FIX 2: 판단 문자열 분기 정확화
        prompt = f"""
다음은 차량 분석 시스템의 전체 결과야.
이 내용을 바탕으로 종합 분석 리포트를 작성해줘.

[사고 판단]
- 사고 여부: {"사고로 판단됨" if accident_detected else "사고로 단정되지는 않음"}
- 사고 유형: {accident_type}
- 판단 신뢰도: {confidence}

[외관 파손 분석]
- 감지된 파손 부위:
{", ".join(damaged_parts) if damaged_parts else "뚜렷한 외관 파손은 확인되지 않음"}

[주행 가능 판단]
- 주행 가능 여부: {
    "주행 가능" if drivable_flag is True
    else "주행 불가" if drivable_flag is False
    else "판단 불가"
}

아래 형식으로, GPT가 설명해주듯 자연스럽게 작성해줘:

1️⃣ 종합 요약  
2️⃣ 세부 분석 설명  
3️⃣ 점검이나 수리가 필요할 수 있는 부분  
4️⃣ 사용자에게 권장되는 다음 단계
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        temperature=0.35,
    )

    return {"gpt_summary": response.choices[0].message.content.strip()}


# ======================================================
# 2️⃣ 사용자 추가 질문
# ======================================================
def generate_gpt_followup(
    gpt_summary: str,
    question: str,
):
    if not GPT_ENABLED:
        return {"answer": "[GPT OFF - 테스트 모드]"}

    client = get_openai_client()

    prompt = f"""
아래는 이미 생성된 차량 종합 분석 리포트이다.
이 리포트의 내용은 확정된 분석 결과이며,
새로운 판단이나 재분석은 절대 하지 마라.

[종합 분석 리포트]
{gpt_summary}

사용자 질문:
{question}

반드시 다음 기준을 지켜서 답변하라:
- 위 종합 분석 리포트 내용과 **모순되지 않게**
- 새로운 사고 판단, 수리 여부 판단을 추가하지 말 것
- 사용자의 질문에 대해 리포트를 **보충 설명**하는 방식으로 답할 것
- 상담사처럼 차분하고 현실적으로 설명할 것
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "너는 차량 사고 종합 분석 리포트를 바탕으로 후속 질문에 답변하는 전문 상담사다.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )

    return {"answer": response.choices[0].message.content.strip()}
