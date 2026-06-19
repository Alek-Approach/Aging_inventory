import React, { useState } from "react";
import { C } from "./lib/theme";
import UploadTracker from "./components/UploadTracker";
import AnalysisView from "./components/AnalysisView";

const TABS = [
  ["track", "Milestone Tracker", "Upload your lot, get 30·45·60·75·90-day alerts"],
  ["analyze", "Price & Risk Analysis", "Rank units by cost-of-inaction with price recs"],
];

export default function App() {
  const [tab, setTab] = useState("track");
  const active = TABS.find((t) => t[0] === tab);

  return (
    <div style={{ minHeight: "100vh", background: C.paper, color: C.ink,
      fontFamily: "'Helvetica Neue', Arial, sans-serif" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&display=swap');
        *{box-sizing:border-box;} body{margin:0;}
      `}</style>

      <header style={{ maxWidth: 860, margin: "0 auto", padding: "30px 24px 0" }}>
        <div style={{ fontSize: 11, letterSpacing: 3, textTransform: "uppercase", color: C.muted }}>
          Aging Inventory Agent
        </div>
        <h1 style={{ fontFamily: "Fraunces, Georgia, serif", fontSize: 30,
          fontWeight: 600, margin: "8px 0 4px" }}>
          {active[1]}
        </h1>
        <p style={{ color: C.muted, fontSize: 14, margin: 0 }}>{active[2]}</p>

        <nav style={{ display: "flex", gap: 4, marginTop: 20,
          borderBottom: `2px solid ${C.ink}` }}>
          {TABS.map(([id, label]) => (
            <button key={id} onClick={() => setTab(id)}
              style={{ padding: "10px 16px", border: "none", cursor: "pointer",
                fontSize: 14, background: tab === id ? C.ink : "transparent",
                color: tab === id ? C.paper : C.muted,
                borderRadius: "6px 6px 0 0", fontWeight: tab === id ? 600 : 400 }}>
              {label}
            </button>
          ))}
        </nav>
      </header>

      <main style={{ maxWidth: 860, margin: "0 auto", padding: "0 24px 60px" }}>
        {tab === "track" ? <UploadTracker /> : <AnalysisView />}
      </main>
    </div>
  );
}
