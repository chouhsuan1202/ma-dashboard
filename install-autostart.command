#!/bin/bash
# Market Compass 背景服務安裝器:只需雙擊一次
# 之後開機自動啟動 http://localhost:8642,不再需要終端機視窗
set -e
REPO="$(cd "$(dirname "$0")" && pwd)"
AGENTS="$HOME/Library/LaunchAgents"
mkdir -p "$AGENTS"
chmod +x "$REPO/serve.sh"

# 1) 常駐伺服器(登入即啟動,掛掉自動重啟)
cat > "$AGENTS/com.hsuan.marketcompass.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.hsuan.marketcompass</string>
  <key>ProgramArguments</key><array>
    <string>/bin/bash</string><string>$REPO/serve.sh</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
</dict></plist>
EOF

# 2) 每天 09:00 自動同步最新資料
cat > "$AGENTS/com.hsuan.marketcompass.pull.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.hsuan.marketcompass.pull</string>
  <key>ProgramArguments</key><array>
    <string>/usr/bin/git</string><string>-C</string><string>$REPO</string>
    <string>pull</string><string>--rebase</string><string>--autostash</string>
  </array>
  <key>StartCalendarInterval</key><dict><key>Hour</key><integer>9</integer><key>Minute</key><integer>0</integer></dict>
</dict></plist>
EOF

launchctl unload "$AGENTS/com.hsuan.marketcompass.plist" 2>/dev/null || true
launchctl unload "$AGENTS/com.hsuan.marketcompass.pull.plist" 2>/dev/null || true
launchctl load "$AGENTS/com.hsuan.marketcompass.plist"
launchctl load "$AGENTS/com.hsuan.marketcompass.pull.plist"

sleep 2
open "http://localhost:8642"
echo ""
echo "✅ 安裝完成!Market Compass 已常駐背景:"
echo "   · http://localhost:8642 隨時可開,不需要終端機"
echo "   · 開機自動啟動;每天 09:00 自動同步資料"
echo ""
echo "(若要移除:launchctl unload ~/Library/LaunchAgents/com.hsuan.marketcompass*.plist)"
read -p "按 Enter 關閉此視窗"
