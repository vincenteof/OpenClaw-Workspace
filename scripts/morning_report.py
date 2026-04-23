#!/usr/bin/env python3
"""
Daily portfolio morning report.
Reads all asset notes, calculates portfolio summary, sends Telegram message via OpenClaw.
Should be run after update_prices.py.
"""

import os
import re
import json
import subprocess
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict

VAULT_PATH = "/Users/vincenteofchen/Documents/vincenteof-obsidian"
ASSETS_PATH = os.path.join(VAULT_PATH, "970 - Investments", "972 - Assets")
SNAPSHOTS_PATH = os.path.join(VAULT_PATH, "970 - Investments", "974 - Snapshots")
TZ = timezone(timedelta(hours=8))
TODAY = datetime.now(tz=TZ).strftime("%Y-%m-%d")


def read_yaml(filepath: str) -> dict:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    yaml_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not yaml_match:
        return {}
    result = {}
    for line in yaml_match.group(1).splitlines():
        m = re.match(r"^(\w[\w_-]*):\s*(.+)$", line)
        if m:
            result[m.group(1)] = m.group(2).strip()
    return result


def load_assets() -> list[dict]:
    assets = []
    for filename in sorted(os.listdir(ASSETS_PATH)):
        if not filename.endswith(".md"):
            continue
        yaml = read_yaml(os.path.join(ASSETS_PATH, filename))
        if yaml.get("type") != "asset":
            continue
        try:
            assets.append({
                "symbol": yaml.get("symbol", ""),
                "category": yaml.get("category", ""),
                "quantity": float(yaml.get("quantity", 0)),
                "avg_cost": float(yaml.get("avg_cost", 0)),
                "current_price": float(yaml.get("current_price", 0)),
                "currency": yaml.get("currency", "USD"),
            })
        except ValueError:
            continue
    return assets


def load_snapshot() -> Optional[Dict]:
    """Load the YTD start snapshot."""
    if not os.path.exists(SNAPSHOTS_PATH):
        return None
    for filename in sorted(os.listdir(SNAPSHOTS_PATH)):
        if not filename.endswith(".md"):
            continue
        yaml = read_yaml(os.path.join(SNAPSHOTS_PATH, filename))
        if yaml.get("period_role") == "ytd_start":
            try:
                return {
                    "date": yaml.get("date", ""),
                    "total_value": float(yaml.get("current_value", yaml.get("total_value", 0))),
                    "net_contributions_since_start": float(yaml.get("net_contributions_since_start", 0)),
                }
            except ValueError:
                return None
    return None


def format_number(n: float, decimals: int = 2) -> str:
    return f"{n:,.{decimals}f}"


def format_pct(n: float) -> str:
    sign = "+" if n >= 0 else ""
    return f"{sign}{n:.2f}%"


def trend_emoji(val: float) -> str:
    return "🟢" if val >= 0 else "🔴"


def build_report(assets: List[Dict], snapshot: Optional[Dict]) -> str:
    date_str = datetime.now(tz=TZ).strftime("%Y-%m-%d")

    # Separate cash and non-cash
    positions = [a for a in assets if a["category"] != "cash"]
    cash_assets = [a for a in assets if a["category"] == "cash"]

    total_cash = sum(a["quantity"] * a["current_price"] for a in cash_assets)
    total_cost = sum(a["quantity"] * a["avg_cost"] for a in positions)
    total_value = sum(a["quantity"] * a["current_price"] for a in positions) + total_cash
    total_invested_value = sum(a["quantity"] * a["current_price"] for a in positions)
    total_gain = sum((a["current_price"] - a["avg_cost"]) * a["quantity"] for a in positions)
    total_return_pct = (total_gain / total_cost * 100) if total_cost > 0 else 0

    gain_sign = "+" if total_gain >= 0 else ""
    gain_emoji = trend_emoji(total_gain)

    lines = []
    lines.append(f"**📊 投资组合早报** · {date_str}")
    lines.append("")
    lines.append(f"**总市值** `${format_number(total_value, 0)}`")
    lines.append(f"**持仓市值** `${format_number(total_invested_value, 0)}`\u3000**现金** `${format_number(total_cash, 0)}`")
    lines.append(f"**总成本** `${format_number(total_cost, 0)}`")
    lines.append(f"**浮动盈亏** {gain_emoji} `{gain_sign}${format_number(total_gain, 0)}  {format_pct(total_return_pct)}`")

    # Period performance
    if snapshot:
        net_contributions = snapshot.get("net_contributions_since_start", 0)
        start_value = snapshot["total_value"]
        period_pl = total_value - start_value - net_contributions
        period_return = (period_pl / start_value * 100) if start_value > 0 else 0
        pp_sign = "+" if period_pl >= 0 else ""
        pp_emoji = trend_emoji(period_pl)
        lines.append(f"**期间收益** {pp_emoji} `{pp_sign}${format_number(period_pl, 0)}  {format_pct(period_return)}`\uff08自 {snapshot['date']}\uff09")

    lines.append("")
    lines.append("\u2501" * 17)
    lines.append("")
    lines.append("**持仓明细**")

    # Individual positions sorted by current value desc
    positions_sorted = sorted(positions, key=lambda a: a["quantity"] * a["current_price"], reverse=True)
    for a in positions_sorted:
        value = a["quantity"] * a["current_price"]
        gain = (a["current_price"] - a["avg_cost"]) * a["quantity"]
        ret_pct = ((a["current_price"] - a["avg_cost"]) / a["avg_cost"] * 100) if a["avg_cost"] > 0 else 0
        weight = (value / total_value * 100) if total_value > 0 else 0
        emoji = trend_emoji(gain)
        ret_str = format_pct(ret_pct)
        lines.append("")
        lines.append(f"{emoji} **{a['symbol']}**\u3000`${format_number(a['current_price'])}`")
        price_str = format_number(a['current_price'], 2)
        lines[-1] = f"{emoji} **{a['symbol']}**\u3000`${price_str}`"
        lines.append(f"\u3000市值 `${format_number(value, 0)}` · 占比 `{weight:.1f}%` · `{ret_str}`")

    return "\n".join(lines)


def send_via_openclaw(message: str):
    result = subprocess.run(
        ["openclaw", "message", "send", "--channel", "telegram", "--target", "8247498175", "--message", message],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"Send failed: {result.stderr}")
    else:
        print("Message sent.")


def main():
    assets = load_assets()
    if not assets:
        print("No assets found.")
        return

    snapshot = load_snapshot()
    report = build_report(assets, snapshot)
    print(report)
    send_via_openclaw(report)


if __name__ == "__main__":
    main()
