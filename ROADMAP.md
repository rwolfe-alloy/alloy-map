# Alloy Map — Next Phase Roadmap

Phases 1–6 are complete (map, pipeline, ratings, ownership, SBA financing, unattended refresh).
This is the prioritized backlog for what comes next. The project's north star is **franchise
rollup analysis**, so items are ranked by how much they advance that goal.

Legend — **Impact**: ⭐ high / ◐ medium / ○ nice-to-have · **Effort**: S / M / L

---

## 🚀 "Next-level" theme rollout *(rolling out one theme at a time for review)*

- **Theme 1 — Synthesis & decision layer** ✅ *(Phase 10)* — Executive **Overview tab**: hero KPIs, auto-generated **deal memo**, **Top-Markets** rollup ranking, **acquisition basket** builder, **implied-valuation** lens.
- **Theme 2 — Market intelligence** ✅ *(Phase 12)* — Census ACS demographics (zip + CBSA), competitor density (OTF/F45/StretchLab via Places), **site-quality score** + map layer, **scored Whitespace ranking**, income in Top Markets. *(Drive-time trade areas deferred.)*
- **Theme 3 — Time & trajectory** — growth time-lapse, projected-openings pipeline map (FDD Item 20 Table 5), cohort/ramp analysis. *Partially started (Phase 11): snapshot-based **Trending** — review-velocity leaderboard, momentum map layer, watch list.*
- **Theme 4 — Context & credibility** — peer-franchise benchmarking, franchise economics (FDD Items 5–7), methodology/sources page.
- **Theme 5 — Presentation** — one-click PDF report, dark mode, mobile polish.

---

## 🎯 Flagship: Phase 7 — Acquisition-Target Scoring

The data is all here (units, ratings, capital, tenure, lender) but it's shown in separate tabs.
The next leap is to **synthesize it into a single ranked view of rollup targets**.

| # | Item | Why it matters | Impact | Effort |
|---|---|---|---|---|
| 1 | **Operator "rollup score"** ✅ *(done)* — composite of units × avg rating × SBA capital × tenure; sortable ranked "Acquisition targets" list in the Ownership tab | Turns the map from a data viewer into a deal-sourcing tool | ⭐ | — |
| 2 | **Operator profile / one-pager** ✅ *(done)* — click an operator → modal with units, ratings, reviews, capital, loans, lenders, tenure, location list + "show on map" | The artifact you'd actually send to a partner | ⭐ | — |
| 3 | **Trade-area overlap / cannibalization** — flag units within N miles of each other | Rollup diligence: which markets are saturated vs. defensible | ◐ | M |

---

## 📊 New Data Layers

| # | Item | Why it matters | Impact | Effort |
|---|---|---|---|---|
| 4 | **FDD Item 19 (financial performance / AUV)** ✅ *(done)* — `parse_item19.py` extracts 2025 revenue by quartile + maturity cohort, memberships, rev/member, retention → "Unit Economics" analytics section + per-location/operator estimated revenue (cohort-average) | Revenue ≈ the single most valuable field for valuation | ⭐ | — |
| 5 | **Closure / churn tracking** ✅ *(done)* — `parse_churn.py` pulls FDD Item 20 outlet flow + Exhibit E (departed franchisees) → "Network Churn" analytics section (96.7% survival, departed list w/ reasons). Snapshot diffs extend this going forward. | Survivorship + operator risk | ⭐ | — |
| 6 | **SBA 504 + earlier 7(a) files** — pull the 504 dataset and FY2010–2019 7(a) | Completes the financing picture (504 funds real estate; some loans predate FY2020) | ◐ | M |
| 7 | **Demographics overlay** ✅ *(done, Phase 12)* — zip-level income/population via Census Reporter (keyless ACS) | Site-quality signal | ◐ | — |
| 8 | **Competitor density** ✅ *(done, Phase 12)* — OTF/F45/StretchLab within 5mi per location, 15mi per whitespace metro | Competitive context per market | ○ | — |
| 9 | **Multi-state FDD cross-check** — pull MN/CA/WA FDDs too | Validates the franchisee list and catches franchisees missed in one filing | ○ | L |

