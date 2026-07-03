#!/usr/bin/env python3
"""
Theme 2 — count boutique-fitness competitors near each location (5 mi) and
each whitespace metro center (15 mi), via Places API (New) searchText with a
location bias circle. Brands: Orangetheory, F45, StretchLab.

Output: alloy_competitors.json
  { "radius_mi": {...}, "brands":[...],
    "locations": {"<name>": {"otf":1,"f45":0,"sl":2,"total":3}},
    "metros":    {"Sacramento": {...}},
    "places":    [{"b":"otf","n":"Orangetheory ...","lat":..,"lng":..}] }  # deduped, for the map overlay

Needs .apikey (same key as fetch_ratings). ~555 API calls.
Usage: python3 fetch_competitors.py
"""
import json, os, subprocess, sys, time
from math import radians, sin, cos, asin, sqrt

KEY = open(".apikey").read().strip() if os.path.exists(".apikey") else os.environ.get("GOOGLE_PLACES_API_KEY", "")
if not KEY:
    sys.exit("No API key (.apikey or $GOOGLE_PLACES_API_KEY)")

URL = "https://places.googleapis.com/v1/places:searchText"
BRANDS = [("otf", "Orangetheory Fitness"), ("f45", "F45 Training"), ("sl", "StretchLab")]
# Text search fuzzy-matches other gyms when exact brand hits are scarce (e.g. a
# "24 Hour Fitness" returned for the F45 query) — require the brand in the name.
import re
BRAND_RE = {"otf": re.compile(r"orange\s*theory", re.I),
            "f45": re.compile(r"f45", re.I),
            "sl":  re.compile(r"stretch\s*lab", re.I)}

def hav(a, b, c, e):
    p = radians; dl = p(e - b); dt = p(c - a)
    return 3958.8 * 2 * asin(sqrt(sin(dt/2)**2 + cos(p(a))*cos(p(c))*sin(dl/2)**2))

PLACES = {}   # place id -> {b, n, lat, lng}, deduped across all search circles

def count_near(lat, lng, query, radius_mi, brand_key):
    body = json.dumps({"textQuery": query,
        "locationBias": {"circle": {"center": {"latitude": lat, "longitude": lng},
                                    "radius": min(radius_mi * 1609.34, 50000)}}})
    cmd = ["curl", "-s", "--connect-timeout", "15", "--max-time", "45", "-X", "POST", URL,
           "-H", "Content-Type: application/json", "-H", f"X-Goog-Api-Key: {KEY}",
           "-H", "X-Goog-FieldMask: places.id,places.location,places.displayName", "-d", body]
    for attempt in range(2):
        try:
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=60).stdout
            d = json.loads(out)
        except Exception:
            continue
        if "error" in d:
            sys.exit(f"!! API error: {d['error'].get('message','')[:120]}")
        hits = [p for p in d.get("places", [])
                if hav(lat, lng, p["location"]["latitude"], p["location"]["longitude"]) <= radius_mi
                and BRAND_RE[brand_key].search((p.get("displayName") or {}).get("text", ""))]
        for p in hits:
            pid = p.get("id")
            if pid and pid not in PLACES:
                PLACES[pid] = {"b": brand_key,
                               "n": (p.get("displayName") or {}).get("text", ""),
                               "lat": round(p["location"]["latitude"], 5),
                               "lng": round(p["location"]["longitude"], 5)}
        return len(hits)
    return None   # both attempts failed — recorded as unknown, not zero

def scan(items, radius_mi, label):
    out = {}
    for i, (name, lat, lng) in enumerate(items, 1):
        counts, total = {}, 0
        for key, query in BRANDS:
            c = count_near(lat, lng, query, radius_mi, key)
            counts[key] = c
            total += c or 0
        counts["total"] = total
        out[name] = counts
        if i % 20 == 0 or i == len(items):
            print(f"  {label} {i}/{len(items)}")
        time.sleep(0.1)
    return out

locs = json.load(open("alloy_enriched.json"))
ws = json.load(open("alloy_whitespace.json"))

result = {
    "source": "Google Places API (New) text search, location-bias circle",
    "radius_mi": {"locations": 5, "metros": 15},
    "brands": [b[1] for b in BRANDS],
    "locations": scan([(l["n"], l["lat"], l["lng"]) for l in locs], 5, "location"),
    "metros": scan([(w["name"], w["lat"], w["lng"]) for w in ws], 15, "metro"),
}
result["places"] = sorted(PLACES.values(), key=lambda p: (p["b"], p["n"]))
json.dump(result, open("alloy_competitors.json", "w"), separators=(",", ":"))

tot = sum(v["total"] for v in result["locations"].values())
free = sum(1 for v in result["locations"].values() if v["total"] == 0)
print(f"done: {tot} competitor sightings near {len(locs)} locations ({free} competitor-free), "
      f"{len(ws)} metros, {len(result['places'])} unique studios mapped")
