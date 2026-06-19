import React, { useState, useCallback } from "react";
import { C, usd, SAMPLE_CSV } from "../lib/theme";
import { analyzeCsv } from "../lib/api";

export default function AnalysisView() {
  const [data, setData] = useState(null);
  const [open, setOpen] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const run = useCallback(async (file) => {
    setLoading(true); setError(null);
    try {
      setData(await analyzeCsv(file));
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const useSample = () =>
    run(new File([SAMPLE_CSV], "sample_inventory.csv", { type: "text/csv" }));

  if (loading) return <div style={{ padding: 60, textAlign: "center", color: C.muted }}>Scoring inventory…</div>;

  if (!data) {
    return (
      <div style={{ padding: "40px 0", textAlign: "center" }}>
        <p style={{ color: C.muted, marginBottom: 20 }}>
          Upload a CSV to score every unit by cost-of-inaction and get a
          market-anchored price recommendation.
        </p>
        <label style={{ display: "inline-block", padding: "10px 20px", background: C.ink,
          color: C.paper, borderRadius: 6, fontSize: 14, cursor: "pointer", marginRight: 12 }}>
          Choose file
          <input type="file" accept=".csv" style={{ display: "none" }}
            onChange={(e) => e.target.files[0] && run(e.target.files[0])} />
        </label>
        <button onClick={useSample}
          style={{ background: "none", border: "none", color: C.muted,
            textDecoration: "underline", fontSize: 13, cursor: "pointer" }}>
          try sample data
        </button>
        {error && (
          <div style={{ marginTop: 20, fontSize: 13, color: C.CRITICAL }}>
            Couldn't reach the API — is the backend running on port 8000?
          </div>
        )}
      </div>
    );
  }

  return (
    <div style={{ padding: "20px 0" }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 18 }}>
        <div style={{ fontSize: 13, color: C.muted }}>
          {data.analyzed} units · {data.high_priority} high priority ·{" "}
          {usd(data.total_monthly_bleed)}/mo total bleed
        </div>
        <button onClick={() => setData(null)}
          style={{ background: "none", border: "none", color: C.muted,
            textDecoration: "underline", fontSize: 12, cursor: "pointer" }}>
          upload another
        </button>
      </div>

      {data.results.map((r) => {
        const isOpen = open === r.vin;
        const p = r.pricing;
        return (
          <div key={r.vin} style={{ borderBottom: `1px solid ${C.line}` }}>
            <div onClick={() => setOpen(isOpen ? null : r.vin)}
              style={{ padding: "16px 4px", display: "flex", alignItems: "center",
                gap: 14, cursor: "pointer" }}>
              <span style={{ fontSize: 11, padding: "3px 9px", borderRadius: 4,
                background: C[r.priority], color: "#fff", letterSpacing: 1, whiteSpace: "nowrap" }}>
                {r.priority}
              </span>
              <div style={{ flex: 1, fontFamily: "Fraunces, Georgia, serif", fontSize: 16 }}>
                {r.headline}
              </div>
              <div style={{ textAlign: "right" }}>
                <div style={{ fontSize: 11, color: C.muted }}>BLEED</div>
                <div style={{ fontFamily: "Fraunces, Georgia, serif", fontSize: 16,
                  fontWeight: 700, color: C.rec }}>
                  {usd(r.monthly_floorplan_bleed)}/mo
                </div>
              </div>
            </div>

            {isOpen && (
              <div style={{ padding: "4px 4px 22px 12px" }}>
                <div style={{ display: "flex", gap: 28, flexWrap: "wrap", marginBottom: 14 }}>
                  <Price label="Current" val={p.current_price} col={C.current} />
                  <Price label="Market" val={p.market_price} col={C.market} />
                  <Price label="Recommended" val={p.recommended_price} col={C.rec} big />
                </div>
                <div style={{ background: "#F4ECDD", borderLeft: `3px solid ${C.rec}`,
                  padding: "10px 14px", borderRadius: "0 6px 6px 0", fontSize: 14, lineHeight: 1.45 }}>
                  <strong>Pricing:</strong> {p.rationale}{" "}
                  <span style={{ fontSize: 11, marginLeft: 6, padding: "2px 7px", borderRadius: 4,
                    background: p.confidence === "HIGH" ? C.market : C.muted, color: "#fff" }}>
                    {p.confidence === "HIGH" ? "MARKET-BACKED" : "AGE-BASED"}
                  </span>
                </div>
                <div style={{ marginTop: 10, fontSize: 14, lineHeight: 1.45 }}>
                  <strong>Marketing:</strong> {r.marketing_action}
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function Price({ label, val, col, big }) {
  return (
    <div>
      <div style={{ fontSize: 10, letterSpacing: 1, textTransform: "uppercase", color: col }}>{label}</div>
      <div style={{ fontFamily: "Fraunces, Georgia, serif",
        fontSize: big ? 22 : 18, fontWeight: 700, color: col }}>{usd(val)}</div>
    </div>
  );
}
