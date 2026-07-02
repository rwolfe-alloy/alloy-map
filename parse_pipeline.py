#!/usr/bin/env python3
"""
Parse FDD Item 20 Table 5 ("Projected Openings") → alloy_pipeline.json:
signed-but-unopened franchise agreements and projected next-FY openings, by state.

Locates the table dynamically (header → "Total" row) so it survives page shifts.
Usage: python3 parse_pipeline.py [fdd.pdf]   (default: alloy_fdd_2026.pdf)
"""
import pdfplumber, re, json, sys

PDF = sys.argv[1] if len(sys.argv) > 1 else "alloy_fdd_2026.pdf"
NAME2ABBR = {"Alabama":"AL","Alaska":"AK","Arizona":"AZ","Arkansas":"AR","California":"CA",
"Colorado":"CO","Connecticut":"CT","Delaware":"DE","Florida":"FL","Georgia":"GA","Hawaii":"HI",
"Idaho":"ID","Illinois":"IL","Indiana":"IN","Iowa":"IA","Kansas":"KS","Kentucky":"KY",
"Louisiana":"LA","Maine":"ME","Maryland":"MD","Massachusetts":"MA","Michigan":"MI",
"Minnesota":"MN","Mississippi":"MS","Missouri":"MO","Montana":"MT","Nebraska":"NE","Nevada":"NV",
"New Hampshire":"NH","New Jersey":"NJ","New Mexico":"NM","New York":"NY","North Carolina":"NC",
"North Dakota":"ND","Ohio":"OH","Oklahoma":"OK","Oregon":"OR","Pennsylvania":"PA",
"Rhode Island":"RI","South Carolina":"SC","South Dakota":"SD","Tennessee":"TN","Texas":"TX",
"Utah":"UT","Vermont":"VT","Virginia":"VA","Washington":"WA","West Virginia":"WV",
"Wisconsin":"WI","Wyoming":"WY","District of Columbia":"DC"}

pdf = pdfplumber.open(PDF)
start = next((i for i, pg in enumerate(pdf.pages)
              if "Projected Openings" in (pg.extract_text() or "")
              and "Table No. 5" in (pg.extract_text() or "")), None)
if start is None:
    sys.exit("!! Table 5 (Projected Openings) not found")

as_of = None
states, total = {}, None
num = lambda s: 0 if s == "?" else int(s)   # "?" = franchisor unsure; count as 0 projected
row_re = re.compile(r"^([A-Z][A-Za-z ]+?)\s+(\d+|\?)\s+(\d+|\?)\s+(\d+|\?)$")

for p in range(start, min(start + 3, len(pdf.pages))):
    for line in (pdf.pages[p].extract_text() or "").split("\n"):
        line = line.strip()
        m = re.search(r"Projected Openings as of (.+)$", line)
        if m: as_of = m.group(1).strip()
        r = row_re.match(line)
        if not r: continue
        name = r.group(1).strip()
        if name == "Total":
            total = {"signed": num(r.group(2)), "projected": num(r.group(3))}
        elif name in NAME2ABBR:
            signed, proj = num(r.group(2)), num(r.group(3))
            if signed or proj:
                states[NAME2ABBR[name]] = {"signed": signed, "projected": proj}
    if total: break

if not states:
    sys.exit("!! No state rows parsed from Table 5")

# cross-check the franchisor's Total row against our row sum
sum_signed = sum(v["signed"] for v in states.values())
if total and total["signed"] != sum_signed:
    print(f"WARN: parsed signed sum {sum_signed} != Total row {total['signed']}")

out = {"source": "Alloy FDD Item 20, Table 5 (Projected Openings)",
       "as_of": as_of, "states": states,
       "total_signed": total["signed"] if total else sum_signed,
       "total_projected": total["projected"] if total else sum(v["projected"] for v in states.values())}
json.dump(out, open("alloy_pipeline.json", "w"), separators=(",", ":"))
print(f"pipeline: {out['total_signed']} signed / {out['total_projected']} projected across {len(states)} states (as of {as_of})")
