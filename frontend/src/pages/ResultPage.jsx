// frontend\src\pages\ResultPage.jsx
import { useState, useEffect, useMemo } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import ResultTabs from "../components/results/ResultTabs";
import AccidentTab from "../components/results/AccidentTab";
import YoloTab from "../components/results/YoloTab";
import DrivableTab from "../components/results/DrivableTab";
import SummaryTab from "../components/results/SummaryTab";

import "../styles/result.css";

export default function ResultPage() {
  const location = useLocation();
  const navigate = useNavigate();

  const pipelineResult = location.state?.result;
  const [activeTab, setActiveTab] = useState("accident");

  const [gptCache, setGptCache] = useState({
    accident: "",
    yolo: "",
    drivable: "",
    summary: "",
  });

  const [gptLoading, setGptLoading] = useState({
    accident: false,
    yolo: false,
    drivable: false,
    summary: false,
  });

  useEffect(() => {
    if (!pipelineResult) {
      navigate("/", { replace: true });
    }
  }, [pipelineResult, navigate]);

  if (!pipelineResult) return null;

  const {
    status,
    vehicle_count,
    damage_result,
    yolo_image_url,
    vehicle, // ✅ 차종
  } = pipelineResult;

  const hasAccident = status === "ANALYZED";

  /* =========================
     🔥 차종
     ========================= */
  const primaryVehicle = useMemo(() => {
    if (!vehicle) return null;
    return {
      vehicle_type: vehicle.vehicle_type,
      confidence: vehicle.confidence,
      probabilities: vehicle.probabilities,
    };
  }, [vehicle]);

  const accidentSummary = useMemo(() => {
    if (!hasAccident) {
      return {
        accident_detected: false,
        accident_type: "UNKNOWN",
        confidence_level: "LOW",
        scores: {},
      };
    }

    return damage_result?.accident || {
      accident_detected: true,
      accident_type: "UNKNOWN",
      confidence_level: "LOW",
      scores: {},
    };
  }, [hasAccident, damage_result]);

  const requestGPT = async (key, payload) => {
    if (gptCache[key] || gptLoading[key]) return;

    setGptLoading((prev) => ({ ...prev, [key]: true }));

    try {
      const res = await fetch("http://127.0.0.1:8000/api/gpt/summary", {
      // const res = await fetch("api/gpt/summary", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await res.json();

      setGptCache((prev) => ({
        ...prev,
        [key]: data.gpt_summary || "",
      }));
    } catch {
      setGptCache((prev) => ({
        ...prev,
        [key]: "AI 설명을 불러오지 못했습니다.",
      }));
    } finally {
      setGptLoading((prev) => ({ ...prev, [key]: false }));
    }
  };

  useEffect(() => {
    if (!pipelineResult) return;

    if (hasAccident) {
      requestGPT("accident", {
        accident: accidentSummary,
        mode: "ACCIDENT",
      });
    }

    if (hasAccident && damage_result) {
      requestGPT("yolo", {
        yolo: damage_result,
        mode: "YOLO",
      });
    }

    if (hasAccident && damage_result?.drivable) {
      const vehicles = damage_result.drivable.vehicles || [];
      if (vehicles.length > 0) {
        const primary =
          vehicles.find((v) => v.drivable === false) || vehicles[0];

        requestGPT("drivable", {
          drivable: {
            drivable: primary.drivable,
            drivable_reason:
              primary.reason || primary.drivable_reason || "unknown",
            confidence: primary.confidence ?? 0,
          },
          mode: "DRIVABLE",
        });
      }
    }

    /* =========================
       🔥 딱 여기만 수정됨 (종합 CNN 판단)
       ========================= */
    if (hasAccident && damage_result) {
      requestGPT("summary", {
        accident: accidentSummary,
        yolo: damage_result,
        drivable: damage_result.drivable, // ✅ 이것만 변경
        mode: "SUMMARY",
      });
    }
  }, [pipelineResult]);

  return (
    <div className="page">
      <div className="result-container">

        <div className="result-header">
          <div className="result-logo" onClick={() => navigate("/")}>
            Carwhy
          </div>
          <h1 className="result-title">AI 차량 사고 분석 결과</h1>
          <div className="header-spacer" />
        </div>

        <div className="tabs-wrap">
          <ResultTabs
            activeTab={activeTab}
            setActiveTab={setActiveTab}
            hasAccident={hasAccident}
          />
        </div>

        <div className="card result-content">

          {activeTab === "accident" && (
            <AccidentTab
              accident={accidentSummary}
              vehicleCount={vehicle_count}
              vehicle={primaryVehicle}
              gptText={gptCache.accident}
              loading={gptLoading.accident}
            />
          )}

          {activeTab === "yolo" && hasAccident && (
            <YoloTab
              damageResult={damage_result}
              yoloImageUrl={yolo_image_url}
              gptText={gptCache.yolo}
              loading={gptLoading.yolo}
            />
          )}

          {activeTab === "drivable" && hasAccident && (
            <DrivableTab
              drivable={damage_result?.drivable}
              gptText={gptCache.drivable}
              loading={gptLoading.drivable}
            />
          )}

          {activeTab === "summary" && (
            <SummaryTab
              gptText={gptCache.summary}
              loading={gptLoading.summary}
            />
          )}

        </div>
      </div>
    </div>
  );
}
