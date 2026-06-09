#!/usr/bin/env python3
"""
Re-embed alloy_enriched.json + alloy_whitespace.json into index.html.

The data lives as two single-line declarations in index.html:
    const LOCATIONS = [ ... ];
    const WHITESPACE = [ ... ];
This rewrites just those two lines in place (no separate template needed).

Usage: python3 rebuild_index.py
"""
import json, re

enr = json.dumps(json.load(open("alloy_enriched.json")),  separators=(",", ":"))
ws  = json.dumps(json.load(open("alloy_whitespace.json")), separators=(",", ":"))

html = open("index.html").read()
# lambda replacement avoids re interpreting backslash escapes (e.g. \u) in the JSON
html, n1 = re.subn(r"const LOCATIONS = \[.*?\];",  lambda m: f"const LOCATIONS = {enr};",  html, count=1)
html, n2 = re.subn(r"const WHITESPACE = \[.*?\];", lambda m: f"const WHITESPACE = {ws};", html, count=1)

if n1 != 1 or n2 != 1:
    raise SystemExit(f"!! Replacement failed (LOCATIONS={n1}, WHITESPACE={n2}). index.html not modified.")

open("index.html", "w").write(html)
print(f"Rebuilt index.html — embedded {len(json.loads(enr))} locations, {len(json.loads(ws))} whitespace metros.")
