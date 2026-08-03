#!/usr/bin/env python3
"""
Theme 4 — download the current registered FDD for each peer franchise from the
Wisconsin DFI portal (same viewstate flow as fetch_fdd.py, generalized).

Saves _fdd_peer_<key>.pdf (gitignored — re-runnable). Peers and their search
terms; the newest "Registered" filing whose trade name matches is taken.

Usage: python3 fetch_peer_fdds.py
"""
import re, subprocess, urllib.parse, html as hm, sys, time, os

BASE = "https://apps.dfi.wi.gov/apps/FranchiseSearch"
PEERS = [
    ("otf", "Orangetheory", r"orangetheory"),
    ("f45", "F45", r"f45 training"),
    ("sl", "Stretch", r"stretch lab"),
    ("cp", "Club Pilates", r"club pilates"),
    ("ec", "Exercise Coach", r"exercise coach"),
    ("ft", "Fitness Together", r"fitness together"),
]

def curl(args, jar):
    return subprocess.run(["curl", "-s", "--connect-timeout", "20", "--max-time", "300",
                           "-b", jar, "-c", jar] + args, capture_output=True, text=True, timeout=330).stdout

def curl_bin(args, jar, out):
    subprocess.run(["curl", "-s", "--connect-timeout", "20", "--max-time", "600",
                    "-b", jar, "-c", jar, "-o", out] + args, timeout=630)

def hidden(h):
    f = {}
    for m in re.finditer(r'<input[^>]*type="hidden"[^>]*>', h):
        n = re.search(r'name="([^"]*)"', m.group(0)); v = re.search(r'value="([^"]*)"', m.group(0))
        if n: f[n.group(1)] = hm.unescape(v.group(1)) if v else ""
    return f

def fetch_one(key, term, trade_re):
    jar = f"/tmp/wi_{key}.txt"
    if os.path.exists(jar): os.remove(jar)
    page = curl([f"{BASE}/MainSearch.aspx"], jar)
    f = hidden(page); f["txtName"] = term; f["btnSearch"] = "(S)earch"
    resp = curl(["-X", "POST", f"{BASE}/MainSearch.aspx",
                 "-H", "Content-Type: application/x-www-form-urlencoded",
                 "--data", urllib.parse.urlencode(f)], jar)
    r = re.search(r'href="([^"]+)"', resp)
    if not r: return f"{key}: no redirect"
    res = curl(["-L", "https://apps.dfi.wi.gov" + hm.unescape(r.group(1))], jar)
    # rows: pick Registered row whose text matches the trade name; take highest id
    best = None
    for m in re.finditer(r'<tr[^>]*>(.*?)</tr>', res, re.S):
        row = m.group(1)
        txt = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', row)).lower()
        if "registered" not in txt or not re.search(trade_re, txt): continue
        link = re.search(r'details\.aspx\?id=(\d+)&(?:amp;)?hash=(\d+)[^"\']*', row)
        if link and (best is None or int(link.group(1)) > best[0]):
            best = (int(link.group(1)), link.group(2))
    if not best: return f"{key}: no registered filing matched"
    fid, fhash = best
    durl = f"{BASE}/details.aspx?id={fid}&hash={fhash}&search=external&type=GENERAL"
    detail = curl(["-L", durl], jar)
    df = hidden(detail); df["upload_downloadFile"] = "Download"
    out = f"_fdd_peer_{key}.pdf"
    curl_bin(["-L", "-X", "POST", durl, "-H", "Content-Type: application/x-www-form-urlencoded",
              "--data", urllib.parse.urlencode(df)], jar, out)
    size = os.path.getsize(out) if os.path.exists(out) else 0
    return f"{key}: filing #{fid} → {out} ({size/1e6:.1f} MB)" if size > 500_000 else f"{key}: DOWNLOAD LOOKS WRONG ({size} bytes)"

for key, term, trade in PEERS:
    print(fetch_one(key, term, trade)); time.sleep(1)
