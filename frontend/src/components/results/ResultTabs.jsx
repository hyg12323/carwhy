// frontend\src\components\results\ResultTabs.jsx
export default function ResultTabs({
  activeTab,
  setActiveTab,
  hasAccident = false,   // 🔥 사고 여부 기준
}) {
  const tabs = [
    { key: "accident", label: "사고판단" },

    ...(hasAccident
      ? [
          { key: "yolo", label: "파손부위" },
          { key: "drivable", label: "주행가능" },
          { key: "summary", label: "전체종합" },
        ]
      : []),
  ];

  const tabCount = tabs.length;

  const activeIndex = Math.max(
    0,
    tabs.findIndex((t) => t.key === activeTab)
  );

  const percent = 100 / tabCount;

  return (
    <div
      style={{
        position: "relative",
        display: "flex",
        gap: 8,
        background: "#111827",
        padding: 6,
        borderRadius: 14,
        overflow: "hidden",
      }}
    >
      {/* 🔥 슬라이드 하이라이트 */}
      <div
        style={{
          position: "absolute",
          top: 6,
          left: `calc(${activeIndex * percent}% + 6px)`,
          width: `calc(${percent}% - 8px)`,
          height: "calc(100% - 12px)",
          borderRadius: 10,

          background:
            "linear-gradient(135deg, rgba(177,71,124,0.95), rgba(110,7,58,0.9))",

          boxShadow: "0 6px 18px rgba(177,71,124,0.45)",
          transition: "left 0.45s cubic-bezier(.4,0,.2,1)",
          zIndex: 0,
        }}
      />

      {tabs.map((tab) => {
        const isActive = activeTab === tab.key;

        return (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            style={{
              position: "relative",
              zIndex: 1,

              flex: 1,
              padding: "12px 0",
              borderRadius: 10,
              border: "none",
              cursor: "pointer",

              fontWeight: 600,
              fontSize: 14,

              background: "transparent",
              color: "#ffffff",
              opacity: isActive ? 1 : 0.65,

              transition: "opacity 0.25s ease",
            }}
          >
            {tab.label}
          </button>
        );
      })}
    </div>
  );
}
