#!/usr/bin/env python3
"""每日抓 FMP 歷史日線,計算 5/20/60/240 日均線與當日站上/跌破訊號,輸出 data.json。
需要環境變數 FMP_API_KEY(到 https://site.financialmodelingprep.com 取得免費 API key)。"""
import os, json, time, datetime, urllib.request

API = os.environ.get("FMP_API_KEY")
if not API:
    raise SystemExit("缺少環境變數 FMP_API_KEY")

SYMBOLS = [
    "MU","WDC","STX","SNDK","LRCX","AMAT","KLAC","SIMO","ASML",
    "AMD","INTC","QCOM","ARM",
    "AAOI","LITE","COHR","MRVL",
    "PLTR","ORCL","TEAM","CRM","NET","ADBE","CRWD",
    "NVDA","MSFT","TSLA","AAPL","GOOGL","AMZN","META",
    "AVGO","TSM",
]
MA_DEFS = [(5, "週線"), (20, "月線"), (60, "季線"), (240, "年線")]
NEAR_PCT = 1.5
BASE = "https://financialmodelingprep.com/stable/historical-price-eod/light"

def fetch_closes(sym):
    frm = (datetime.date.today() - datetime.timedelta(days=420)).isoformat()
    url = f"{BASE}?symbol={sym}&from={frm}&apikey={API}"
    req = urllib.request.Request(url, headers={"User-Agent": "ma-dashboard/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = json.load(r)
    rows = raw.get("historical") if isinstance(raw, dict) else raw
    if not rows:
        raise ValueError("空資料")
    closes, dates = [], []
    for x in rows:
        px = x.get("price", x.get("close"))
        if px is None:
            continue
        closes.append(float(px)); dates.append(x["date"])
    closes.reverse(); dates.reverse()        # 新到舊 -> 舊到新
    return dates, closes

def sma(c, n, back=0):
    end = len(c) - back
    return sum(c[end - n:end]) / n if end >= n else None

def build(sym):
    dates, closes = fetch_closes(sym)
    price, date = closes[-1], dates[-1]
    price_prev = closes[-2] if len(closes) > 1 else price
    mas = []
    for n, label in MA_DEFS:
        v = sma(closes, n, 0); vp = sma(closes, n, 1)
        if v is None:
            mas.append({"k": n, "label": label, "v": None}); continue
        above = price >= v
        diff = (price / v - 1) * 100
        cross = None
        if vp is not None:
            prev_above = price_prev >= vp
            if not prev_above and above: cross = "bull"
            elif prev_above and not above: cross = "bear"
        mas.append({"k": n, "label": label, "v": round(v, 4),
                    "above": above, "diff": round(diff, 2),
                    "cross": cross, "near": abs(diff) <= NEAR_PCT})
    valid = sum(1 for m in mas if m["v"] is not None)
    score = sum(1 for m in mas if m["v"] is not None and m["above"])
    return {"price": round(price, 4), "date": date, "mas": mas,
            "score": score, "valid": valid}

out = {}
for sym in SYMBOLS:
    try:
        out[sym] = build(sym)
        print(f"OK  {sym}: {out[sym]['price']} @ {out[sym]['date']}")
    except Exception as e:
        msg = str(e)
        if "402" in msg or "Payment Required" in msg or "higher plan" in msg.lower():
            msg = "免費方案未支援"
        out[sym] = {"error": msg}
        print(f"ERR {sym}: {e}")
    time.sleep(0.25)

out["_updated"] = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
with open("data.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print(f"\n寫入 data.json,共 {len(SYMBOLS)} 檔。")
