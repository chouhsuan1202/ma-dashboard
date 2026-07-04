#!/bin/bash
# Market Compass 本地啟動器:雙擊即用(視窗保持開著=伺服器運作中)
cd "$(dirname "$0")"
echo "同步最新資料中…"
git pull --rebase --autostash 2>&1 | tail -1
( sleep 1 && open "http://localhost:8642" ) &
echo ""
echo "✅ Market Compass → http://localhost:8642"
echo "⚠️  這個視窗要保持開著;關閉即停止。"
echo ""
python3 -m http.server 8642
