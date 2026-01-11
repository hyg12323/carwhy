// frontend\src\components\results\AccidentTab.jsx
import { useMemo } from "react";
import "../../styles/accidentTab.css";

const ACCIDENT_TYPES = [
  "FRONT_COLLISION",
  "REAR_COLLISION",
  "SIDE_COLLISION",
  "COMPLEX_DAMAGE",
];

const ACCIDENT_TYPE_LABELS = {
  FRONT_COLLISION: "전방 충돌",
  REAR_COLLISION: "후방 충돌",
  SIDE_COLLISION: "측면 충돌",
  COMPLEX_DAMAGE: "복합 손상",
  UNKNOWN: "판단 불가",
};

export default function AccidentTab({
  accident,
  vehicleCount,
  vehicle,          // ✅ 그대로
  gptText,
  loading,
}) {
  console.log("🚗 vehicle prop:", vehicle);

  if (!accident) {
    return (
      <div className="accident-tab">
        <p className="accident-empty">사고 판단 결과가 없습니다.</p>
      </div>
    );
  }

  const {
    accident_detected,
    accident_state,
    accident_type,
    scores,
  } = accident;

  const isConfirmed = accident_state === "CONFIRMED_ACCIDENT";

  /* =========================
     퍼센트 정규화 (CONFIRMED만)
     ========================= */
  const scoreEntries = useMemo(() => {
    if (!isConfirmed) {
      return ACCIDENT_TYPES.map((type) => ({
        type,
        percent: 0,
      }));
    }

    const map = scores || {};
    const total = ACCIDENT_TYPES.reduce(
      (sum, type) => sum + (map[type] ?? 0),
      0
    );

    return ACCIDENT_TYPES.map((type) => {
      const value = map[type] ?? 0;
      const percent = total > 0 ? Math.round((value / total) * 100) : 0;
      return { type, percent };
    });
  }, [scores, isConfirmed]);

  const topType = scoreEntries.reduce(
    (max, cur) => (cur.percent > max.percent ? cur : max),
    scoreEntries[0]
  );

  return (
    <div className="accident-tab">
      <h3 className="accident-title">사고 판단 결과</h3>

      <section className="accident-section">
        <div className="accident-layout accident-layout-wide">

          {/* ===== 좌측 ===== */}
          <div className="accident-summary">
            <div className="accident-item">
              <span className="accident-label">사고 여부</span>
              <span className="accident-value">
                {accident_detected ? "사고 감지" : "사고 아님"}
              </span>
            </div>

            <div className="accident-item">
              <span className="accident-label">사고 상태</span>
              <span className="accident-value">{accident_state}</span>
            </div>

            {/* ✅🔥 차종 표시 (여기만 수정) */}
            <div className="accident-item">
              <span className="accident-label">차종</span>
              <span className="accident-value">
                {vehicle?.vehicle_type
                  ? vehicle.vehicle_type
                  : "알 수 없음"}
              </span>
            </div>

            <div className="accident-item">
              <span className="accident-label">차량 수</span>
              <span className="accident-value">
                {vehicleCount != null ? `${vehicleCount}대` : "N/A"}
              </span>
            </div>

            <div
              className="accident-item"
              style={{ gridColumn: "1 / -1", marginTop: 8 }}
            >
              <span className="accident-label">판단 요약</span>
              <span className="accident-value">
                {isConfirmed && topType?.percent > 0
                  ? `${ACCIDENT_TYPE_LABELS[topType.type]} 비율이 가장 높게 분석되었습니다.`
                  : "사고로 확정되지 않아 사고 유형 비율은 표시되지 않습니다."}
              </span>
            </div>
          </div>

          {/* ===== 우측 그래프 (그대로 유지) ===== */}
          <div className="accident-ratio">
            <h4 className="accident-ratio-title">
              사고 유형별 판단 비율
            </h4>

            {scoreEntries.map(({ type, percent }) => (
              <div key={type} className="accident-score-item">
                <div className="accident-score-label">
                  <span>{ACCIDENT_TYPE_LABELS[type]}</span>
                  <span>{percent}%</span>
                </div>

                <div className="accident-score-bar">
                  <div
                    className="accident-score-fill"
                    style={{ width: `${percent}%` }}
                  />
                </div>
              </div>
            ))}
          </div>

        </div>
      </section>

      <section className="accident-section accident-gpt">
        <h3 className="accident-title">AI 사고 판단 설명</h3>

        {loading ? (
          <p className="accident-loading">
            AI가 사고 판단 결과를 분석 중입니다…
          </p>
        ) : (
          <p className="accident-gpt-text">
            {gptText || "AI 설명을 불러오지 못했습니다."}
          </p>
        )}
      </section>
    </div>
  );
}
