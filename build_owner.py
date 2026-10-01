#!/usr/bin/env python3
"""
Build the Owner Edition (public, owner-safe) from this project's datasets.

Writes sanitized data into the Owner Edition's index.html (a separate repo,
default ../Alloy Owner Map) by swapping its single-line `const X = ...;`
declarations — the same approach as rebuild_index.py.

Only owner-safe fields are embedded. Financing, revenue estimates, Item 19,
departed franchisees, per-studio decline data, demographics/site scores,
whitespace and pipeline projections never reach the Owner Edition — a guard
scans the final page and aborts without writing if any of it appears.

Owners who ask not to be named: list their studio names (e.g. "Middleton, WI")
or owner/entity names in _owner_optout.json (gitignored, local only).

Usage: python3 build_owner.py [owner_repo_dir]
"""
import json, os, re, sys
from datetime import date

OUT_DIR = sys.argv[1] if len(sys.argv) > 1 else os.path.join("..", "Alloy Owner Map")
OUT = os.path.join(OUT_DIR, "index.html")
load = lambda f, d=None: json.load(open(f)) if os.path.exists(f) else d

# ── Studios ──
KEEP = ["n", "a", "s", "r", "lat", "lng", "p", "u", "y", "m", "coming_soon", "email", "hours",
        "instagram", "facebook", "place_id", "rating", "review_count", "owner", "franchisee"]
optout = {s.strip().lower() for s in (load("_owner_optout.json", []) or []) if s.strip()}
locs = []
for l in load("alloy_enriched.json"):
    rec = {k: l.get(k) for k in KEEP}
    names = {(rec["n"] or "").lower(), (rec["owner"] or "").lower(), (rec["franchisee"] or "").lower()}
    if optout & names:
        rec["owner"] = rec["franchisee"] = None
    locs.append(rec)

# ── Momentum: network totals + positive movers only (no per-studio declines) ──
t = load("alloy_trends.json", {}) or {}
trends = {}
if t.get("network"):
    net = t["network"]
    per = t.get("locations", {})
    growers = sorted(((n, e["vel"]) for n, e in per.items() if (e.get("vel") or 0) > 0), key=lambda x: -x[1])[:8]
    trends = {
        "period": {k: t["period"][k] for k in ("from", "to") if k in t.get("period", {})},
        "network": [{"d": s["d"], "live": s["live"]} for s in net],
        "growers": [{"n": n, "vel": v} for n, v in growers],
        "went_live": sum(1 for e in per.values() if e.get("went_live")),
        "gainers": sum(1 for e in per.values() if (e.get("dr") or 0) > 0),
        "new_reviews": max(0, net[-1].get("reviews", 0) - net[-2].get("reviews", 0)) if len(net) > 1 else 0,
    }

# ── Network stability: Item 20 system totals only (no departed franchisee names) ──
c = load("alloy_churn.json", {}) or {}
churn = {"source": "Alloy 2026 FDD, Item 20",
         "systemwide": [{k: y[k] for k in ("year", "start", "opened", "closed", "end")} for y in c.get("systemwide", [])]}

# ── Peer brands: size, growth, survival only (no fees, AUV or Item 19) ──
b = load("alloy_benchmarks.json", {}) or {}
order = ["alloy", "cp", "otf", "sl", "ec", "f45", "ft"]
bench = {"year": 2025, "brands": [
    {"name": b[k]["name"], "units": b[k].get("units"), "growth_3yr_pct": b[k].get("growth_3yr_pct"),
     "survival_3yr_pct": b[k].get("survival_3yr_pct"), "me": k == "alloy"}
    for k in order if k in b]}

# ── Competitors: per-studio totals + studio pins (no metro/whitespace data) ──
cp = load("alloy_competitors.json", {}) or {}
comp = {"brands": cp.get("brands", []), "radius_mi": (cp.get("radius_mi") or {}).get("locations", 5),
        "locations": {n: {"total": v.get("total", 0)} for n, v in (cp.get("locations") or {}).items()},
        "places": cp.get("places", [])}

as_of = trends.get("period", {}).get("to") or date.today().isoformat()
build = {"as_of": as_of, "as_of_label": date.fromisoformat(as_of).strftime("%B %-d, %Y")}

# ── Inject ──
js = lambda o: json.dumps(o, separators=(",", ":"), ensure_ascii=False)
html = open(OUT).read()
for name, val in [("LOCATIONS", locs), ("BUILD", build), ("TRENDS", trends), ("CHURN", churn),
                  ("BENCHMARKS", bench), ("COMPETITORS", comp)]:
    html, n = re.subn(rf"^const {name} = .*?;$", lambda m: f"const {name} = {js(val)};", html, count=1, flags=re.M)
    if n != 1:
        sys.exit(f"!! could not place const {name} in {OUT} — not written")

# ── Guard: nothing sensitive may reach the public page ──
FORBIDDEN = [r"\bSBA\b", r"\bsba", r"\bloan", r"bankname", r"grossapproval", r"acquisition", r"basket", r"roll-?up",
             r"EBITDA", r"valuation", r"Deal Memo", r"estRevenue", r"est\. revenue", r"ITEM19", r"Item 19",
             r"\bAUV\b", r"\bauv", r"royalty", r"franchise_fee", r"invest_(low|high)", r"departed", r"never_opened",
             r"\"facility\"", r"watch ?list", r"lost_listing", r"site quality", r"_sq\b", r"WHITESPACE",
             r"whitespace", r"PIPELINE", r"total_signed", r"projected", r"DEMOG", r"\"inc\"", r"fetch_ratings",
             r"apikey", r"robert\.alan\.wolfe", r"gmail\.com"]
hits = [p for p in FORBIDDEN if re.search(p, html, re.I if p.islower() else 0)]
if hits:
    sys.exit(f"!! Owner Edition guard tripped on {hits} — {OUT} NOT written")
bad = {k for l in locs for k in l} - set(KEEP)
if bad:
    sys.exit(f"!! unexpected studio fields {bad} — not written")

open(OUT, "w").write(html)
named = sum(1 for l in locs if l["owner"] or l["franchisee"])
print(f"Owner Edition built — {len(locs)} studios ({named} with owner names, {len(optout)} opt-outs), "
      f"{len(trends.get('growers', []))} growers, {len(bench['brands'])} peer brands, data as of {as_of}.")
