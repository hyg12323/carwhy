// frontend\src\components\results\SummaryTab.jsx
import { useState, useEffect, useRef } from "react";
import "../../styles/accidentTab.css";

export default function SummaryTab({ gptText, loading }) {
  /* =========================
     UI 미리보기용 더미 텍스트
     ========================= */
  const previewText = `
본 화면은 AI 사고 분석 시스템의
종합 분석 결과 UI 미리보기입니다.

실제 서비스에서는
사고 판단, 파손 부위, 주행 가능 여부를
종합한 AI 설명이 이 영역에 표시됩니다.
`;

  /* =========================
     초기 GPT 종합 결과
     ========================= */
  const baseParagraphs = gptText
    ? gptText.split("\n\n")
    : previewText.split("\n\n");

  /* =========================
     🔥 채팅용 로컬 상태
     ========================= */
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);

  /* =========================
     🔥 스크롤 제어용 ref
     ========================= */
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  /* =========================
     🔥 질문 전송 (GPT follow-up)
     ========================= */
  const handleSend = async () => {
    if (!input.trim() || sending) return;

    const userMessage = input;
    setInput("");
    setSending(true);

    // 1️⃣ 사용자 질문 먼저 추가
    setMessages((prev) => [
      ...prev,
      { role: "user", content: userMessage },
    ]);

    try {
      // 2️⃣ GPT follow-up 호출
      const res = await fetch("http://127.0.0.1:8000/api/gpt/chat", {
      // const res = await fetch("http://40.89.215.220:8000/api/gpt/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: userMessage,
          summary_text: gptText || previewText, // ✅ ⭐ 핵심 수정
        }),
      });

      const data = await res.json();

      // 3️⃣ GPT 답변만 추가
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            data?.answer ||
            "현재 질문에 대한 답변을 생성하지 못했습니다.",
        },
      ]);
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "서버와 통신 중 문제가 발생했습니다. 잠시 후 다시 시도해주세요.",
        },
      ]);
    } finally {
      setSending(false);
    }
  };

  return (
    <section className="accident-section accident-gpt">
      <h3 className="accident-title">종합 분석 결과</h3>

      {loading ? (
        <p className="accident-loading">
          종합 분석 결과를 생성 중입니다…
        </p>
      ) : (
        <div className="chat-area">
          {/* =========================
              1️⃣ 최초 종합 분석 (큰 말풍선, 고정)
              ========================= */}
          <div className="chat-bubble assistant">
            {baseParagraphs.map((p, i) => (
              <p
                key={i}
                style={{
                  marginBottom: 14,
                  fontSize: "1.05rem",
                  lineHeight: 1.7,
                }}
              >
                {p}
              </p>
            ))}
          </div>

          {/* =========================
              2️⃣ 사용자 질문 + GPT 답변 (채팅형)
              ========================= */}
          {messages.map((msg, i) => (
            <div key={i} className={`chat-bubble ${msg.role}`}>
              {msg.content.split("\n\n").map((p, idx) => (
                <p key={idx} style={{ marginBottom: 12 }}>
                  {p}
                </p>
              ))}
            </div>
          ))}

          <div ref={bottomRef} />

          {/* =========================
              3️⃣ 입력 영역
              ========================= */}
          <div className="chat-input-wrapper">
            <input
              className="chat-input"
              value={input}
              placeholder="예: 이거 수리해야 하나요?"
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleSend();
              }}
              disabled={sending}
            />
            <button
              className="chat-send"
              onClick={handleSend}
              disabled={sending}
            >
              전송
            </button>
          </div>
        </div>
      )}
    </section>
  );
}
