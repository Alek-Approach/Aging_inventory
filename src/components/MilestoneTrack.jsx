import React from "react";
import { C } from "../lib/theme";

export default function MilestoneTrack({ milestones }) {
  return (
    <div style={{ display: "flex", alignItems: "center" }}>
      {milestones.map((m, i) => (
        <React.Fragment key={m.day}>
          {i > 0 && (
            <div style={{ width: 16, height: 2,
              background: milestones[i].crossed ? C.ink : C.line }} />
          )}
          <div title={`${m.day}d · ${m.severity}: ${m.action}`}
            style={{ display: "flex", flexDirection: "column",
              alignItems: "center", gap: 3 }}>
            <div style={{ width: 14, height: 14, borderRadius: "50%",
              background: m.crossed ? C[m.severity] : "transparent",
              border: `2px solid ${m.crossed ? C[m.severity] : C.line}`,
              boxShadow: m.newly_crossed ? `0 0 0 3px ${C[m.severity]}33` : "none" }} />
            <span style={{ fontSize: 9, fontWeight: m.crossed ? 700 : 400,
              color: m.crossed ? C[m.severity] : C.muted }}>{m.day}</span>
          </div>
        </React.Fragment>
      ))}
    </div>
  );
}
