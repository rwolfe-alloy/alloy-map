#!/usr/bin/env python3
"""
Data validation gate — runs in refresh.sh after all data steps and BEFORE the
commit/push, so a parser regression or upstream format change can never deploy
bad data. Exits non-zero with a list of failures; any failure aborts the push.

Checks are deliberately loose bounds (the network will grow) — they catch
structural breakage, not ordinary drift.

Usage: python3 validate.py
"""
import json, os, sys

errors = []
def check(cond, msg):
    if not cond:
        errors.append(msg)

# ── locations ──
locs = json.load(open("alloy_enriched.json"))
check(120 <= len(locs) <= 400, f"location count {len(locs)} outside sane range 120–400")
names = [l.get("n") for l in locs]
check(len(names) == len(set(names)), "duplicate location names")
for l in locs:
    n = l.get("n", "?")
    check(all(l.get(k) for k in ("n", "a", "s")), f"{n}: missing name/address/state")
    lat, lng = l.get("lat"), l.get("lng")
    check(lat is not None and 18 < lat < 72, f"{n}: lat {lat} outside US bounds")
    check(lng is not None and -180 < lng < -60, f"{n}: lng {lng} outside US bounds")
    r = l.get("rating")
    check(r is None or 1 <= r <= 5, f"{n}: rating {r} out of range")
    rc = l.get("review_count")
    check(rc is None or 0 <= rc < 100000, f"{n}: review_count {rc} out of range")
rated = sum(1 for l in locs if l.get("rating") is not None)
check(rated >= 0.5 * len(locs), f"only {rated}/{len(locs)} rated — ratings pipeline likely broke")
owners = sum(1 for l in locs if l.get("owner") or l.get("franchisee"))
check(owners >= 0.5 * len(locs), f"only {owners}/{len(locs)} with operator — FDD match likely broke")

# ── SBA loans ──
if os.path.exists("alloy_sba_loans.json"):
    loans = json.load(open("alloy_sba_loans.json"))
    check(50 <= len(loans) <= 2000, f"SBA loan count {len(loans)} outside 50–2000")
    for ln in loans:
        check(1000 <= ln.get("amount", 0) <= 5_000_000,
              f"loan {ln.get('borrname','?')}: amount {ln.get('amount')} out of range")
    matched = sum(1 for ln in loans if ln.get("loc"))
    check(matched >= 0.5 * len(loans), f"only {matched}/{len(loans)} loans matched a location")

# ── Item 19 ──
if os.path.exists("alloy_item19.json"):
    i19 = json.load(open("alloy_item19.json"))
    auv = i19.get("system_auv")
    check(auv and 100_000 <= auv <= 1_500_000, f"system AUV {auv} outside $100K–$1.5M")
    ret = i19.get("avg_monthly_retention_pct")
    check(ret is None or 50 <= ret <= 100, f"retention {ret}% out of range")
    q = i19.get("revenue_by_quartile", {})
    q1, q4 = (q.get("First Quartile") or {}).get("avg"), (q.get("Fourth Quartile") or {}).get("avg")
    check(not (q1 and q4) or q1 > q4, f"quartile ordering broken (Q1 {q1} <= Q4 {q4})")

# ── churn ──
if os.path.exists("alloy_churn.json"):
    ch = json.load(open("alloy_churn.json"))
    sw = ch.get("systemwide", [])
    check(len(sw) >= 2, f"churn systemwide has {len(sw)} year(s) — parse likely broke")
    for y in sw:
        check(y.get("end", 0) > 0 and y.get("opened", 0) >= y.get("closed", 0),
              f"churn year {y.get('year')}: implausible open/close ({y})")

# ── trends ──
if os.path.exists("alloy_trends.json"):
    tr = json.load(open("alloy_trends.json"))
    net = tr.get("network", [])
    if net:
        dates = [s["d"] for s in net]
        check(dates == sorted(dates), "trend snapshots out of order")
        check(all(s.get("total", 0) > 0 for s in net), "trend snapshot with zero locations")

if errors:
    print(f"VALIDATION FAILED — {len(errors)} problem(s):")
    for e in errors[:25]:
        print("  ✗", e)
    sys.exit(1)
print(f"validation OK — {len(locs)} locations, {rated} rated, {owners} with operator")
