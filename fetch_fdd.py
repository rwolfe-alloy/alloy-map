#!/usr/bin/env python3
"""
Download the latest registered Alloy Personal Training FDD from the Wisconsin DFI
Franchise Search, then extract Exhibit D ("LIST OF FRANCHISEES") to _exhibitD.txt
(column-aware) for parse_fdd.py.

The portal is ASP.NET (viewstate POST chain). Page numbers shift year to year, so
Exhibit D is located dynamically (between its "LIST OF FRANCHISEES" header and the
next exhibit). Best-effort: exits non-zero with a clear message if anything changes.

Usage: python3 fetch_fdd.py   ->   alloy_fdd_latest.pdf + _exhibitD.txt
"""
import re, sys, subprocess, urllib.parse, html as htmlmod

BASE = "https://apps.dfi.wi.gov/apps/FranchiseSearch"
COOKIES = "_wi_cookies.txt"

def curl(args):
    return subprocess.run(["curl","-s","-b",COOKIES,"-c",COOKIES]+args,
                          capture_output=True, text=True).stdout

def hidden_fields(html):
    f = {}
    for m in re.finditer(r'<input[^>]*type="hidden"[^>]*>', html):
        n = re.search(r'name="([^"]*)"', m.group(0)); v = re.search(r'value="([^"]*)"', m.group(0))
        if n: f[n.group(1)] = htmlmod.unescape(v.group(1)) if v else ""
    return f

def main():
    # 1. search page → viewstate
    page = curl([f"{BASE}/MainSearch.aspx"])
    fields = hidden_fields(page)
    fields["txtName"] = "Alloy"; fields["btnSearch"] = "(S)earch"
    # 2. POST search → follow redirect to results
    resp = curl(["-X","POST",f"{BASE}/MainSearch.aspx",
                 "-H","Content-Type: application/x-www-form-urlencoded",
                 "--data", urllib.parse.urlencode(fields)])
    redir = re.search(r'href="([^"]+)"', resp)
    if not redir: sys.exit("!! No redirect from search — portal layout changed.")
    results = curl(["-L", "https://apps.dfi.wi.gov"+htmlmod.unescape(redir.group(1))])

    # 3. pick the registered "Alloy Personal Training" filing with the highest id
    cands = []
    for m in re.finditer(r'details\.aspx\?id=(\d+)&(?:amp;)?hash=(\d+)[^"\']*', results):
        seg = results[max(0,m.start()-400):m.end()+200]
        if "Alloy Personal Training" in seg and "Registered" in seg:
            cands.append((int(m.group(1)), m.group(2)))
    if not cands: sys.exit("!! No registered Alloy Personal Training filing found.")
    fid, fhash = max(cands)
    print(f"Filing #{fid} (registered).")

    # 4. detail page → download the FDD PDF
    detail_url = f"{BASE}/details.aspx?id={fid}&hash={fhash}&search=external&type=GENERAL"
    detail = curl(["-L", detail_url])
    df = hidden_fields(detail); df["upload_downloadFile"] = "Download"
    curl(["-L","-X","POST",detail_url,
          "-H","Content-Type: application/x-www-form-urlencoded",
          "--data", urllib.parse.urlencode(df), "-o","alloy_fdd_latest.pdf"])

    # 5. extract Exhibit D (column-aware) — locate dynamically
    import pdfplumber
    pdf = pdfplumber.open("alloy_fdd_latest.pdf")
    start = end = None
    for i, pg in enumerate(pdf.pages):
        t = (pg.extract_text() or "")
        if start is None and "LIST OF FRANCHISEES" in t and "Exhibit" in t and "as of" in t.lower():
            start = i
        elif start is not None and i > start and re.search(r"Exhibit\s+[A-Z]\b", t) and "LIST OF FRANCHISEES" not in t:
            end = i; break
    if start is None: sys.exit("!! Could not locate Exhibit D (LIST OF FRANCHISEES) in the FDD.")
    end = end or min(start+20, len(pdf.pages))
    print(f"Exhibit D: pages {start}-{end-1}")

    def col_text(pg, lo, hi):
        words = [w for w in pg.extract_words() if lo <= w["x0"] < hi]
        words.sort(key=lambda w: (round(w["top"]/3), w["x0"]))
        lines, cur, cy = [], [], None
        for w in words:
            if cy is None or abs(w["top"]-cy) <= 3: cur.append(w); cy = cy or w["top"]
            else: lines.append(" ".join(x["text"] for x in cur)); cur, cy = [w], w["top"]
        if cur: lines.append(" ".join(x["text"] for x in cur))
        return lines

    out = []
    for p in range(start, end):
        pg = pdf.pages[p]
        mid = pg.width/2
        out.append(f"@@@ PAGE {p} LEFT"); out += col_text(pg, 0, mid)
        out.append(f"@@@ PAGE {p} RIGHT"); out += col_text(pg, mid, pg.width)
    open("_exhibitD.txt","w").write("\n".join(out))
    print(f"Wrote _exhibitD.txt ({len(out)} lines).")

if __name__ == "__main__":
    main()
