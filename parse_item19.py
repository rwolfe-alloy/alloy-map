#!/usr/bin/env python3
"""
Parse Item 19 (Financial Performance Representations) from the Alloy FDD into
alloy_item19.json: 2025 revenue by quartile and by maturity cohort, plus average
memberships, revenue/member, and retention.

Locates Item 19 dynamically (heading → next ITEM), so it survives page shifts.
Best-effort: writes what it can find; the annual fdd refresh logs failures.

Usage: python3 parse_item19.py [fdd.pdf]   (default: alloy_fdd_2026.pdf)
"""
import pdfplumber, re, json, sys

PDF = sys.argv[1] if len(sys.argv) > 1 else "alloy_fdd_2026.pdf"
pdf = pdfplumber.open(PDF)

# find Item 19 page range (skip the table of contents)
start = end = None
for i, pg in enumerate(pdf.pages):
    t = pg.extract_text() or ""
    if start is None and re.search(r"ITEM 19\b", t) and "FINANCIAL PERFORMANCE" in t and "TABLE OF CONTENTS" not in t:
        start = i
    elif start is not None and i > start and re.search(r"\bITEM 20\b", t) and "TABLE OF CONTENTS" not in t:
        end = i; break
if start is None:
    sys.exit("!! Item 19 not found")
end = end or min(start + 8, len(pdf.pages))

num = lambda s: int(re.sub(r"[^\d]", "", s)) if s and re.search(r"\d", s) else None

# Revenue cohorts from the Part-1 tables (quartile + opening-date)
cohorts = {}      # label -> {avg,max,min,median, count}
cur = None
for p in range(start, end + 1):
    for tbl in (pdf.pages[p].extract_tables() or []):
        for row in tbl:
            cells = [c.replace("\n", " ").strip() if c else "" for c in row]
            label = cells[0]
            m = re.match(r"(First|Second|Third|Fourth) Quartile|Open [\d+\-]+ Months", label)
            lm = re.search(r"\((\d+) locations?\)", label)
            if m:
                cur = re.sub(r"\s*\(\d+ locations?\)", "", label).strip()
                cohorts[cur] = {"count": num(lm.group(1)) if lm else None}
            if cur and len(cells) >= 3:
                key = cells[1].lower()
                # take only the first number — the average cell trails "(with N exceeding the average)"
                first = re.search(r"[\d,]+", cells[2])
                val = num(first.group(0)) if first else None
                if key in ("average", "max", "min", "median") and val:
                    cohorts[cur][{"average": "avg"}.get(key, key)] = val

quartiles = {k: v for k, v in cohorts.items() if "Quartile" in k}
maturity  = {k: v for k, v in cohorts.items() if "Months" in k}

# Parts 2-4 KPIs from text
text = "\n".join(pdf.pages[p].extract_text() or "" for p in range(start, end + 1))
def after(label, n=5):
    m = re.search(label + r".{0,80}?#\s*Exceeding\s*Avg\s*\n([\d.,\s]+)", text, re.S | re.I)
    if not m: return None
    vals = re.findall(r"[\d.,]+", m.group(1))
    return [float(v.replace(",", "")) for v in vals[:n]]

mem = after(r"Active Monthly Memberships")
rpm = after(r"Revenue per Member")
ret = re.search(r"Avg\s+([\d.]+)%", text)

out = {
    "source": "Alloy 2026 FDD, Item 19 (Financial Performance Representations)",
    "period": "2025 Measurement Period (Jan–Dec 2025)",
    "revenue_by_quartile": quartiles,
    "revenue_by_maturity": maturity,
    "avg_monthly_memberships": ({"avg": mem[0], "max": mem[1], "min": mem[2], "median": mem[3]} if mem else None),
    "revenue_per_member": ({"avg": rpm[0], "max": rpm[1], "min": rpm[2], "median": rpm[3]} if rpm else None),
    "avg_monthly_retention_pct": float(ret.group(1)) if ret else None,
}
# system AUV = location-weighted average of quartile averages
qs = [q for q in quartiles.values() if q.get("avg") and q.get("count")]
if qs:
    out["system_auv"] = round(sum(q["avg"] * q["count"] for q in qs) / sum(q["count"] for q in qs))

json.dump(out, open("alloy_item19.json", "w"), indent=1)
print(f"Item 19 (pages {start}-{end}): {len(quartiles)} quartiles, {len(maturity)} maturity cohorts, "
      f"AUV ${out.get('system_auv','?'):,}" if out.get("system_auv") else "parsed")
