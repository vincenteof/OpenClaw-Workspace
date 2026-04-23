#!/usr/bin/env python3
"""
Investment portfolio price updater.
Reads all asset notes in 972 - Assets/, fetches latest prices from Yahoo Finance,
updates current_price in YAML frontmatter, then commits and pushes.
"""

import os
import re
import json
import subprocess
import urllib.request
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple, List

VAULT_PATH = "/Users/vincenteofchen/Documents/vincenteof-obsidian"
ASSETS_PATH = os.path.join(VAULT_PATH, "970 - Investments", "972 - Assets")
TODAY = datetime.now(tz=timezone(timedelta(hours=8))).strftime("%Y-%m-%d")

# Symbol mapping: YAML symbol -> Yahoo Finance query symbol
SYMBOL_MAP = {
    "BTC": "BTC-USD",
    "ETH": "ETH-USD",
    "BRK/B": "BRK-B",
}

# Symbols to skip (no price data needed)
SKIP_SYMBOLS = {"USD-CASH", "HKD-CASH", "CNY-CASH"}


def fetch_price(yahoo_symbol: str) -> Optional[float]:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}?interval=1d&range=1d"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        return data["chart"]["result"][0]["meta"]["regularMarketPrice"]
    except Exception as e:
        print(f"  ERROR fetching {yahoo_symbol}: {e}")
        return None


def read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path: str, content: str):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def update_yaml_field(content: str, field: str, value) -> str:
    pattern = rf"(^{field}:\s*)(.+)$"
    replacement = rf"\g<1>{value}"
    return re.sub(pattern, replacement, content, flags=re.MULTILINE)


def update_platform_table_price(content: str, new_price: float) -> str:
    """Update current_price column in platform distribution table in note body."""
    lines = content.split("\n")
    result = []
    in_platform_table = False
    header_passed = False

    for line in lines:
        if "## 平台分布" in line:
            in_platform_table = True
            result.append(line)
            continue

        if in_platform_table:
            if line.startswith("|") and "平台" in line:
                header_passed = True
                result.append(line)
                continue
            if line.startswith("|---"):
                result.append(line)
                continue
            if line.startswith("|") and header_passed:
                # Data row: | 平台 | 数量 | 平均成本 | 当前价格 | 货币 |
                cols = line.split("|")
                if len(cols) >= 6:
                    cols[4] = f" {new_price:.2f} "
                    line = "|".join(cols)
                result.append(line)
                continue
            else:
                in_platform_table = False

        result.append(line)

    return "\n".join(result)


def process_asset(filepath: str) -> Tuple[str, Optional[float], Optional[float]]:
    """Returns (symbol, old_price, new_price) or (symbol, None, None) if skipped."""
    content = read_file(filepath)

    # Extract symbol
    symbol_match = re.search(r"^symbol:\s*(.+)$", content, re.MULTILINE)
    category_match = re.search(r"^category:\s*(.+)$", content, re.MULTILINE)
    price_match = re.search(r"^current_price:\s*(.+)$", content, re.MULTILINE)

    if not symbol_match:
        return ("unknown", None, None)

    symbol = symbol_match.group(1).strip()
    category = category_match.group(1).strip() if category_match else ""
    old_price = float(price_match.group(1).strip()) if price_match else None

    if symbol in SKIP_SYMBOLS or category == "cash":
        return (symbol, None, None)

    yahoo_symbol = SYMBOL_MAP.get(symbol, symbol)
    new_price = fetch_price(yahoo_symbol)

    if new_price is None:
        return (symbol, old_price, None)

    new_price = round(new_price, 2)

    # Update YAML
    new_content = update_yaml_field(content, "current_price", new_price)
    new_content = update_yaml_field(new_content, "last_updated", TODAY)

    # Update platform table if present
    if "## 平台分布" in new_content:
        new_content = update_platform_table_price(new_content, new_price)

    write_file(filepath, new_content)
    return (symbol, old_price, new_price)


def git_commit_push(changed_files: List[str]):
    if not changed_files:
        print("No files changed, skipping git commit.")
        return

    rel_files = [os.path.relpath(f, VAULT_PATH) for f in changed_files]
    # stash → pull → apply stash → commit → push
    subprocess.run(["git", "-C", VAULT_PATH, "stash"], check=True)
    subprocess.run(["git", "-C", VAULT_PATH, "pull", "--rebase"], check=True)
    subprocess.run(["git", "-C", VAULT_PATH, "stash", "pop"], check=True)
    subprocess.run(["git", "-C", VAULT_PATH, "add"] + rel_files, check=True)
    result = subprocess.run(
        ["git", "-C", VAULT_PATH, "commit", "-m", f"prices: update current_price {TODAY}"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        subprocess.run(["git", "-C", VAULT_PATH, "push"], check=True)
        print("Git: committed and pushed.")
    else:
        print("Git: nothing to commit.")


def main():
    print(f"=== Price Update {TODAY} ===")
    changed_files = []
    results = []

    for filename in sorted(os.listdir(ASSETS_PATH)):
        if not filename.endswith(".md"):
            continue
        filepath = os.path.join(ASSETS_PATH, filename)
        symbol, old_price, new_price = process_asset(filepath)

        if new_price is None:
            if old_price is not None:
                print(f"  {symbol}: SKIPPED or ERROR")
            continue

        changed_files.append(filepath)
        change = new_price - old_price if old_price else 0
        pct = (change / old_price * 100) if old_price else 0
        sign = "+" if change >= 0 else ""
        print(f"  {symbol}: {old_price} → {new_price} ({sign}{change:.2f}, {sign}{pct:.2f}%)")
        results.append((symbol, old_price, new_price, change, pct))

    git_commit_push(changed_files)
    return results


if __name__ == "__main__":
    main()
