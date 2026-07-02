#!/usr/bin/env python3
"""
Distill snapshots/ into alloy_trends.json for the dashboard's trending features.

Network series spans ALL snapshots (long-run charts); per-location deltas cover
the LATEST period (last two snapshots), with review velocity normalized to
reviews per 30 days. Gets richer automatically as monthly snapshots accumulate.

Run by refresh.sh after snapshot.py. Needs >=2 snapshots; writes {} otherwise.

Usage: python3 build_trends.py
"""
import json, glob, re
from datetime import date

snaps = sorted(glob.glob("snapshots/alloy_enriched_*.json"))
if len(snaps) < 2:
    json.dump({}, open("alloy_trends.json", "w"))
    raise SystemExit(f"only {len(snaps)} snapshot(s) — trends need 2+; wrote empty alloy_trends.json")

def snap_date(path):
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", path)
    return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))

def load(path):
    return {l["n"]: l for l in json.load(open(path))}

# ── network series across all snapshots ──
network = []
for p in snaps:
    d = load(p)
    rated = [l for l in d.values() if l.get("rating") is not None]
    network.append({
        "d": snap_date(p).isoformat(),
        "total": len(d),
        "live": sum(1 for l in d.values() if not l.get("coming_soon")),
        "rated": len(rated),
        "reviews": sum(l.get("review_count") or 0 for l in d.values()),
        "avg_rating": round(sum(l["rating"] for l in rated) / len(rated), 3) if rated else None,
    })

# ── latest-period per-location deltas ──
prev_p, last_p = snaps[-2], snaps[-1]
prev, last = load(prev_p), load(last_p)
span = max((snap_date(last_p) - snap_date(prev_p)).days, 1)

locs = {}
for n, lb in last.items():
    la = prev.get(n)
    e = {}
    if la is None:
        e["new"] = True
    else:
        ra, rb = la.get("review_count"), lb.get("review_count")
        if ra is not None and rb is not None and ra != rb:
            e["dr"] = rb - ra
            e["vel"] = round((rb - ra) / span * 30, 1)
        if ra is not None and rb is None:
            e["lost_listing"] = True          # Google listing vanished/remapped
        if la.get("rating") is not None and lb.get("rating") is not None and la["rating"] != lb["rating"]:
            e["drat"] = round(lb["rating"] - la["rating"], 1)
        if la.get("coming_soon") and not lb.get("coming_soon"):
            e["went_live"] = True
    if e:
        locs[n] = e

out = {
    "period": {"from": snap_date(prev_p).isoformat(), "to": snap_date(last_p).isoformat(), "days": span},
    "network": network,
    "locations": locs,
}
json.dump(out, open("alloy_trends.json", "w"), separators=(",", ":"))

gainers = sum(1 for e in locs.values() if e.get("dr", 0) > 0)
went = sum(1 for e in locs.values() if e.get("went_live"))
print(f"trends: {len(network)} snapshots, latest period {span}d | "
      f"{len(locs)} locations changed ({gainers} gained reviews, {went} went live)")
