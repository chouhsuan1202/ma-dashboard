#!/usr/bin/env python3
"""每日抓 FMP 歷史日線,計算 5/20/60/240 日均線,輸出 data.json。
需要環境變數 FMP_API_KEY(到 https://site.financialmodelingprep.com 取得免費 API key)。"""
import os, json, time, datetime, urllib.request, urllib.error

API = os.environ.get("FMP_API_KEY")
if not API:
    raise SystemExit("缺少環境變數 FMP_API_KEY")

# 與 index.html 的清單一致(美股)
SYMBOLS = [
    "MU","WDC","STX","SNDK","LRCX","AMAT","KLAC","SIMO","ASML",
    "AMD","INTC","QCOM","ARM",
    "AAOI","LITE","COHR","MRVL",
    "PLTR","ORCL","TEAM","CRM","NET","ADBE","CRWD",
    "NVDA","MSFT","TSLA","AAPL","GOOGL","AMZN","META",
    "AVGO","TSM",
    "VST","GEV","CEG",
    "SBGSY","POWL","PWR","FIX","ETN",
    "MOD","VRT","NVT",
    "NOK","ERIC","ANET","NBIS",
    "TER","LLY","UNH",
]

BASE = "https://financialmodelingprep.com/stable/historical-price-eod/light"

def fetch_closes(sym):
    frm = (datetime.date.today() - datetime.timedelta(days=420)).isoformat()
    url = f"{BASE}?symbol={sym}&from={frm}&apikey={API}"
    req = urllib.request.Request(url, headers={"User-Agent": "ma-dashboard/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = json.load(r)
    # 兼容兩種格式:扁平陣列,或 {"historical":[...]}
    rows = raw.get("historical") if isinstance(raw, dict) else raw
    if not rows:
        raise ValueError("空資料")
    closes, dates = [], []
    for x in rows:
        px = x.get("price", x.get("close"))
        if px is None:
            continue
        closes.append(float(px)); dates.append(x["date"])
    # FMP 回傳為新到舊,反轉成舊到新
    closes.reverse(); dates.reverse()
    return dates, closes

def sma(c, n):
    return round(sum(c[-n:]) / n, 4) if len(c) >= n else None

out = {}
for sym in SYMBOLS:
    try:
        dates, closes = fetch_closes(sym)
        out[sym] = {
            "price": round(closes[-1], 4),
            "date": dates[-1],
            "ma5": sma(closes, 5),
            "ma20": sma(closes, 20),
            "ma60": sma(closes, 60),
            "ma240": sma(closes, 240),
        }
        print(f"OK  {sym}: {out[sym]['price']} @ {out[sym]['date']}")
    except Exception as e:
        out[sym] = {"error": str(e)}
        print(f"ERR {sym}: {e}")
    time.sleep(0.25)  # 友善 FMP 速率

out["_updated"] = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
with open("data.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print(f"\n寫入 data.json,共 {len(SYMBOLS)} 檔。")
