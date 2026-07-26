#!/usr/bin/env python3
"""每日抓 FMP 歷史日線,計算 5/20/60/240 日均線與當日站上/跌破訊號,輸出 data.json。

清單唯一來源為 watchlist.json(indexes / holdings / watch)。
需要環境變數 FMP_API_KEY(到 https://site.financialmodelingprep.com 取得免費 API key)。

FMP 免費方案不支援的代碼(含多數指數)會自動改抓 Yahoo Finance chart API(見 fetch_closes)。
指數(^GSPC ^NDX ^SOX ^VIX)兩源皆失敗時,再改抓對應 ETF 代理(見 INDEX_FALLBACK)
並在資料中標記 fallback=true。
"""
import os, json, time, datetime, urllib.request, urllib.error, urllib.parse

API = os.environ.get("FMP_API_KEY")
if not API:
    raise SystemExit("缺少環境變數 FMP_API_KEY")

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "watchlist.json"), encoding="utf-8") as f:
    WL = json.load(f)

# 指數抓不到時的 ETF 代理。^VIX 沒有等比例 ETF,故不設代理(免費方案通常可直接取得)。
INDEX_FALLBACK = {"^GSPC": "SPY", "^NDX": "QQQ", "^SOX": "SOXX", "^VIX": None}

INDEXES         = list(WL.get("indexes", []))
MARKET_HOLDINGS = [h["s"] for h in WL.get("market_holdings", [])]
HOLDINGS        = [h["s"] for h in WL.get("holdings", [])]
WATCH           = [w["s"] for w in WL.get("watch", [])]

# 需要向 FMP 抓的個股/ETF(指數另外處理,含 fallback)
def _dedupe(seq):
    seen, out = set(), []
    for x in seq:
        if x not in seen:
            seen.add(x); out.append(x)
    return out

STOCK_SYMBOLS = _dedupe(MARKET_HOLDINGS + HOLDINGS + WATCH)
# 只有個股(holdings + watch)抓 P/E 與財報日;指數與 ETF(market_holdings)不抓
FUNDAMENTAL_SYMBOLS = _dedupe(HOLDINGS + WATCH)
# 對外公開的完整代碼清單(供檢查用)
SYMBOLS = _dedupe(INDEXES + STOCK_SYMBOLS)

MA_DEFS = [(5, "週線"), (20, "月線"), (60, "季線"), (240, "年線")]
NEAR_PCT = 0.8                 # 接近閾值(%)
NEAR_KS = (60, 240)            # 只有季線 / 年線會產生「接近」訊號

# 需要輸出完整價格歷史序列(供前端點擊彈窗畫線圖)的代碼。
# 先只做 TSM(台積電);之後要幫其他股票加線圖,把代碼加進這個集合即可。
HIST_SYMBOLS = {"TSM", "SXRV.DE", "SEC0.DE", "SXR8.DE", "0050.TW"}
HIST_MAX_DAYS = 520            # 每檔最多保留幾個交易日的歷史(足夠「全部」約 2 年)
BASE = "https://financialmodelingprep.com/stable/historical-price-eod/light"


# 記憶快取:同一 symbol 只抓一次(fallback 代理與清單重複時省額度)。
# 值為 (dates, closes, provider) 或 ("ERR", 例外)。
_FETCH_CACHE = {}

YAHOO_BASE = "https://query1.finance.yahoo.com/v8/finance/chart"


