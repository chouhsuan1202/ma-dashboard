#!/bin/bash
# Market Compass 背景伺服器(由 launchd 管理,勿手動執行)
cd "$(dirname "$0")"
# 若埠已被占用,先清掉舊的
lsof -ti tcp:8642 | xargs kill 2>/dev/null
git pull --rebase --autostash >/dev/null 2>&1
exec /usr/bin/python3 -m http.server 8642
