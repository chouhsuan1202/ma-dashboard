#!/bin/bash
# Market Compass 本地啟動器:雙擊即用
# 1) 從 GitHub 拉最新資料(離線也能用,只是資料停在上次)
# 2) 啟動本機伺服器並打開瀏覽器
cd "$(dirname "$0")"
git pull --rebase --autostash >/dev/null 2>&1
( sleep 1 && open "http://localhost:8642" ) &
echo "Market Compass 已啟動 → http://localhost:8642"
echo "(關閉這個視窗即停止)"
python3 -m http.server 8642 >/dev/null 2>&1
