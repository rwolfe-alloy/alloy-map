#!/usr/bin/env python3
"""
Match FDD franchisee records (_fdd_franchisees.json) to our 169 locations
(alloy_enriched.json) and attach owner + franchisee entity.

Match signals, in priority order:
  1. email exact (normalized)
  2. zip + street-number
  3. facility-name token overlap with location name
Writes `owner` and `franchisee` onto matched locations.
"""
import json, re

locs = json.load(open("alloy_enriched.json"))
frans = json.load(open("_fdd_franchisees.json"))

def norm_email(e): return (e or "").lower().strip()
def streetno(s):
    m = re.match(r"\s*(\d+)", s or ""); return m.group(1) if m else None
def toks(s):
    return set(re.findall(r"[a-z]+", (s or "").lower())) - {
        "apt","atp","the","at","of","and","ca","az","ga","fl","tx","il","co","nc","oh",
        "wa","mo","mi","mn","nv","ut","tn","sc","md","va","ky","or","in","ar","wi","nj",
        "ne","ok","suite","ste","unit"}

# index franchisees by email and zip
by_email = {norm_email(f["email"]): f for f in frans if f.get("email")}

def best_match(loc):
    # 1. email
    f = by_email.get(norm_email(loc.get("email")))
    if f: return f, "email"
    # 2. zip + street number  (zip = LAST 5-digit group; the first is the street number)
    zips = re.findall(r"\b\d{5}\b", loc["a"]); locz = zips[-1] if zips else None
    locno = streetno(loc["a"])
    if locz:
        for f in frans:
            if f.get("zip") == locz and locno and streetno(f.get("street")) == locno:
                return f, "addr"
    # 3. facility-name token overlap (require >=1 shared distinctive token + state)
    lname = loc["n"].split(",")[0]
    lt = toks(lname)
    best, bestscore = None, 0
    for f in frans:
        if f.get("state") and f["state"] != loc["s"]: continue
        ft = toks(f.get("facility"))
        score = len(lt & ft)
        if score > bestscore:
            best, bestscore = f, score
    if best and bestscore >= 1:
        return best, "facility"
    return None, None

matched = 0
methods = {}
used = set()
for loc in locs:
    f, how = best_match(loc)
    if f:
        loc["owner"] = f.get("owner")
        loc["franchisee"] = f.get("entity")
        matched += 1
        methods[how] = methods.get(how, 0) + 1
        used.add(id(f))
    else:
        loc.pop("owner", None); loc.pop("franchisee", None)

json.dump(locs, open("alloy_enriched.json", "w"), separators=(",", ":"))

with_owner = sum(1 for l in locs if l.get("owner"))
print(f"matched {matched}/{len(locs)} locations  methods={methods}")
print(f"with owner name: {with_owner}")
print(f"franchisee entries used: {len(used)}/{len(frans)}")

# Multi-unit operators (group by owner)
from collections import Counter, defaultdict
owners = defaultdict(list)
for l in locs:
    if l.get("owner"): owners[l["owner"]].append(l["n"])
multi = {o: v for o, v in owners.items() if len(v) > 1}
print(f"\noperators: {len(owners)} total, {len(multi)} multi-unit")
for o, v in sorted(multi.items(), key=lambda x: -len(x[1]))[:15]:
    print(f"  {o} ({len(v)}): {', '.join(v)}")
