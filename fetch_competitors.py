#!/usr/bin/env python3
"""
Theme 2 — count boutique-fitness competitors near each location (5 mi) and
each whitespace metro center (15 mi), via Places API (New) searchText with a
location bias circle. Brands: Orangetheory, F45, StretchLab.

Output: alloy_competitors.json
  { "radius_mi": {...}, "brands":[...],
    "locations": {"<name>": {"otf":1,"f45":0,"sl":2,"total":3}},
    "metros":    {"Sacramento": {...}} }

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

def hav(a, b, c, e):
    p = radians; dl = p(e - b); dt = p(c - a)
    return 3958.8 * 2 * asin(sqrt(sin(dt/2)**2 + cos(p(a))*cos(p(c))*sin(dl/2)**2))

def count_near(lat, lng, query, radius_mi):
    body = json.dumps({"textQuery": query,
        "locationBias": {"circle": {"center": {"latitude": lat, "longitude": lng},
                                    "radius": min(radius_mi * 1609.34, 50000)}}})
    cmd = ["curl", "-s", "--connect-timeout", "15", "--max-time", "45", "-X", "POST", URL,
           "-H", "Content-Type: application/json", "-H", f"X-Goog-Api-Key: {KEY}",
           "-H", "X-Goog-FieldMask: places.location", "-d", body]
    for attempt in range(2):
        try:
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=60).stdout
            d = json.loads(out)
        except Exception:
            continue
        if "error" in d:
            sys.exit(f"!! API error: {d['error'].get('message','')[:120]}")
        return sum(1 for p in d.get("places", [])
                   if hav(lat, lng, p["location"]["latitude"], p["location"]["longitude"]) <= radius_mi)
    return None   # both attempts failed — recorded as unknown, not zero

def scan(items, radius_mi, label):
    out = {}
    for i, (name, lat, lng) in enumerate(items, 1):
        counts, total = {}, 0
        for key, query in BRANDS:
            c = count_near(lat, lng, query, radius_mi)
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
json.dump(result, open("alloy_competitors.json", "w"), separators=(",", ":"))

tot = sum(v["total"] for v in result["locations"].values())
free = sum(1 for v in result["locations"].values() if v["total"] == 0)
print(f"done: {tot} competitors near {len(locs)} locations ({free} competitor-free), {len(ws)} metros scanned")
