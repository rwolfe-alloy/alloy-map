#!/usr/bin/env python3
"""
Theme 4 — extract benchmark metrics from each peer FDD (+ Alloy's own):

  - Item 20 Table 1 (Systemwide Outlet Summary): outlets by year  [FTC-standardized]
  - Item 20 Table 3 totals: opened/closed → 3-yr survival         [FTC-standardized]
  - Item 5: initial franchise fee
  - Item 6/7: royalty %, estimated initial investment range
  - Item 19: candidate average-revenue lines (printed with page numbers for
    curation — formats vary too much across brands to trust blind parsing)

Writes alloy_benchmarks.json (auv fields left null where curation is needed).
Usage: python3 parse_benchmarks.py
"""
import pdfplumber, re, json, os

PDFS = [
    ("alloy", "Alloy Personal Training", "alloy_fdd_2026.pdf"),
    ("otf", "Orangetheory", "_fdd_peer_otf.pdf"),
    ("f45", "F45 Training", "_fdd_peer_f45.pdf"),
    ("sl", "StretchLab", "_fdd_peer_sl.pdf"),
    ("cp", "Club Pilates", "_fdd_peer_cp.pdf"),
    ("ec", "The Exercise Coach", "_fdd_peer_ec.pdf"),
    ("ft", "Fitness Together", "_fdd_peer_ft.pdf"),
]

num = lambda s: int(s.replace(",", "")) if s else None

def extract(key, name, path):
    if not os.path.exists(path):
        return None
    pdf = pdfplumber.open(path)
    pages = [pg.extract_text() or "" for pg in pdf.pages]
    text = "\n".join(pages)
    out = {"name": name, "pages": len(pages)}

    # ── Item 20 Table 1: Systemwide Outlet Summary ──
    i = text.find("Systemwide Outlet Summary")
    seg = text[i:i+2500] if i >= 0 else ""
    rows = re.findall(r"(Franchised|Total Outlets)\s+(20\d\d)\s+([\d,]+)\s+([\d,]+)\s+([+-]?[\d,]+)", seg)
    fr = {int(y): num(end) for kind, y, start, end, net in rows if kind == "Franchised"}
    if fr:
        out["franchised_by_year"] = fr
        yrs = sorted(fr)
        out["units"] = fr[yrs[-1]]
        out["units_3yr_ago"] = fr[yrs[0]]
        out["growth_3yr_pct"] = round((fr[yrs[-1]] / max(fr[yrs[0]], 1) - 1) * 100, 1)

    # ── Item 20 Table 3 totals: opened/terminations/... per year ──
    m = re.search(r"Total[s\*]*\s+(20\d\d(?:\s+[\d,]+){7}(?:\s+20\d\d(?:\s+[\d,]+){7}){0,2})", text)
    if m:
        opened = closed = 0
        for r in re.finditer(r"(20\d\d)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)", m.group(1)):
            y, start, op, term, nonren, ceased, reacq, end = r.groups()
            opened += num(op); closed += num(term) + num(nonren) + num(ceased)
        out["opened_3yr"] = opened
        out["closed_3yr"] = closed
        out["survival_3yr_pct"] = round((opened - closed) / opened * 100, 1) if opened else None

    # ── Item 5: initial franchise fee ──
    m = re.search(r"[Ii]nitial [Ff]ranchise [Ff]ee[^.$]{0,120}?\$([\d,]{4,8})", text)
    if m: out["franchise_fee"] = num(m.group(1))

    # ── Item 6: royalty ──
    m = re.search(r"Royalty[^%$\n]{0,200}?([\d.]{1,4})\s*%", text)
    if m:
        try: out["royalty_pct"] = float(m.group(1))
        except ValueError: pass

    # ── Item 7: estimated initial investment total range ──
    for pat in [r"(?:Total(?:s)?(?:\s+Estimated)?(?:\s+Initial)?(?:\s+Investment)?)[^\d$\n]{0,60}\$\s?([\d,]{6,10})\s*(?:to|[-–])\s*\$\s?([\d,]{6,10})",
                r"total (?:estimated )?initial investment[^$]{0,200}\$\s?([\d,]{6,10})\s*(?:to|[-–])\s*\$\s?([\d,]{6,10})"]:
        m = re.search(pat, text, re.I)
        if m and num(m.group(1)) > 50000:
            out["invest_low"], out["invest_high"] = num(m.group(1)), num(m.group(2))
            break

    # ── Item 19 AUV candidates (for curation) ──
    i19 = None
    for p, t in enumerate(pages):
        if re.search(r"ITEM 19", t) and "FINANCIAL PERFORMANCE" in t and "TABLE OF CONTENTS" not in t:
            i19 = p; break
    cands = []
    if i19 is not None:
        for p in range(i19, min(i19 + 12, len(pages))):
            for ln in pages[p].split("\n"):
                if re.search(r"[Aa]verage|[Mm]ean|AUV", ln) and re.search(r"\$?[\d,]{6,}", ln):
                    cands.append(f"p{p}: {ln.strip()[:110]}")
    out["_auv_candidates"] = cands[:12]
    out["auv"] = None
    return out

result = {}
for key, name, path in PDFS:
    r = extract(key, name, path)
    if r is None:
        print(f"{key}: MISSING {path}"); continue
    result[key] = r
    print(f"=== {name} ({r['pages']}pp) ===")
    print(f"  units:{r.get('units')} (3yr ago {r.get('units_3yr_ago')}, +{r.get('growth_3yr_pct')}%) | "
          f"opened:{r.get('opened_3yr')} closed:{r.get('closed_3yr')} survival:{r.get('survival_3yr_pct')}%")
    print(f"  fee:${r.get('franchise_fee')} royalty:{r.get('royalty_pct')}% invest:${r.get('invest_low')}–${r.get('invest_high')}")
    for c in r["_auv_candidates"][:5]:
        print("   AUV?", c)

json.dump(result, open("alloy_benchmarks.json", "w"), indent=1)
print("\nwrote alloy_benchmarks.json (curate 'auv' fields from candidates above)")
