// frontend\src\components\results\YoloTab.jsx
import { useState } from "react";
import "../../styles/accidentTab.css";

export default function YoloTab({
  damageResult,
  yoloImageUrl,
  gptText,
  loading,
}) {
  const [currentIndex, setCurrentIndex] = useState(0);

  if (!damageResult || !damageResult.vehicles) {
    return (
      <div className="accident-tab">
        <p className="accident-empty">파손 분석 결과가 없습니다.</p>
      </div>
    );
  }

  const vehicles = damageResult.vehicles;
  const vehicle = vehicles[currentIndex];

  const DAMAGE_PARTS = [
    "Fender",
    "Light",
    "Bumper",
    "Bonnet",
    "Door",
    "CAR_TRUNK-KP48",
  ];

  const DISPLAY_NAME_MAP = {
    "CAR_TRUNK-KP48": "TRUNK",
  };

  const canPrev = currentIndex > 0;
  const canNext = currentIndex < vehicles.length - 1;

  return (
    <div className="accident-tab">
      <h3 className="accident-title">파손 부위 분석</h3>

      {/* =====================
          파손 결과 카드
         ===================== */}
      <section className="accident-section">
        <div className="accident-layout">

          {/* 좌측 이미지 */}
          <div className="yolo-image-box">
            {yoloImageUrl ? (
              <img
                src={`http://127.0.0.1:8000${yoloImageUrl}`}
                // src={`${yoloImageUrl}`}
                alt="YOLO Damage"
                className="yolo-image"
              />
            ) : (
              <div className="yolo-image-empty">이미지 없음</div>
            )}
          </div>

          {/* 우측 그래프 */}
          <div>
            {/* 차량 전환 */}
            {vehicles.length > 1 && (
              <div className="vehicle-header">
                <button
                  className={`vehicle-arrow ${!canPrev ? "disabled" : ""}`}
                  onClick={() => canPrev && setCurrentIndex(i => i - 1)}
                >
                  ◀
                </button>

                <span className="vehicle-indicator">
                  차량 {currentIndex + 1} / {vehicles.length}
                </span>

                <button
                  className={`vehicle-arrow ${!canNext ? "disabled" : ""}`}
                  onClick={() => canNext && setCurrentIndex(i => i + 1)}
                >
                  ▶
                </button>
              </div>
            )}

            {/* 파손 그래프 */}
            {DAMAGE_PARTS.map((part, idx) => {
              const found = vehicle.damages.find(
                (d) => d.class_name === part
              );

              const percent = Math.round((found?.confidence || 0) * 100);

              return (
                <div key={idx} className="accident-score-item">
                  <div className="accident-score-label">
                    <span>
                      <strong>{DISPLAY_NAME_MAP[part] || part}</strong>{" "}
                      <span style={{ color: "#9ca3af" }}>
                        ({found?.region || "-"})
                      </span>
                    </span>
                    <span>{percent}%</span>
                  </div>

                  <div className="accident-score-bar">
                    <div
                      className="accident-score-fill"
                      style={{ width: `${percent}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* =====================
          AI 파손부위 설명 (표시 전용)
         ===================== */}
      <section className="accident-section accident-gpt">
        <h3 className="accident-title">AI 파손 부위 분석 설명</h3>

        {loading ? (
          <p className="accident-loading">
            AI가 파손 부위를 분석 중입니다…
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
