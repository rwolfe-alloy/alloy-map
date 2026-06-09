#!/usr/bin/env python3
"""
Phase 6 — extract Alloy Personal Training 7(a) loans from the SBA FOIA CSV
(_sba_7a.csv, FY2020-present) and match each to a location.

Franchise code S4826 ("Alloy Personal Traning" — SBA's typo).
Output: alloy_sba_loans.json — one record per loan, with `loc` = matched
location name (or null). Aggregates are computed in the frontend from this list.
"""
import csv, json, re

FIELDS = ["borrname","borrcity","borrstate","borrzip","bankname","grossapproval",
          "sbaguaranteedapproval","approvaldate","approvalfy","terminmonths",
          "initialinterestrate","jobssupported","loanstatus","businessage"]

loans = []
with open("_sba_7a.csv", newline="") as f:
    for row in csv.DictReader(f):
        if "alloy personal" in (row.get("franchisename") or "").lower():
            loans.append({k: (row.get(k) or "").strip() for k in FIELDS})

locs = json.load(open("alloy_enriched.json"))
def norm(s): return re.sub(r"[^a-z0-9]", "", (s or "").lower())
def zip5(s):
    z = re.findall(r"\b\d{5}\b", s or ""); return z[-1] if z else None

# indexes
zip_to_locs = {}
ent_to_locs = {}
for l in locs:
    z = zip5(l["a"])
    if z: zip_to_locs.setdefault(z, []).append(l["n"])
    if l.get("franchisee"): ent_to_locs.setdefault(norm(l["franchisee"]), []).append(l["n"])

def match_loan(ln):
    bz = (ln["borrzip"] or "")[:5]
    zc = zip_to_locs.get(bz, [])
    ec = ent_to_locs.get(norm(ln["borrname"]), [])
    inter = [n for n in ec if n in zc]
    if inter: return inter[0]
    if len(zc) == 1: return zc[0]
    if len(ec) == 1: return ec[0]
    if zc: return sorted(zc)[0]
    if ec: return sorted(ec)[0]
    return None

for ln in loans:
    ln["amount"] = int(ln["grossapproval"] or 0)
    ln["loc"] = match_loan(ln)

json.dump(loans, open("alloy_sba_loans.json", "w"), separators=(",", ":"))

matched = [l for l in loans if l["loc"]]
locs_funded = {l["loc"] for l in matched}
total = sum(l["amount"] for l in loans)
print(f"loans: {len(loans)} | matched to a location: {len(matched)} | distinct funded locations: {len(locs_funded)}")
print(f"total SBA 7(a) capital: ${total:,}")
print(f"avg loan: ${total//len(loans):,} | median term: see UI")
from collections import Counter
banks = Counter(l["bankname"] for l in loans)
print("top lenders:", banks.most_common(5))
fy = Counter(l["approvalfy"] for l in loans)
print("by FY:", sorted(fy.items()))
jobs = sum(int(l["jobssupported"] or 0) for l in loans)
print(f"jobs supported: {jobs}")