---

## 🔎 Analysis & Visualization

| # | Item | Why it matters | Impact | Effort |
|---|---|---|---|---|
| 10 | **Network growth time-lapse** — animate openings by year on the map | Tells the growth story at a glance | ◐ | S |
| 11 | **Cohort analysis** — rating & review volume vs. unit age | Do older units rate higher? Where's the ramp? | ◐ | M |
| 12 | **Whitespace *scoring*** ✅ *(done, Phase 12)* — metros ranked by pop × income × competitive openness | Makes the Whitespace tab actionable | ◐ | — |
| 13 | **Cross-source reconciliation** — FDD outlet count vs. website vs. SBA loan count | A trust/QA dashboard; surfaces data gaps | ○ | S |

---

## 🖥️ UX & Output

| # | Item | Why it matters | Impact | Effort |
|---|---|---|---|---|
| 14 | **Export** ✅ *(done)* — CSV of the current filtered locations (Locations tab) and the ranked operator table (Ownership tab) | People want the data *out* for spreadsheets/decks | ⭐ | — |
| 15 | **Shareable deep links** ✅ *(done)* — active filters/search/tab encoded in the URL, restored on load | Send a colleague "the 4.5★ TX multi-unit view" | ◐ | — |
| 16 | **Address search / "nearest Alloy"** — geocode an address, fly + list nearest | Common first thing a user tries | ◐ | S |
| 17 | **Mobile polish + dark mode** | Currently desktop-first | ○ | M |

---

## ⚙️ Pipeline & Reliability

| # | Item | Why it matters | Impact | Effort |
|---|---|---|---|---|
| 18 | **curl timeouts + unbuffered logging** ✅ *(done this session)* | Hardened every curl with `--max-time` + a subprocess backstop + one retry (insurance against a genuinely stalled request), and set `PYTHONUNBUFFERED` so logs stream live instead of looking hung | ⭐ | — |
| 19 | **Failure notifications** ✅ *(done)* — `refresh.sh` posts a macOS notification on any failed step (and on a successful deploy) | "Runs without intervention" needs to *tell you* when it can't | ⭐ | — |
| 20 | **Historical snapshots / changelog** ✅ *(done)* — `snapshot.py` saves a dated copy of `alloy_enriched.json` and prepends a "what changed" entry to `CHANGELOG.md` each refresh | Enables every time-series feature above (#5, #11) | ⭐ | — |
| 21 | **Manual-override file** — `overrides.json` for the ~18 unmatched owners / ~14 ungeocoded gaps and known fixes | Recover the long tail the fuzzy match misses, survives re-runs | ◐ | S |
| 22 | **Per-field confidence / "as-of" dates** in the UI | Honest provenance: ownership is ~annual, SBA ~quarterly, ratings monthly | ○ | M |

---

## Suggested sequence

1. ~~#20 snapshots + #19 failure alerts~~ ✅ **done** — automation hardened; time-series history now accumulating.
2. ~~#1–2 operator scoring + profile~~ ✅ **done** — ranked "Acquisition targets" list + operator profile modal.
3. ~~#14 export + #15 deep links~~ ✅ **done** — CSV export + shareable URL state.
4. ~~#4 Item 19 AUV~~ ✅ **done** — Unit Economics section + estimated revenue per location/operator.
5. ~~#5 closure/churn tracking~~ ✅ **done** — Network Churn section from FDD Item 20 + Exhibit E; snapshot diffs extend it over time.
6. Layer in the rest (demographics #7, competitors #8, SBA 504 #6, trade-area overlap #3) as appetite allows.

**Note:** the public-data + estimates build is now a fairly complete POC. The next big unlock is the **proprietary per-location KPIs** — to be wired into a **local-only private build** (gitignored, never pushed) when provided.
