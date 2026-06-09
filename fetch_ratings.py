#!/usr/bin/env python3
"""
Phase 4 — fetch Google Places star ratings + review counts for every Alloy location.

Usage:
    python3 fetch_ratings.py                 # reads key from .apikey file or $GOOGLE_PLACES_API_KEY
    python3 fetch_ratings.py AIzaSy...        # key as arg

Notes:
  - Uses the **Places API (New)** Text Search endpoint (POST places:searchText).
    The legacy Find Place endpoint is not enabled on this project.
  - Uses `curl` via subprocess because urllib fails SSL verification on this machine.
  - Strategy: text query "Alloy Personal Training {address}" — robust for all 169,
    independent of the base64 proto placeId tokens on the locations page.
  - Writes back into alloy_enriched.json:
        rating        float | None   (None when no live Google listing, e.g. coming-soon)
        review_count  int   | None
        place_id      str            (canonical ChIJ… id, overwrites the proto token when found)
  - Idempotent; safe to interrupt (writes at the end).
"""
import json, sys, os, subprocess, time

ENRICHED = "alloy_enriched.json"
URL = "https://places.googleapis.com/v1/places:searchText"
FIELD_MASK = "places.rating,places.userRatingCount,places.id,places.displayName,places.formattedAddress"


def get_key():
    if len(sys.argv) > 1 and sys.argv[1].strip():
        return sys.argv[1].strip()
    if os.path.exists(".apikey"):
        return open(".apikey").read().strip()
    k = os.environ.get("GOOGLE_PLACES_API_KEY", "").strip()
    if k:
        return k
    sys.exit("No API key. Pass as arg, put in .apikey, or set GOOGLE_PLACES_API_KEY.")


def search(query, key):
    body = json.dumps({"textQuery": query})
    # curl timeouts + a subprocess backstop so one hung request can't stall the
    # whole (possibly unattended) run; retry once on timeout/transient failure.
    cmd = ["curl", "-s", "--connect-timeout", "15", "--max-time", "45",
        "-X", "POST", URL,
        "-H", "Content-Type: application/json",
        "-H", f"X-Goog-Api-Key: {key}",
        "-H", f"X-Goog-FieldMask: {FIELD_MASK}",
        "-d", body]
    for attempt in range(2):
        try:
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=60).stdout
        except subprocess.TimeoutExpired:
            continue
        try:
            return json.loads(out)
        except json.JSONDecodeError:
            if attempt == 0:
                continue
            return {"_parse_error": out[:200]}
    return {"_parse_error": "timeout"}


def main():
    key = get_key()
    enr = json.load(open(ENRICHED))
    n = len(enr)
    got = 0
    for i, loc in enumerate(enr, 1):
        data = search(f"Alloy Personal Training {loc['a']}", key)

        if "error" in data:
            print(f"\n!! API error: {data['error'].get('status')} — {data['error'].get('message','')[:140]}")
            print("   Stopping early; nothing further fetched.")
            break
        if "_parse_error" in data:
            print(f"\n!! Unparseable response: {data['_parse_error']}")
            break

        places = data.get("places", [])
        if places:
            p = places[0]
            loc["rating"] = p.get("rating")
            loc["review_count"] = p.get("userRatingCount")
            if p.get("id"):
                loc["place_id"] = p["id"]
            got += 1
            r = loc["rating"]
            flag = f"{r}★ ({loc['review_count']})" if r is not None else "[listing, no rating]"
        else:
            loc["rating"] = None
            loc["review_count"] = None
            flag = "[no match]"

        print(f"  {i:3}/{n}  {loc['n']:<34} {flag}")
        time.sleep(0.05)

    json.dump(enr, open(ENRICHED, "w"), separators=(",", ":"))
    rated = sum(1 for l in enr if l.get("rating") is not None)
    print(f"\nDone. {got}/{n} matched a listing, {rated} have a numeric rating. Saved to {ENRICHED}.")


if __name__ == "__main__":
    main()
