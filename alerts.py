#!/usr/bin/env python3
"""季線(60MA)跌破警示。

讀取 build_data.py 產生的 data.json,檢查 ALERT_SYMBOLS 中的標的今天是否
「跌破季線」——也就是 60MA 出現 bear cross(昨天站上、今天跌破)。

若有觸發,透過 $GITHUB_OUTPUT 輸出 triggered=true / subject / body,
供 workflow 後續的寄信步驟使用。無觸發則 triggered=false。

要加/移除警示標的:改下面 ALERT_SYMBOLS 即可(key = data.json 代號、value = 顯示名)。
"""
import json, os

# 大盤持有標的:跌破季線時通知(準備槓桿買入)
ALERT_SYMBOLS = {
    "SXRV.DE": "SXRV",
    "SEC0.DE": "SEC0",
}
ALERT_K = 60          # 季線
ALERT_LABEL = "季線 60MA"

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "data.json"), encoding="utf-8") as f:
    DATA = json.load(f)

hits = []
for sym, name in ALERT_SYMBOLS.items():
    r = DATA.get(sym)
    if not r or r.get("error"):
        continue
    m = next((x for x in r.get("mas", []) if x.get("k") == ALERT_K), None)
    if m and m.get("cross") == "bear":
        price = r.get("price")
        ma = m.get("v")
        diff = m.get("diff")
        cur = r.get("currency", "")
        hits.append(f"{name} ({sym}) 跌破{ALERT_LABEL}:收 {price} {cur} < {ma}（{diff:+.2f}%）")

out_path = os.environ.get("GITHUB_OUTPUT")


def emit(**kv):
    if not out_path:
        return
    with open(out_path, "a", encoding="utf-8") as f:
        for k, v in kv.items():
            if "\n" in str(v):
                f.write(f"{k}<<__EOF__\n{v}\n__EOF__\n")
            else:
                f.write(f"{k}={v}\n")


if hits:
    names = ", ".join(h.split(" (")[0] for h in hits)
    subject = f"⚠️ 均線警示:{names} 跌破{ALERT_LABEL}"
    body = (
        "以下大盤持有標的今天跌破季線(60MA),可考慮你的槓桿買入時機:\n\n- "
        + "\n- ".join(hits)
        + "\n\n看板:https://chouhsuan1202.github.io/ma-dashboard/\n"
        + "(此信由 GitHub Actions 每日自動檢查後寄出)"
    )
    print("ALERT TRIGGERED:\n" + body)
    emit(triggered="true", subject=subject, body=body)
else:
    print(f"No {ALERT_LABEL} bear cross today.")
    emit(triggered="false")
