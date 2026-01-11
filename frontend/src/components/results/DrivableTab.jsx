// frontend\src\components\results\DrivableTab.jsx
import "../../styles/accidentTab.css";

export default function DrivableTab({ drivable, gptText, loading }) {
  const vehicles = drivable?.vehicles || [];

  if (!vehicles.length) {
    return (
      <div className="accident-tab">
        <h3 className="accident-title">주행 가능 판단</h3>
        <section className="accident-section">
          <p className="accident-loading">주행 판단 결과가 없습니다.</p>
        </section>
      </div>
    );
  }

  /* =========================
     차량별 점수 계산 함수 (기존 유지)
     ========================= */
  const calcScores = (v) => {
    const confidenceScore = Math.round((v.confidence ?? 0) * 100);
    let riskScore;

    if (v.drivable) {
      riskScore = Math.round(40 - confidenceScore * 0.3);
      riskScore = Math.max(5, Math.min(40, riskScore));
    } else {
      riskScore = Math.round(80 + confidenceScore * 0.2);
      riskScore = Math.min(100, riskScore);
    }

    return { confidenceScore, riskScore };
  };

  return (
    <div className="accident-tab">
      <h3 className="accident-title">주행 가능 판단</h3>

      {/* ================= 차량별 카드 ================= */}
      {vehicles.map((v, idx) => {
        const { confidenceScore, riskScore } = calcScores(v);

        return (
          <section className="accident-section" key={idx}>
            <div className="accident-layout">
              {/* ===== 좌측 ===== */}
              <div className="accident-summary">
                <div className="accident-item">
                  <span className="accident-label">
                    차량 {idx + 1} 주행 가능 여부
                  </span>
                  <span
                    className="accident-value"
                    style={{
                      fontSize: "22px",
                      fontWeight: 800,
                      color: v.drivable ? "#16a34a" : "#dc2626",
                    }}
                  >
                    {v.drivable ? "주행 가능" : "주행 불가"}
                  </span>
                </div>
              </div>

              {/* ===== 우측 ===== */}
              <div className="accident-ratio">
                <h4 className="accident-ratio-title">주행 판단 지표</h4>

                <div className="accident-score-item">
                  <div className="accident-score-label">
                    <span>주행 위험 점수</span>
                    <span>{riskScore}%</span>
                  </div>
                  <div className="accident-score-bar">
                    <div
                      className="accident-score-fill"
                      style={{ width: `${riskScore}%` }}
                    />
                  </div>
                </div>

                <div className="accident-score-item">
                  <div className="accident-score-label">
                    <span>CNN 판단 신뢰도</span>
                    <span>{confidenceScore}%</span>
                  </div>
                  <div className="accident-score-bar">
                    <div
                      className="accident-score-fill"
                      style={{ width: `${confidenceScore}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>
          </section>
        );
      })}

      {/* ================= AI 설명 (표시 전용) ================= */}
      <h3 className="accident-title">AI 주행 가능 설명</h3>
      <section className="accident-section accident-gpt">
        {loading ? (
          <p className="accident-loading">
            AI가 주행 가능성을 분석 중입니다…
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
