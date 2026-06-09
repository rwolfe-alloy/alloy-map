#!/usr/bin/env python3
"""
Re-scrape Alloy locations + per-location enrichment and MERGE into alloy_enriched.json.

Pulls: name, address, lat/lng, phone, placeId from the /locations/ page;
year + canonical URL from the WP REST API; hours, email, instagram, facebook,
coming_soon from each location page.

MERGE-PRESERVING: keeps Phase 4–6 fields (place_id, rating, review_count, owner,
franchisee) on existing records, updates the volatile fields, and appends new
locations. region is derived from state; metro from nearest existing centroid.

Safety: aborts (non-zero exit, no file written) if the scrape yields fewer than
90% of the current location count — a signal the site structure changed.

Usage: python3 scrape_locations.py
"""
import csv, json, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from math import radians, sin, cos, asin, sqrt

LOCS_URL = "https://www.alloypersonaltraining.com/locations/"
WP_URL = "https://alloypersonaltraining.com/wp-json/wp/v2/location?per_page=100&page={}&_fields=id,date,link"
ENRICHED = "alloy_enriched.json"

DAYS = [("Monday","Mon"),("Tuesday","Tue"),("Wednesday","Wed"),("Thursday","Thu"),
        ("Friday","Fri"),("Saturday","Sat"),("Sunday","Sun")]
REGION = {  # state -> region (matches existing dataset's convention)
 **{s:"Northeast" for s in "CT ME MA NH RI VT NJ NY PA".split()},
 **{s:"Southeast" for s in "DE FL GA MD NC SC VA WV AL KY MS TN AR LA DC".split()},
 **{s:"Midwest"   for s in "IL IN MI OH WI IA KS MN MO NE ND SD".split()},
 **{s:"Southwest" for s in "AZ NM OK TX".split()},
 **{s:"West"      for s in "AK CA CO HI ID MT NV OR UT WA WY".split()}}

def curl(url):
    try:
        return subprocess.run(["curl","-s","-L","--connect-timeout","15","--max-time","45",url],
                              capture_output=True, text=True, timeout=60).stdout
    except subprocess.TimeoutExpired:
        return ""

def clean(s): return re.sub(r"\s+"," ",(s or "")).strip()

def decode_cfemail(h):
    r = bytes.fromhex(h); k = r[0]
    return "".join(chr(b ^ k) for b in r[1:])

def haversine(a, b, c, d):
    p = radians; dlon = p(d-b); dlat = p(c-a)
    h = sin(dlat/2)**2 + cos(p(a))*cos(p(c))*sin(dlon/2)**2
    return 3958.8 * 2 * asin(sqrt(h))

# ── 1. Locations array ──
def parse_locations(html):
    m = re.search(r"var locations\s*=\s*\[\s*\{", html)
    if not m: return []
    arr = html[m.start(): html.find("];", m.start())]
    recs = []
    for o in re.split(r"(?=\{\s*\n?\s*\"name\")", arr):
        nm = re.search(r"\"name\"\s*:\s*\"([^\"]+)\"", o)
        if not nm: continue
        ad = re.search(r"\"address\"\s*:\s*\"([^\"]+)\"", o)
        la = re.search(r"\"lat\"\s*:\s*(-?[\d.]+)", o)
        lo = re.search(r"\"lng\"\s*:\s*(-?[\d.]+)", o)
        pid = re.search(r"\"placeId\"\s*:\s*\"([^\" ]+)", o)
        post = re.search(r"\"postid\"\s*:\s*\"(\d+)\"", o)
        recs.append({"n": re.sub(r"^Alloy\s*\|\s*", "", nm.group(1)).strip(),
            "a": ad.group(1).strip() if ad else None,
            "lat": round(float(la.group(1)), 6) if la else None,
            "lng": round(float(lo.group(1)), 6) if lo else None,
            "place_id": pid.group(1) if pid else None,
            "postid": post.group(1) if post else None})
    return recs

# ── 2. WP REST: postid -> year, url ──
def fetch_wp():
    out = {}
    for page in (1, 2, 3):
        data = curl(WP_URL.format(page))
        try: rows = json.loads(data)
        except json.JSONDecodeError: break
        if not isinstance(rows, list) or not rows: break
        for r in rows:
            out[str(r["id"])] = {"y": (r.get("date") or "")[:4], "u": r.get("link")}
    return out

