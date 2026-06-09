#!/usr/bin/env python3
"""
Parse Exhibit D (LIST OF FRANCHISEES, as of 2025-12-31) from the Alloy 2026 FDD
into structured franchisee records. Input: _exhibitD.txt (column-aware text dump).

Each entry is delimited by its "Phone" line. We classify the other lines of the
block into: entity (legal LLC/Inc), facility ("APT <name>"), street, city/state/zip,
owner (person name), email, phone, state header.
"""
import re, json

STATES = {"ALABAMA","ALASKA","ARIZONA","ARKANSAS","CALIFORNIA","COLORADO","CONNECTICUT",
"DELAWARE","FLORIDA","GEORGIA","HAWAII","IDAHO","ILLINOIS","INDIANA","IOWA","KANSAS",
"KENTUCKY","LOUISIANA","MAINE","MARYLAND","MASSACHUSETTS","MICHIGAN","MINNESOTA",
"MISSISSIPPI","MISSOURI","MONTANA","NEBRASKA","NEVADA","NEW HAMPSHIRE","NEW JERSEY",
"NEW MEXICO","NEW YORK","NORTH CAROLINA","NORTH DAKOTA","OHIO","OKLAHOMA","OREGON",
"PENNSYLVANIA","RHODE ISLAND","SOUTH CAROLINA","SOUTH DAKOTA","TENNESSEE","TEXAS",
"UTAH","VERMONT","VIRGINIA","WASHINGTON","WEST VIRGINIA","WISCONSIN","WYOMING"}
ABBR = {"AL":"AL","AK":"AK","AZ":"AZ","AR":"AR","CA":"CA","CO":"CO","CT":"CT","DE":"DE",
"FL":"FL","GA":"GA","HI":"HI","ID":"ID","IL":"IL","IN":"IN","IA":"IA","KS":"KS","KY":"KY",
"LA":"LA","ME":"ME","MD":"MD","MA":"MA","MI":"MI","MN":"MN","MS":"MS","MO":"MO","MT":"MT",
"NE":"NE","NV":"NV","NH":"NH","NJ":"NJ","NM":"NM","NY":"NY","NC":"NC","ND":"ND","OH":"OH",
"OK":"OK","OR":"OR","PA":"PA","RI":"RI","SC":"SC","SD":"SD","TN":"TN","TX":"TX","UT":"UT",
"VT":"VT","VA":"VA","WA":"WA","WV":"WV","WI":"WI","WY":"WY"}

ENTITY_RE = re.compile(r"\b(LLC|L\.L\.C|Inc\.?|Incorporated|Corp\.?|Corporation|Company|Co\.|Ltd|Industries|Holdings|Ventures|Enterprises?|Group|Partners|Investments?|Fitness|Wellness)\b", re.I)
CITYSTATEZIP_RE = re.compile(r",?\s*([A-Z]{2})\.?\s+(\d{5})(?:-\d{4})?\b")
PERSON_RE = re.compile(r"^[A-Z][a-zA-Z'’.\-]+(?:\s+(?:and\s+)?[A-Z][a-zA-Z'’.\-]+){1,3}$")
NONNAME = re.compile(r"\b(OPERATIONAL|TBD|CLOSED|COMING|LOCATION|PENDING|N/?A)\b", re.I)

def is_person(l):
    if not PERSON_RE.match(l): return False
    if l.startswith(("APT", "ATP")): return False
    if l.isupper() and " " in l: return False   # e.g. "YET OPERATIONAL"
    if NONNAME.search(l): return False
    if ENTITY_RE.search(l): return False
    return True
FOOTER_RE = re.compile(r"^(Alloy\b|DMS_US|Exhibit D|LIST OF|\(as of|Disclosure Document|\d+, 20\d\d\))", re.I)

def clean(s): return re.sub(r"\s+", " ", s).strip()

lines = [l.rstrip() for l in open("_exhibitD.txt") if not l.startswith("@@@")]

entries = []
cur = []
state = None
for raw in lines:
    line = clean(raw).lstrip("*").strip()   # drop footnote-marker asterisks
    if not line: continue
    if FOOTER_RE.match(line): continue
    up = line.upper().rstrip(".")
    if up in STATES:            # state header
        state = up
        continue
    cur.append(line)
    if re.match(r"^Phone", line, re.I):     # entry ends at phone
        entries.append((state, cur)); cur = []