def fetch_closes_fmp(sym):
    """向 FMP 抓歷史日線,回傳 (dates, closes),依 date 升冪排序。"""
    frm = (datetime.date.today() - datetime.timedelta(days=420)).isoformat()
    url = f"{BASE}?symbol={sym}&from={frm}&apikey={API}"
    req = urllib.request.Request(url, headers={"User-Agent": "ma-dashboard/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = json.load(r)
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", "ignore")
        except Exception:
            pass
        raise ValueError(f"HTTP {e.code} {body[:120]}")
    # FMP 受限端點常回傳 {"Error Message": ...} 或 {"message": ...}
    if isinstance(raw, dict) and ("Error Message" in raw or "message" in raw):
        raise ValueError(str(raw.get("Error Message") or raw.get("message")))
    rows = raw.get("historical") if isinstance(raw, dict) else raw
    if not rows:
        raise ValueError("空資料")
    # 依 date 欄位升冪排序(舊到新),取代盲目 reverse
    rows = sorted((x for x in rows if x.get("date")), key=lambda x: x["date"])
    closes, dates = [], []
    for x in rows:
        px = x.get("price", x.get("close"))
        if px is None:
            continue
        closes.append(float(px)); dates.append(x["date"])
    if not closes:
        raise ValueError("空資料")
    return dates, closes


def fetch_closes_yahoo(sym):
    """向 Yahoo Finance chart API 抓歷史日線,回傳 (dates, closes),依 date 升冪排序。"""
    url = f"{YAHOO_BASE}/{urllib.parse.quote(sym)}?range=2y&interval=1d"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            j = json.load(r)
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", "ignore")
        except Exception:
            pass
        raise ValueError(f"HTTP {e.code} {body[:120]}")
    chart = j.get("chart") if isinstance(j, dict) else None
    if not isinstance(chart, dict):
        raise ValueError("無 chart")
    if chart.get("error"):
        raise ValueError(str(chart["error"])[:120])
    result = chart.get("result")
    if not result:
        raise ValueError("無 result")
    r0 = result[0]
    ts = r0.get("timestamp") or []
    quote = (r0.get("indicators", {}).get("quote") or [{}])[0]
    raw_closes = quote.get("close") or []
    pairs = []
    for t, px in zip(ts, raw_closes):
        if px is None:
            continue
        d = datetime.datetime.fromtimestamp(t, datetime.timezone.utc).date().isoformat()
        pairs.append((d, float(px)))
    if not pairs:
        raise ValueError("空資料")
    pairs.sort(key=lambda p: p[0])
    dates = [p[0] for p in pairs]
    closes = [p[1] for p in pairs]
    return dates, closes


def fetch_closes(sym):
    """先試 FMP,失敗改試 Yahoo。回傳 (dates, closes, provider)。結果與最終失敗都快取。"""
    cached = _FETCH_CACHE.get(sym)
    if cached is not None:
        if cached[0] == "ERR":
            raise cached[1]
        return cached

    try:
        dates, closes = fetch_closes_fmp(sym)
        result = (dates, closes, "fmp")
    except Exception as e1:
        time.sleep(0.25)  # Yahoo 請求之間也遵守節流
        try:
            dates, closes = fetch_closes_yahoo(sym)
            result = (dates, closes, "yahoo")
        except Exception as e2:
            err = ValueError(f"FMP: {str(e1)[:80]} | Yahoo: {str(e2)[:80]}")
            _FETCH_CACHE[sym] = ("ERR", err)
            raise err
    _FETCH_CACHE[sym] = result
    return result


def sma(c, n, back=0):
    end = len(c) - back
    return sum(c[end - n:end]) / n if end >= n else None


def compute(dates, closes):
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
        near = (n in NEAR_KS) and (abs(diff) <= NEAR_PCT)
        mas.append({"k": n, "label": label, "v": round(v, 4),
                    "above": above, "diff": round(diff, 2),
                    "cross": cross, "near": near})
    valid = sum(1 for m in mas if m["v"] is not None)
    score = sum(1 for m in mas if m["v"] is not None and m["above"])
    return {"price": round(price, 4), "date": date, "mas": mas,
            "score": score, "valid": valid}


def attach_hist(r, dates, closes):
    """把價格歷史序列塞進結果(僅限 HIST_SYMBOLS),保留最後 HIST_MAX_DAYS 筆。
    形狀:{"d": [日期...], "c": [收盤...]},兩陣列等長、依日期升冪。"""
    d = dates[-HIST_MAX_DAYS:]
    c = [round(float(x), 2) for x in closes[-HIST_MAX_DAYS:]]
    r["hist"] = {"d": d, "c": c}
    return r


def build_stock(sym):
    dates, closes, provider = fetch_closes(sym)
    r = compute(dates, closes)
    r["provider"] = provider
    if sym in HIST_SYMBOLS:
        attach_hist(r, dates, closes)
    return r


def build_index(sym):
    """先抓指數本身(FMP -> Yahoo),失敗則改抓 ETF 代理(若有)。回傳結果並標記來源。"""
    try:
        dates, closes, provider = fetch_closes(sym)
        r = compute(dates, closes)
        r.update(src=sym, fallback=False, provider=provider)
        return r
    except Exception as e1:
        proxy = INDEX_FALLBACK.get(sym)
        if not proxy:
            raise
        dates, closes, provider = fetch_closes(proxy)  # 讓 proxy 的錯誤自然往外拋
        r = compute(dates, closes)
        r.update(src=proxy, fallback=True, provider=provider, index_error=str(e1)[:80])
        return r


def fetch_fundamentals(symbols):
    """用 Yahoo quoteSummary(需 crumb)抓個股 P/E 與下次財報日。
    最佳努力:任何失敗都回傳已取得的部分,絕不讓核心 MA 資料建置中斷。
    回傳 {sym: {"pe": float|None, "earnings": "YYYY-MM-DD"|None, "est": bool}}。"""
    import http.cookiejar
    out = {}
    ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    try:
        cj = http.cookiejar.CookieJar()
        op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
        op.addheaders = [("User-Agent", ua)]
        try:
            op.open("https://fc.yahoo.com", timeout=15)
        except Exception:
            pass
        crumb = op.open("https://query2.finance.yahoo.com/v1/test/getcrumb",
                        timeout=15).read().decode().strip()
    except Exception as e:
        print(f"WARN 無法取得 Yahoo crumb,略過 P/E 與財報日: {e}")
        return out
    if not crumb or "<" in crumb:
        print("WARN Yahoo crumb 無效,略過 P/E 與財報日")
        return out

    for sym in symbols:
        url = (f"https://query2.finance.yahoo.com/v10/finance/quoteSummary/"
               f"{urllib.parse.quote(sym)}?modules=summaryDetail,calendarEvents"
               f"&crumb={urllib.parse.quote(crumb)}")
        try:
            with op.open(url, timeout=20) as r:
                res = json.load(r)["quoteSummary"]["result"][0]
            sd = res.get("summaryDetail", {}) or {}
            ce = res.get("calendarEvents", {}) or {}
            pe = (sd.get("trailingPE") or {}).get("raw")
            if pe is None:
                pe = (sd.get("forwardPE") or {}).get("raw")
            ed = (ce.get("earnings") or {}).get("earningsDate") or []
            edate = ed[0].get("fmt") if ed else None
            out[sym] = {"pe": round(pe, 1) if pe is not None else None,
                        "earnings": edate,
                        "est": len(ed) > 1}
            print(f"OK  fund {sym}: PE={out[sym]['pe']} 財報={edate}")
        except Exception as e:
            print(f"ERR fund {sym}: {str(e)[:80]}")
        time.sleep(0.3)
    return out


out = {}

# 1) 指數(含 fallback)
for sym in INDEXES:
    try:
        out[sym] = build_index(sym)
        tag = f"(fallback -> {out[sym]['src']})" if out[sym].get("fallback") else ""
        print(f"OK  {sym}: {out[sym]['price']} @ {out[sym]['date']} {tag}")
    except Exception as e:
        out[sym] = {"error": str(e), "fallback": False}
        print(f"ERR {sym}: {e}")
    time.sleep(0.25)

# 2) 個股 / ETF
for sym in STOCK_SYMBOLS:
    try:
        out[sym] = build_stock(sym)
        print(f"OK  {sym}: {out[sym]['price']} @ {out[sym]['date']}")
    except Exception as e:
        msg = str(e)
        if "402" in msg or "Payment Required" in msg or "higher plan" in msg.lower():
            msg = "免費方案未支援"
        out[sym] = {"error": msg}
        print(f"ERR {sym}: {e}")
    time.sleep(0.25)

# 3) 個股基本面(P/E + 下次財報日),併進個股並彙整成財報清單
funds = fetch_fundamentals(FUNDAMENTAL_SYMBOLS)
earnings = []
for sym in FUNDAMENTAL_SYMBOLS:
    f = funds.get(sym)
    if not f:
        continue
    if isinstance(out.get(sym), dict) and not out[sym].get("error"):
        if f.get("pe") is not None:
            out[sym]["pe"] = f["pe"]
    if f.get("earnings"):
        earnings.append({"s": sym, "date": f["earnings"], "est": f.get("est", False)})
earnings.sort(key=lambda x: x["date"])
out["_earnings"] = earnings
print(f"\n基本面:P/E {sum(1 for s in FUNDAMENTAL_SYMBOLS if isinstance(out.get(s),dict) and out[s].get('pe') is not None)} 檔,財報日 {len(earnings)} 檔。")

out["_updated"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
with open(os.path.join(HERE, "data.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print(f"\n寫入 data.json,指數 {len(INDEXES)} 檔 + 個股/ETF {len(STOCK_SYMBOLS)} 檔。")
