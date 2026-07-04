# Market Compass(均線多空羅盤)

顯示大盤指數與持股 / 觀察清單各檔收盤價相對 **週線(5MA)/月線(20MA)/季線(60MA)/年線(240MA)** 的多空狀態(綠=站上、紅=跌破),大盤分頁並附市場訊號紅綠燈。資料由 GitHub Actions 每日自動向 Financial Modeling Prep(FMP)抓取並重算。

## ⚠️ 鐵則:倉庫保持 Public,但不得含任何帳戶數字

> 本倉庫只放代碼、順序與分組,**不得出現股數 / 金額 / 槓桿 / 保證金等任何帳戶數字**。
> 帳戶相關數字(若有)一律不落地:不寫進本倉庫、不進 commit。

## 清單結構(watchlist.json)

清單的唯一來源是 **`watchlist.json`**。要換股 / 改分組,只改這一個檔案,`build_data.py` 與 `index.html` 都會自動跟著讀。改完 push,GitHub Actions 會重抓資料。

```jsonc
{
  "indexes":  ["^GSPC", "^NDX", "^SOX", "^VIX"],          // 大盤分頁指數
  "holdings": [                                            // 實際持股(依此順序顯示)
    { "s": "TSM", "dn": "台積電", "note": "2330 現股+ADR" } // s=抓數據代號, dn=顯示名, note=說明
  ],
  "watch": [                                              // 觀察清單(未持有)
    { "s": "NVDA", "group": "半導體" }                     // group=分組
  ]
}
```

- 抓資料的代碼集合 = `holdings[].s` + `watch[].s`(去重),再加上 `indexes`。
- `build_data.py` 對同一代碼有記憶快取,重複代碼(含 fallback 代理)只抓一次,省 FMP 額度。

## 檔案結構
```
watchlist.json               # ← 唯一清單來源(indexes / holdings / watch)
index.html                   # 前端頁面(fetch watchlist.json + data.json)
data.json                    # 由 Actions 產生的均線資料
build_data.py                # 抓 FMP、算均線、寫 data.json
.github/workflows/update.yml # 每日排程
```

## 指數與免費方案

FMP 免費方案對指數的支援不一致(實測:`^GSPC`、`^VIX` 可用;`^NDX`、`^SOX` 需付費方案)。
FMP 不支援的代碼(含多數指數與個股)會**自動改抓 Yahoo Finance**(chart API)作為第二資料源。
若 Yahoo 也取不到,`build_data.py` 才會對指數**自動 fallback**:改抓對應 ETF,並在頁面標記「以 XXX 代替」。

| 指數 | fallback ETF |
|------|--------------|
| ^GSPC | SPY |
| ^NDX | QQQ |
| ^SOX | SOXX |
| ^VIX | (無等比例 ETF,免費方案通常可直接取得) |

## 上線步驟

1. **設定 FMP API key**:repo 的 `Settings → Secrets and variables → Actions → New repository secret`,名稱 `FMP_API_KEY`,值填你的 FMP API key(<https://site.financialmodelingprep.com>,免費方案即可,僅支援美股)。
2. **開啟 GitHub Pages**:`Settings → Pages → Source 選 "Deploy from a branch" → 分支 main、資料夾 / (root)`(倉庫維持 Public,免費方案即可)。
3. **跑一次資料更新**:`Actions → Update MA data → Run workflow`(或等每日排程)。完成後 `data.json` 更新,網頁即有資料。

## 給 AI 的維護指南

使用者會在 chat 丟兩類更新,處理規則:

1. **關注股票增減**:改 `watchlist.json`——持有變動改 `holdings`(維持淨值權重順序,`s`=FMP 代號、`dn`=顯示名、`note`=說明);觀察標的改 `watch`(`s`+`group`)。改完由使用者自己 `git push`,AI 不執行 push。
2. **IBKR 帳戶截圖**:僅在對話中分析(曝險倍率/借款比例/追繳緩衝),本倉庫與本儀表板不儲存任何帳戶數字。

鐵則:本倉庫 Public,只放代碼、順序與分組;股數/金額/槓桿/保證金一律不落地。

## 本機驗證(選用)

```bash
export FMP_API_KEY=你的key
python build_data.py     # 會就地產生 data.json;可檢查指數是否走 fallback
```

> 注意:清單為美股。台股(0050、2330 等)FMP 免費方案不支援,以 ETF 代理估算。
