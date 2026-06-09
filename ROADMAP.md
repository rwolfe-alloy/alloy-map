# Alloy Map — Next Phase Roadmap

Phases 1–6 are complete (map, pipeline, ratings, ownership, SBA financing, unattended refresh).
This is the prioritized backlog for what comes next. The project's north star is **franchise
rollup analysis**, so items are ranked by how much they advance that goal.

Legend — **Impact**: ⭐ high / ◐ medium / ○ nice-to-have · **Effort**: S / M / L

---

## 🎯 Flagship: Phase 7 — Acquisition-Target Scoring

The data is all here (units, ratings, capital, tenure, lender) but it's shown in separate tabs.
The next leap is to **synthesize it into a single ranked view of rollup targets**.

| # | Item | Why it matters | Impact | Effort |
|---|---|---|---|---|
| 1 | **Operator "rollup score"** — composite of unit count × avg rating × SBA capital × tenure, with a sortable, weighted table | Turns the map from a data viewer into a deal-sourcing tool: "who are the 10 best multi-unit operators to approach?" | ⭐ | M |
| 2 | **Operator profile / one-pager** — click an operator → modal with their units, ratings, total capital, lenders, map | The artifact you'd actually send to a partner or use in a pitch | ⭐ | M |
| 3 | **Trade-area overlap / cannibalization** — flag units within N miles of each other | Rollup diligence: which markets are saturated vs. defensible | ◐ | M |

---

## 📊 New Data Layers

| # | Item | Why it matters | Impact | Effort |
|---|---|---|---|---|
| 4 | **FDD Item 19 (financial performance / AUV)** — parse revenue figures already in the FDD we download | Revenue ≈ the single most valuable field for valuation; we already have the PDF | ⭐ | M |
| 5 | **Closure / churn tracking** — diff each monthly snapshot, flag units that went dark | Survivorship + operator risk; today we only see what's currently live | ⭐ | M |
| 6 | **SBA 504 + earlier 7(a) files** — pull the 504 dataset and FY2010–2019 7(a) | Completes the financing picture (504 funds real estate; some loans predate FY2020) | ◐ | M |
| 7 | **Demographics overlay** — median income / population density per trade area (Census ACS) | Site-quality signal; explains rating/ramp differences | ◐ | M |
| 8 | **Competitor density** — Orangetheory / F45 / StretchLab nearby (Places API) | Competitive context per market | ○ | M |
| 9 | **Multi-state FDD cross-check** — pull MN/CA/WA FDDs too | Validates the franchisee list and catches franchisees missed in one filing | ○ | L |

---

## 🔎 Analysis & Visualization

| # | Item | Why it matters | Impact | Effort |
|---|---|---|---|---|
| 10 | **Network growth time-lapse** — animate openings by year on the map | Tells the growth story at a glance | ◐ | S |
| 11 | **Cohort analysis** — rating & review volume vs. unit age | Do older units rate higher? Where's the ramp? | ◐ | M |
| 12 | **Whitespace *scoring*** — rank uncovered metros by opportunity (pop × income × competitor gap), not just population | Makes the Whitespace tab actionable for expansion | ◐ | M |
| 13 | **Cross-source reconciliation** — FDD outlet count vs. website vs. SBA loan count | A trust/QA dashboard; surfaces data gaps | ○ | S |

---

## 🖥️ UX & Output

| # | Item | Why it matters | Impact | Effort |
|---|---|---|---|---|
| 14 | **Export** — CSV/PDF of the current filtered view, operator table, loan table | People want the data *out* for spreadsheets/decks | ⭐ | S |
| 15 | **Shareable deep links** — encode active filters/tab in the URL | Send a colleague "the 4.5★ TX multi-unit view" | ◐ | S |
| 16 | **Address search / "nearest Alloy"** — geocode an address, fly + list nearest | Common first thing a user tries | ◐ | S |
| 17 | **Mobile polish + dark mode** | Currently desktop-first | ○ | M |

---

## ⚙️ Pipeline & Reliability

| # | Item | Why it matters | Impact | Effort |
|---|---|---|---|---|
| 18 | **curl timeouts + unbuffered logging** ✅ *(done this session)* | Hardened every curl with `--max-time` + a subprocess backstop + one retry (insurance against a genuinely stalled request), and set `PYTHONUNBUFFERED` so logs stream live instead of looking hung | ⭐ | — |
| 19 | **Hard per-step timeout + failure notification** — wrap steps; on failure send a macOS notification / email | "Runs without intervention" needs to *tell you* when it can't (the first validation run looked stuck for 2 min — it was fine, but you'd want a real signal when it isn't) | ⭐ | S |
| 20 | **Historical snapshots / changelog** — keep dated copies of `alloy_enriched.json`, auto-write a "what changed" diff each refresh | Enables every time-series feature above (#5, #11); cheap to start now | ⭐ | S |
| 21 | **Manual-override file** — `overrides.json` for the ~18 unmatched owners / ~14 ungeocoded gaps and known fixes | Recover the long tail the fuzzy match misses, survives re-runs | ◐ | S |
| 22 | **Per-field confidence / "as-of" dates** in the UI | Honest provenance: ownership is ~annual, SBA ~quarterly, ratings monthly | ○ | M |

---

## Suggested sequence

1. **#20 snapshots + #19 failure alerts** — small, and they harden the automation you just built (and unlock time-series).
2. **#1–2 operator scoring + profile** — the flagship rollup payoff, using data you already have.
3. **#14 export + #15 deep links** — make the insights portable.
4. **#4 Item 19 AUV** — the highest-value new dataset, parsed from the FDD you already download.
5. Layer in the rest (demographics, competitors, 504) as appetite allows.
