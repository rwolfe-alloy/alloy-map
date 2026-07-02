#!/usr/bin/env python3
"""
Theme 2 — fetch trade-area demographics (median household income + population)
from Census Reporter's keyless ACS API.

- Locations: ZCTA level, by the zip in each address (batched requests).
- Whitespace metros: CBSA level, resolved by name search.

Output: alloy_demog.json
  { "source":..., "zips": {"30101": {"inc":110774,"pop":62593}, ...},
    "metros": {"Sacramento": {"inc":..., "pop":...}, ...} }

Usage: python3 fetch_demographics.py
"""
import json, re, subprocess, time, urllib.parse

API = "https://api.censusreporter.org/1.0"

def curl_json(url):
    try:
        out = subprocess.run(["curl", "-s", "--connect-timeout", "15", "--max-time", "60", url],
                             capture_output=True, text=True, timeout=75).stdout
        return json.loads(out)
    except Exception:
        return {}

locs = json.load(open("alloy_enriched.json"))
ws = json.load(open("alloy_whitespace.json"))

def zip5(a):
    z = re.findall(r"\b\d{5}\b", a or "")
    return z[-1] if z else None

zips = sorted({zip5(l["a"]) for l in locs if zip5(l["a"])})
print(f"{len(zips)} unique zips")

# ── ZCTA income + population, batched ──
zip_data = {}
BATCH = 40
for i in range(0, len(zips), BATCH):
    batch = zips[i:i+BATCH]
    ids = ",".join(f"86000US{z}" for z in batch)
    d = curl_json(f"{API}/data/show/latest?table_ids=B19013,B01003&geo_ids={ids}")
    for gid, tables in (d.get("data") or {}).items():
        z = gid[-5:]
        inc = (tables.get("B19013", {}).get("estimate") or {}).get("B19013001")
        pop = (tables.get("B01003", {}).get("estimate") or {}).get("B01003001")
        if inc or pop:
            zip_data[z] = {"inc": int(inc) if inc else None, "pop": int(pop) if pop else None}
    print(f"  batch {i//BATCH+1}: {len(zip_data)} zips resolved")
    time.sleep(1)

# ── whitespace metros: name → CBSA → income/pop ──
metro_data = {}
for w in ws:
    q = urllib.parse.quote(w["name"])
    s = curl_json(f"{API}/geo/search?q={q}&sumlevs=310")
    results = s.get("results") or []
    if not results:
        print(f"  metro {w['name']}: no CBSA match"); continue
    gid = results[0]["full_geoid"]
    d = curl_json(f"{API}/data/show/latest?table_ids=B19013,B01003&geo_ids={gid}")
    t = (d.get("data") or {}).get(gid, {})
    inc = (t.get("B19013", {}).get("estimate") or {}).get("B19013001")
    pop = (t.get("B01003", {}).get("estimate") or {}).get("B01003001")
    metro_data[w["name"]] = {"inc": int(inc) if inc else None, "pop": int(pop) if pop else None,
                             "cbsa": results[0].get("full_name")}
    time.sleep(0.6)

out = {"source": "US Census ACS 5-year (via Census Reporter), ZCTA + CBSA level",
       "zips": zip_data, "metros": metro_data}
json.dump(out, open("alloy_demog.json", "w"), separators=(",", ":"))

covered = sum(1 for l in locs if zip5(l["a"]) in zip_data)
print(f"done: {len(zip_data)} zips ({covered}/{len(locs)} locations covered), {len(metro_data)} whitespace metros")
