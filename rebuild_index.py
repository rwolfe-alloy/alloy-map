#!/usr/bin/env python3
"""
Re-embed the project's JSON datasets into index.html.

The data lives as single-line declarations in index.html:
    const LOCATIONS = [ ... ];
    const WHITESPACE = [ ... ];
    const SBA_LOANS = [ ... ];
This rewrites just those lines in place (no separate template needed).
SBA_LOANS is optional — skipped if alloy_sba_loans.json is absent.

Usage: python3 rebuild_index.py
"""
import json, re, os

enr = json.dumps(json.load(open("alloy_enriched.json")),  separators=(",", ":"))
ws  = json.dumps(json.load(open("alloy_whitespace.json")), separators=(",", ":"))
sba = json.dumps(json.load(open("alloy_sba_loans.json")), separators=(",", ":")) if os.path.exists("alloy_sba_loans.json") else "[]"
item19 = json.dumps(json.load(open("alloy_item19.json")), separators=(",", ":")) if os.path.exists("alloy_item19.json") else "{}"
churn = json.dumps(json.load(open("alloy_churn.json")), separators=(",", ":")) if os.path.exists("alloy_churn.json") else "{}"
trends = json.dumps(json.load(open("alloy_trends.json")), separators=(",", ":")) if os.path.exists("alloy_trends.json") else "{}"

html = open("index.html").read()
# lambda replacement avoids re interpreting backslash escapes (e.g. \u) in the JSON
html, n1 = re.subn(r"const LOCATIONS = \[.*?\];",  lambda m: f"const LOCATIONS = {enr};",  html, count=1)
html, n2 = re.subn(r"const WHITESPACE = \[.*?\];", lambda m: f"const WHITESPACE = {ws};", html, count=1)
html, n3 = re.subn(r"const SBA_LOANS = \[.*?\];",  lambda m: f"const SBA_LOANS = {sba};",  html, count=1)
html, n4 = re.subn(r"const ITEM19 = \{.*?\};",     lambda m: f"const ITEM19 = {item19};",  html, count=1)
html, n5 = re.subn(r"const CHURN = \{.*?\};",       lambda m: f"const CHURN = {churn};",    html, count=1)
html, n6 = re.subn(r"const TRENDS = \{.*?\};",      lambda m: f"const TRENDS = {trends};",  html, count=1)

if min(n1, n2, n3, n4, n5, n6) != 1:
    raise SystemExit(f"!! Replacement failed (LOCATIONS={n1}, WHITESPACE={n2}, SBA_LOANS={n3}, ITEM19={n4}, CHURN={n5}, TRENDS={n6}). index.html not modified.")

open("index.html", "w").write(html)
print(f"Rebuilt index.html — {len(json.loads(enr))} locations, {len(json.loads(ws))} whitespace metros, "
      f"{len(json.loads(sba))} SBA loans, Item 19 {'embedded' if item19!='{}' else 'absent'}.")
