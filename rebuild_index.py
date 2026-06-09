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

html = open("index.html").read()
# lambda replacement avoids re interpreting backslash escapes (e.g. \u) in the JSON
html, n1 = re.subn(r"const LOCATIONS = \[.*?\];",  lambda m: f"const LOCATIONS = {enr};",  html, count=1)
html, n2 = re.subn(r"const WHITESPACE = \[.*?\];", lambda m: f"const WHITESPACE = {ws};", html, count=1)
html, n3 = re.subn(r"const SBA_LOANS = \[.*?\];",  lambda m: f"const SBA_LOANS = {sba};",  html, count=1)

if n1 != 1 or n2 != 1 or n3 != 1:
    raise SystemExit(f"!! Replacement failed (LOCATIONS={n1}, WHITESPACE={n2}, SBA_LOANS={n3}). index.html not modified.")

open("index.html", "w").write(html)
print(f"Rebuilt index.html — {len(json.loads(enr))} locations, {len(json.loads(ws))} whitespace metros, {len(json.loads(sba))} SBA loans.")
