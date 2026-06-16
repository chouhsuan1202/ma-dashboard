# 均線多空總覽(美股)

公開的靜態 dashboard:顯示觀察清單各股收盤價相對 **週線(5MA)/月線(20MA)/季線(60MA)/年線(240MA)** 的多空狀態(綠=站上、紅=跌破)。資料由 GitHub Actions 每日自動向 Financial Modeling Prep(FMP)抓取並重算。

## 檔案結構
```
index.html                 # 前端頁面(讀 data.json)
data.json                  # 由 Actions 產生的資料
scripts/build_data.py      # 抓 FMP、算均線、寫 data.json
.github/workflows/update.yml  # 每日排程
```

## 上線步驟

1. **建立 repo** 並把這些檔案放進去(見下方 git 指令)。
2. **設定 FMP API key**:到 repo 的 `Settings → Secrets and variables → Actions → New repository secret`,
   名稱填 `FMP_API_KEY`,值填你的 FMP API key(在 https://site.financialmodelingprep.com 帳戶取得,免費方案即可,僅支援美股)。
3. **開啟 GitHub Pages**:`Settings → Pages → Build and deployment → Source 選 "Deploy from a branch" → 分支 main、資料夾 / (root)`。
4. **跑一次資料更新**:`Actions → Update MA data → Run workflow`(或等每日排程)。完成後 `data.json` 會被更新,網頁即有資料。
5. 你的網站網址:`https://<你的帳號>.github.io/<repo 名稱>/`

## 本機 push 指令
```bash
cd ma-site
git init
git add .
git commit -m "init: MA dashboard"
git branch -M main
git remote add origin https://github.com/<你的帳號>/<repo 名稱>.git
git push -u origin main
```

> 注意:清單為美股。台股(0050、2330 等)FMP 免費方案不支援,仍請用 Cowork 內的即時版查看。