if cur: entries.append((state, cur))

# Map full state name -> abbr
NAME2ABBR = {"ALABAMA":"AL","ALASKA":"AK","ARIZONA":"AZ","ARKANSAS":"AR","CALIFORNIA":"CA",
"COLORADO":"CO","CONNECTICUT":"CT","DELAWARE":"DE","FLORIDA":"FL","GEORGIA":"GA","HAWAII":"HI",
"IDAHO":"ID","ILLINOIS":"IL","INDIANA":"IN","IOWA":"IA","KANSAS":"KS","KENTUCKY":"KY",
"LOUISIANA":"LA","MAINE":"ME","MARYLAND":"MD","MASSACHUSETTS":"MA","MICHIGAN":"MI",
"MINNESOTA":"MN","MISSISSIPPI":"MS","MISSOURI":"MO","MONTANA":"MT","NEBRASKA":"NE","NEVADA":"NV",
"NEW HAMPSHIRE":"NH","NEW JERSEY":"NJ","NEW MEXICO":"NM","NEW YORK":"NY","NORTH CAROLINA":"NC",
"NORTH DAKOTA":"ND","OHIO":"OH","OKLAHOMA":"OK","OREGON":"OR","PENNSYLVANIA":"PA",
"RHODE ISLAND":"RI","SOUTH CAROLINA":"SC","SOUTH DAKOTA":"SD","TENNESSEE":"TN","TEXAS":"TX",
"UTAH":"UT","VERMONT":"VT","VIRGINIA":"VA","WASHINGTON":"WA","WEST VIRGINIA":"WV",
"WISCONSIN":"WI","WYOMING":"WY"}

def parse_entry(state, block):
    rec = {"state": NAME2ABBR.get(state), "entity": None, "facility": None,
           "owner": None, "email": None, "phone": None, "street": None, "city": None, "zip": None}
    email_idx = None
    for i, l in enumerate(block):
        if rec["email"] is None and re.match(r"^Email", l, re.I):
            m = re.search(r"[\w.\-]+@[\w.\-]+", l)
            if m: rec["email"] = m.group(0).lower().replace("trainning","training").replace("alloy.personaltraining","alloypersonaltraining"); email_idx = i
        elif re.match(r"^Phone", l, re.I):
            m = re.search(r"[\d().\-\s]{7,}", l); rec["phone"] = clean(m.group(0)) if m else None
        elif l.startswith(("APT ", "ATP ")) and not rec["facility"]:
            rec["facility"] = l
        else:
            csz = CITYSTATEZIP_RE.search(l)
            if csz and not rec["zip"]:
                rec["zip"] = csz.group(2); rec["city"] = clean(l[:csz.start()]).rstrip(",")
            elif re.match(r"^\*?\d+\s", l) or re.search(r"\b(Rd|Road|St|Street|Ave|Avenue|Blvd|Pkwy|Pkw|Hwy|Highway|Dr|Drive|Ln|Lane|Way|Ct|Court|Suite|Ste|Unit|Sq|Square|Place|Pl|Circle|Cir|Route|Rte)\b", l, re.I) and not rec["street"]:
                rec["street"] = l.lstrip("*").strip()
    # entity = first line with an entity keyword (strip leading *)
    for l in block:
        if ENTITY_RE.search(l) and not l.startswith(("APT","ATP")):
            rec["entity"] = l.lstrip("*").strip(); break
    # owner = person-name line just before Email; else any person-name line
    cand = None
    if email_idx is not None:
        for j in range(email_idx-1, -1, -1):
            if is_person(block[j]):
                cand = block[j]; break
    if not cand:
        for l in block:
            if is_person(l):
                cand = l; break
    rec["owner"] = cand
    return rec

recs = [parse_entry(s, b) for s, b in entries if b]
json.dump(recs, open("_fdd_franchisees.json", "w"), indent=1)

with_email = sum(1 for r in recs if r["email"])
with_owner = sum(1 for r in recs if r["owner"])
with_addr  = sum(1 for r in recs if r["zip"])
print(f"entries: {len(recs)} | email:{with_email} owner:{with_owner} addr:{with_addr}")
print("\nsample:")
for r in recs[:6]:
    print(" ", {k:r[k] for k in ("entity","facility","owner","email","zip")})
