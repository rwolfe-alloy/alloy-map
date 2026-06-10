#!/usr/bin/env python3
"""
Parse network churn from the Alloy FDD: Item 20 outlet-status tables (system
openings/closures by year) and Exhibit E (franchisees who left the system).
Output: alloy_churn.json.

Best-effort; locates sections dynamically. Used by the annual fdd refresh.

Usage: python3 parse_churn.py [fdd.pdf]   (default: alloy_fdd_2026.pdf)
"""
import pdfplumber, re, json, sys

PDF = sys.argv[1] if len(sys.argv) > 1 else "alloy_fdd_2026.pdf"
pdf = pdfplumber.open(PDF)
pages = [pg.extract_text() or "" for pg in pdf.pages]

# ── Item 20 Table 3 totals: year start opened terminations non-renewals ceased reacquired end ──
systemwide = []
alltext = "\n".join(pages)
m = re.search(r"Total\*?\*?\s+(20\d\d(?:\s+\d+){7}(?:\s+20\d\d(?:\s+\d+){7})*)", alltext)
if m:
    for row in re.finditer(r"(20\d\d)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)", m.group(1)):
        y, start, opened, term, nonren, ceased, reacq, end = map(int, row.groups())
        systemwide.append({"year": y, "start": start, "opened": opened,
                           "closed": term + nonren + ceased, "reacquired": reacq, "end": end})

# ── Exhibit E: franchisees who left ──
def col_lines(pg, lo, hi):
    ws = [w for w in pg.extract_words() if lo <= w["x0"] < hi]
    ws.sort(key=lambda w: (round(w["top"] / 3), w["x0"]))
    out, cur, cy = [], [], None
    for w in ws:
        if cy is None or abs(w["top"] - cy) <= 3:
            cur.append(w); cy = cy or w["top"]
        else:
            out.append(" ".join(x["text"] for x in cur)); cur, cy = [w], w["top"]
    if cur: out.append(" ".join(x["text"] for x in cur))
    return out

# find Exhibit E page range
e_start = next((i for i, t in enumerate(pages) if "Exhibit E" in t and "LEFT THE SYSTEM" in t), None)
departed = []
if e_start is not None:
    e_end = next((i for i in range(e_start + 1, len(pages)) if re.search(r"Exhibit F\b", pages[i])), e_start + 3)
    never_open = False
    for p in range(e_start, e_end):
        # the "...NEVER OPENING AN OUTLET" header is full-width (splits across columns),
        # so flag by page: every entry from that page on is a never-opened termination
        if re.search(r"DUE TO NEVER", pages[p], re.I):   # header of the never-opened sub-list
            never_open = True
        pg = pdf.pages[p]
        lines = col_lines(pg, 0, pg.width / 2) + col_lines(pg, pg.width / 2, pg.width)
        cur_fac = None
        for ln in lines:
            fac = re.match(r"(APT|ATP)\b.*", ln)
            if fac:
                cur_fac = ln.strip()
            rm = re.match(r"Reason:\s*(.+)", ln, re.I)
            if rm and cur_fac:
                departed.append({"facility": cur_fac, "reason": rm.group(1).strip(), "never_opened": never_open})
                cur_fac = None

# de-dupe (the two-column flow occasionally repeats an entry)
seen, uniq = set(), []
for d in departed:
    k = (d["facility"], d["reason"], d["never_opened"])
    if k not in seen:
        seen.add(k); uniq.append(d)

out = {
    "source": "Alloy 2026 FDD — Item 20 (Outlets) + Exhibit E (franchisees who left)",
    "as_of": "2025-12-31",
    "systemwide": systemwide,
    "departed": uniq,
}
json.dump(out, open("alloy_churn.json", "w"), indent=1)

closed = sum(s["closed"] for s in systemwide)
opened = sum(s["opened"] for s in systemwide)
left = sum(1 for d in uniq if not d["never_opened"])
neveropen = sum(1 for d in uniq if d["never_opened"])
print(f"systemwide: {len(systemwide)} yrs, {opened} opened / {closed} closed | "
      f"departed: {left} left ({neveropen} never opened)")