# ── 3. Per-location page scrape ──
def scrape_page(url):
    if not url: return {}
    html = curl(url)
    d = {}
    hours = {}
    for full, ab in DAYS:
        m = re.search(full + r":\s*([^<\n]{1,40})", html)
        if m: hours[ab] = clean(m.group(1))
    if hours: d["hours"] = hours
    cf = re.search(r'data-cfemail="([a-f0-9]+)"', html)
    if cf:
        try: d["email"] = decode_cfemail(cf.group(1))
        except Exception: pass
    # per-location handle only — skip the brand's footer accounts
    GENERIC = {"alloyptfranchise","alloypersonaltraining","teamalloy","alloy","alloypt",
               "sharer","plugins","tr","profile.php","pages"}
    igs = [h.strip("/") for h in re.findall(r'instagram\.com/([A-Za-z0-9._]+)', html)]
    d["instagram"] = next((h for h in igs if h.lower() not in GENERIC), None)
    fbs = [h.strip("/") for h in re.findall(r'facebook\.com/([A-Za-z0-9._]+)', html)]
    d["facebook"] = next((h for h in fbs if h.lower() not in GENERIC), None)
    tel = re.search(r'tel:([+\d().\- ]{7,})', html)
    if tel: d["p"] = clean(tel.group(1))
    d["coming_soon"] = bool(re.search(r"COMING SOON OPENING", html, re.I))
    return d

def main():
    existing = json.load(open(ENRICHED))
    by_name = {l["n"]: l for l in existing}
    # region map derived from existing data (authoritative — preserves the dataset's
    # own convention, e.g. MD=Northeast), with the standard map as fallback for new states
    region_map = {l["s"]: l["r"] for l in existing if l.get("s") and l.get("r")}

    html = curl(LOCS_URL)
    locs = parse_locations(html)
    if len(locs) < 0.9 * len(existing):
        sys.exit(f"!! ABORT: scraped {len(locs)} locations < 90% of current {len(existing)}. "
                 "Site structure may have changed; not writing.")

    wp = fetch_wp()
    # metro centroids from existing data (for assigning new locations)
    centroids = {}
    for l in existing:
        if l.get("m") and l.get("lat"):
            centroids.setdefault(l["m"], []).append((l["lat"], l["lng"]))
    centroids = {m: (sum(x[0] for x in v)/len(v), sum(x[1] for x in v)/len(v)) for m, v in centroids.items()}
    def nearest_metro(lat, lng):
        best, bd = None, 50
        for m, (clat, clng) in centroids.items():
            dist = haversine(lat, lng, clat, clng)
            if dist < bd: best, bd = m, dist
        return best

    # scrape pages concurrently (use WP url, else build from existing)
    for l in locs:
        meta = wp.get(l["postid"] or "", {})
        l["y"] = meta.get("y")
        l["u"] = meta.get("u") or (by_name.get(l["n"], {}) or {}).get("u")
    with ThreadPoolExecutor(max_workers=10) as ex:
        scraped = list(ex.map(lambda l: scrape_page(l["u"]), locs))

    out = []
    for l, sc in zip(locs, scraped):
        prev = by_name.get(l["n"], {})
        rec = dict(prev)  # start from existing → preserves owner/franchisee/rating/review_count/place_id
        rec["n"] = l["n"]
        rec["a"] = l["a"] or prev.get("a")
        rec["s"] = (re.search(r",\s*([A-Z]{2})\s+\d{5}", l["a"] or "") or [None, prev.get("s")])[1] if l["a"] else prev.get("s")
        rec["r"] = region_map.get(rec.get("s")) or REGION.get(rec.get("s")) or prev.get("r")
        rec["lat"] = l["lat"] if l["lat"] is not None else prev.get("lat")
        rec["lng"] = l["lng"] if l["lng"] is not None else prev.get("lng")
        rec["p"] = sc.get("p") or prev.get("p")
        rec["u"] = l["u"] or prev.get("u")
        rec["y"] = l["y"] or prev.get("y")
        rec["m"] = prev.get("m") or (nearest_metro(rec["lat"], rec["lng"]) if rec.get("lat") else None)
        rec["coming_soon"] = sc.get("coming_soon", prev.get("coming_soon", False))
        rec["email"] = sc.get("email") or prev.get("email")
        rec["hours"] = sc.get("hours") or prev.get("hours")
        rec["instagram"] = sc.get("instagram") or prev.get("instagram")
        rec["facebook"] = sc.get("facebook") or prev.get("facebook")
        if not rec.get("place_id"): rec["place_id"] = l.get("place_id")
        out.append(rec)

    json.dump(out, open(ENRICHED, "w"), separators=(",", ":"))
    new = [l["n"] for l in out if l["n"] not in by_name]
    gone = [n for n in by_name if n not in {l["n"] for l in out}]
    print(f"scraped {len(out)} locations | new: {len(new)} | dropped: {len(gone)}")
    if new:  print("  NEW:", ", ".join(new))
    if gone: print("  DROPPED:", ", ".join(gone))

if __name__ == "__main__":
    main()
