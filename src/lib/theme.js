// Design tokens shared across components.
export const C = {
  ink: "#16110D",
  paper: "#FBF7F0",
  line: "#E4DACB",
  muted: "#7A6E5F",
  panel: "#FFFFFF",
  // severity / priority
  WATCH: "#5C7A52",
  ACT: "#C68A2E",
  URGENT: "#C25A1C",
  CRITICAL: "#B4341F",
  HIGH: "#B4341F",
  MEDIUM: "#C68A2E",
  LOW: "#5C7A52",
  // price track
  current: "#7A6E5F",
  market: "#2F6B8F",
  rec: "#B4341F",
};

export const usd = (n) =>
  n == null ? "—" : "$" + Math.round(n).toLocaleString();

export const SAMPLE_CSV = `vin,year,make,model,cost,list_price,date_in_stock,photos_count,leads_30d,views_30d,market_avg_price,market_days_supply
5XYZU3LB0JG333333,2019,Hyundai,Santa Fe,21000,26995,2026-04-12,18,0,120,24800,41
WBA8E9G50GNT44444,2018,BMW,330i,24000,29995,2026-03-08,4,0,60,27200,52
3FA6P0H75GR222222,2020,Ford,Fusion,18000,21995,2026-05-03,6,2,90,20900,70
1FTEW1EP7JFA55555,2022,Ford,F-150,39000,44995,2026-05-29,24,14,520,45200,22
1HGCV1F30LA111111,2021,Honda,Accord,23000,27995,2026-06-07,22,9,310,27500,38`;
