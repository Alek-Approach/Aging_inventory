import React, { useState, useCallback } from "react";
import { C, usd, SAMPLE_CSV } from "../lib/theme";
import { trackCsv } from "../lib/api";
import MilestoneTrack from "./MilestoneTrack";

export default function UploadTracker() {
  const [data, setData] = useState(null);
  const [drag, setDrag] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const run = useCallback(async (file) => {
    setLoading(true);
    setError(null);
    try {
      const res = await trackCsv(file, 7);
      setData(res);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const useSample = () =>
    run(new File([SAMPLE_CSV], "sample_inventory.csv", { type: "text/csv" }));

  if (loading) return <Centered>Analyzing lot…</Centered>;

  if (!data) {
    return (
      <div style={{ padding: "20px 0" }}>
        <div
          onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
          onDragLeave={() => setDrag(false)}
          onDrop={(e) => { e.preventDefault(); setDrag(false);
            if (e.dataTransfer.files[0]) run(e.dataTransfer.files[0]); }}
          style={{ border: `2px dashed ${drag ? C.CRITICAL : C.line}`,
            borderRadius: 10, padding: "48px 24px", textAlign: "center",
            background: drag ? "#F4ECDD" : "transparent", transition: "all .15s" }}>
          <div style={{ fontFamily: "Fraunces, Georgia, serif", fontSize: 20, marginBottom: 8 }}>
            Drop inventory CSV here
          </div>
          <div style={{ fontSize: 13, color: C.muted, marginBottom: 20 }}>
            Columns: vin, year, make, model, cost, list_price, date_in_stock,
            market_avg_price (optional)
          </div>
          <label style={{ display: "inline-block", padding: "10px 20px",
            background: C.ink, color: C.paper, borderRadius: 6, fontSize: 14, cursor: "pointer" }}>
            Choose file
            <input type="file" accept=".csv" style={{ display: "none" }}
              onChange={(e) => e.target.files[0] && run(e.target.files[0])} />
          </label>
          <div style={{ marginTop: 18 }}>
            <button onClick={useSample}
              style={{ background: "none", border: "none", color: C.muted,
                textDecoration: "underline", fontSize: 13, cursor: "pointer" }}>
              or try it with sample data
            </button>
          </div>
        </div>
        {error && <ErrorNote msg={error} />}
      </div>
    );
  }

  const alerts = data.vehicles.filter((v) => v.alert);
  const totalBleed = data.vehicles.reduce((a, v) => a + v.monthly_bleed, 0);

  return (
    <div style={{ padding: "20px 0" }}>
      <div style={{ display: "flex", justifyContent: "space-between",
        alignItems: "center", marginBottom: 18 }}>
        <div style={{ fontSize: 13, color: C.muted }}>
          {data.tracked} vehicles tracked · {usd(totalBleed)}/mo total bleed
        </div>
        <button onClick={() => setData(null)}
          style={{ background: "none", border: "none", color: C.muted,
            textDecoration: "underline", fontSize: 12, cursor: "pointer" }}>
          upload another
        </button>
      </div>

      {alerts.length > 0 && (
        <div style={{ marginBottom: 24 }}>
          <div style={{ fontSize: 12, letterSpacing: 1, textTransform: "uppercase",
            color: C.muted, marginBottom: 10 }}>
            🔔 {alerts.length} new alert{alerts.length > 1 ? "s" : ""} since last upload
          </div>
          {alerts.map((v) => {
            const m = v.milestones.find((x) => x.newly_crossed);
            return (
              <div key={v.vin} style={{ display: "flex", gap: 12, alignItems: "flex-start",
                padding: "12px 14px", background: C.panel, borderRadius: 8,
                borderLeft: `4px solid ${C[m.severity]}`, marginBottom: 8 }}>
                <span style={{ fontSize: 10, letterSpacing: 1, padding: "3px 8px",
                  borderRadius: 4, background: C[m.severity], color: "#fff", whiteSpace: "nowrap" }}>
                  {m.day}d · {m.severity}
                </span>
                <span style={{ fontSize: 14, lineHeight: 1.4 }}>{v.alert}</span>
              </div>
            );
          })}
        </div>
      )}

      <div style={{ fontSize: 12, letterSpacing: 1, textTransform: "uppercase",
        color: C.muted, marginBottom: 10 }}>Full lot</div>
      {data.vehicles.map((v) => (
        <div key={v.vin} style={{ padding: "16px 4px", borderBottom: `1px solid ${C.line}`,
          display: "flex", alignItems: "center", gap: 14 }}>
          <div style={{ flex: 1 }}>
            <div style={{ fontFamily: "Fraunces, Georgia, serif", fontSize: 17, fontWeight: 600 }}>
              {v.label}
            </div>
            <div style={{ fontSize: 12, color: C.muted, marginTop: 2 }}>
              {v.days_on_lot} days on lot ·{" "}
              {v.next_milestone ? `${v.next_milestone}d milestone in ${v.days_to_next}d` : "past 90 days"} ·{" "}
              {usd(v.monthly_bleed)}/mo
            </div>
          </div>
          <MilestoneTrack milestones={v.milestones} />
        </div>
      ))}
    </div>
  );
}

function Centered({ children }) {
  return <div style={{ padding: "60px 0", textAlign: "center", color: C.muted }}>{children}</div>;
}
function ErrorNote({ msg }) {
  return (
    <div style={{ marginTop: 16, padding: "12px 14px", background: "#FBE9E6",
      borderLeft: `4px solid ${C.CRITICAL}`, borderRadius: 8, fontSize: 13 }}>
      Couldn't reach the API. Make sure the backend is running on port 8000.
      <div style={{ color: C.muted, marginTop: 4, fontSize: 12 }}>{msg}</div>
    </div>
  );
}
