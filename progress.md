# Alloy Personal Training — Interactive Map · Project Progress

## Live URL
**https://rwolfe-alloy.github.io/alloy-map/**
GitHub repo: `https://github.com/rwolfe-alloy/alloy-map`

---

## What This Is
A self-contained interactive map of all Alloy Personal Training franchise locations in the US, built for franchise rollup analysis. Single `index.html` file — no build step, no server required.

---

## Project Files

| File | Description |
|---|---|
| `index.html` | The complete map app — ~180KB, all data embedded |
| `alloy_enriched.json` | Master dataset — 169 locations with all fields (see schema below) |
| `alloy_locations.json` | Original clean locations (lat/lng/address/phone/url) — kept as source of truth |
| `alloy_whitespace.json` | 16 major metros (500k+ pop) with no Alloy within 50 miles |
| `fetch_ratings.py` | Phase 4 — fetches Google Places ★ rating + review count per location (needs API key) |
| `parse_fdd.py` | Phase 5 — parses Exhibit D (franchisee list) from the 2026 FDD text dump into `_fdd_franchisees.json` |
| `match_owners.py` | Phase 5 — matches franchisee records to locations (email/address/facility) and writes `owner` + `franchisee` |
| `match_sba.py` | Phase 6 — extracts Alloy 7(a) loans from the SBA FOIA CSV (franchise code S4826) and matches each to a location → `alloy_sba_loans.json` |
| `alloy_sba_loans.json` | 106 SBA 7(a) loans (amount, bank, year, term, jobs, matched location) — embedded into `index.html` as `SBA_LOANS` |
| `rebuild_index.py` | Re-embeds LOCATIONS + WHITESPACE + SBA_LOANS into `index.html` (replaces the `const` data lines in place — no template file) |
| `scrape_locations.py` | Re-scrapes locations + hours/email/social/coming_soon and **merge-preserves** Phase 4–6 fields into `alloy_enriched.json` |
| `fetch_fdd.py` | Auto-downloads the latest registered FDD from WI DFI + extracts Exhibit D → `_exhibitD.txt` (dynamic page detection) |
| `refresh.sh` | Unattended orchestrator: `locations` / `sba` / `fdd` modes → rebuild → commit + push (only if data changed); logs to `logs/` |
| `setup_schedule.sh` | Installs the launchd jobs (monthly / quarterly / annual) that run `refresh.sh` |
| `snapshot.py` | Saves a dated copy of `alloy_enriched.json` to `snapshots/` and prepends a "what changed" entry to `CHANGELOG.md` each refresh |
| `parse_item19.py` | Parses FDD **Item 19** (financial performance) → `alloy_item19.json` (revenue by quartile/maturity, memberships, retention) |
| `alloy_item19.json` | Parsed Item 19 figures — embedded into `index.html` as `ITEM19` |
| `parse_churn.py` | Parses FDD **Item 20** outlet flow + **Exhibit E** (departed franchisees) → `alloy_churn.json` |
| `alloy_churn.json` | Systemwide outlet open/close by year + departed-franchisee list — embedded as `CHURN` |
| `build_trends.py` | Distills `snapshots/` into month-over-month trends (review velocity, rating moves, went-live, lost listings) → `alloy_trends.json` |
| `alloy_trends.json` | Network series + latest-period per-location deltas — embedded as `TRENDS` |
| `CHANGELOG.md` | Auto-generated history of data changes (new/dropped locations, rating/owner/status changes) |
| `snapshots/` | Dated point-in-time copies of the dataset (the time-series record) |
| `ROADMAP.md` | Prioritized next-phase backlog |
| `.gitignore` | Excludes `.apikey`, `logs/`, `*.csv`, `*.pdf`, and `_*` scratch files |

---

## Data Schema — `alloy_enriched.json`

Each record has these fields:

| Field | Type | Source | Coverage |
|---|---|---|---|
| `n` | string | Alloy website | 169/169 |
| `a` | string | Alloy website | 169/169 |
| `s` | string | Alloy website | 169/169 — state abbr |
| `r` | string | Computed | 169/169 — Northeast/Southeast/Midwest/Southwest/West |
| `lat` | float | Alloy website | 169/169 |
| `lng` | float | Alloy website | 169/169 |
| `p` | string | Alloy website | ~169/169 — phone |
| `u` | string | Alloy website | 169/169 — location page URL |
| `y` | string | WP REST API (`/wp-json/wp/v2/location`) | 169/169 — year page published (proxy for opening year) |
| `m` | string | Computed via haversine | 158/169 — nearest named metro within 50 miles |
| `coming_soon` | bool | Scraped from location page | 169/169 — 25 flagged |
| `email` | string | Scraped (Cloudflare XOR decode) | 168/169 |
| `hours` | object | Scraped from location page | 164/169 — `{Mon,Tue,Wed,Thu,Fri,Sat,Sun}` each `"6AM - 8PM"` or `"Closed"` |
| `instagram` | string | Scraped (per-location only) | 144/169 — handle only, no URL prefix |
| `facebook` | string | Scraped (per-location only) | 162/169 — handle only |
| `place_id` | string | Google Places API (New) | 169/169 — canonical `ChIJ…` id (replaced the proto token) |
| `rating` | float\|null | Google Places API (New) | 157/169 — null when no live Google listing (coming-soon) |
| `review_count` | int\|null | Google Places API (New) | 157/169 |
| `owner` | string | 2026 FDD Exhibit D | 149/169 — franchisee owner person name |
| `franchisee` | string | 2026 FDD Exhibit D | 130/169 — franchisee legal entity (LLC/Inc) |

**Note on email:** Alloy uses Cloudflare email obfuscation (`data-cfemail` hex attribute). Decoded via XOR — first byte is key, remaining bytes XOR'd to get email string. Pattern is consistently `info.[location]@alloypersonaltraining.com`.

---

## Network Stats (as of Jun 2026)

- **169 total** locations — 144 live, 25 coming soon
- **34 states** — TX (25), GA (15), CA (15), IL (10), FL (9)
- **Regions:** Southeast 49, West 37, Midwest 35, Southwest 31, Northeast 17
- **Openings by year:** 2021: 8, 2022: 9, 2023: 24, 2024: 60, 2025: 54, 2026: 14
- **Hours:** 157/164 locations open at 6AM Mon–Fri; 163/164 closed Sunday
- **16 whitespace metros** (largest: Sacramento 2.4M, Columbus 2.1M, Providence 1.7M)
- **Google ratings:** 157/169 rated, **network avg 4.96★** across 7,160 reviews; 151 at 4.8–5.0, none below 4.0 (lowest 4.1). 12 unrated (11 coming-soon + 1 brand-new listing)
- **Ownership (2026 FDD):** 151/169 matched to a franchisee operator (149 with owner name); **122 operators, 20 multi-unit** (49 locations). Largest: John Farkas, Daniel Atkins, Trey Ely (4 each). 18 unmatched (company-owned or opened after Dec 2025)
- **SBA 7(a) financing:** **$26.4M** across 106 loans (FY2022–26), 95 matched to 55 locations; avg $249K, median $317K, 581 jobs supported. **Huntington National Bank = 85 of 106 loans** (dominant Alloy SBA lender). Top-funded: Falls Church VA $812K (4 loans)
- **Unit economics (2026 FDD Item 19, 2025 period):** **system AUV ~$395K**; quartile avgs $555K → $253K; by maturity $371K (12–24mo) → $445K (36+mo); ~93 members/unit, ~$348 rev/member/mo, 90.3% monthly retention
- **Network churn (2026 FDD Item 20 + Exhibit E):** **96.7% outlet survival** — only 4 closures of 120 opened (2023–25); franchised outlets 12→30→77→128; 13 ownership transfers, 7 signed-but-never-opened

---

## Features Built

### Map
- Leaflet + MarkerCluster (CARTO light basemap)
- **Red pins** — live locations
- **Green pins** — currently open (timezone-aware, refreshes every 60s)
- **Dashed amber pins** — coming soon locations
- **Gray pins** — whitespace metros (toggleable layer)

### Sidebar — Overview Tab *(Phase 10 / Theme 1 — default landing)*
- **Hero KPI board** — 9 headline metrics (locations, states, live/soon, avg ★, system AUV, survival, SBA capital, operators, multi-unit)
- **Auto-generated Deal Memo** — narrative synthesis of the whole dataset (regenerates with each refresh)
- **Top Markets** — every metro ranked by a rollup-opportunity score (units × est. revenue × rating); sortable; click to fly the map
- **Acquisition Basket** — add operators (from their profile) to model a roll-up; live tally of units / states / est. revenue / SBA debt (persists via localStorage)
- **Implied Valuation lens** — est. revenue × adjustable EBITDA margin × EV/EBITDA multiple → implied EBITDA + EV (basket if selected, else whole network)

### Sidebar — Locations Tab
- **Status pills:** All 169 / Live 144 / Soon 25
- **Open Now toggle** — filters to currently open locations, per-state IANA timezone
- **Filters:** Region, State, Year Opened, Density (≥5 / 2–4 / single-market), Google rating checkboxes
- **Search:** name + address full-text
- **⬇ CSV export** of the current filtered view *(Phase 7)*
- **Shareable deep links** *(Phase 7)*: active filters/search/tab encode into the URL and restore on load
- **Cards** show: region tag, year tag, metro tag, "Open now" or "Opening [year]" badge, phone, directions, IG/FB links, email

### Sidebar — Analytics Tab
- Stat cards: Total, States, Pipeline (coming soon count), Opened 2025–26, Avg Google ★, Below 4.0 ★
- **SBA 7(a) Financing section** *(Phase 6)*: stat cards (capital deployed, loans, avg loan, jobs supported) + "Loans Approved by Year" and "Top SBA Lenders" charts
- **Unit Economics section (FDD Item 19)** *(Phase 8)*: System AUV, avg members/unit, revenue/member, monthly retention + "Avg Revenue by Maturity" and "by Quartile" charts
- **Network Churn section (FDD Item 20 + Exhibit E)** *(Phase 9)*: outlet survival rate, closures, transfers, never-opened + year-end outlet chart + departed-franchisees modal (reason-coded). Snapshot diffs extend it over time.
- **Trending section (snapshot deltas)** *(Phase 11)*: hottest location, opened-this-period, gainers, watch-list stat cards + "Fastest-Growing Locations" (review velocity /mo) and network-by-snapshot charts + watch-list modal (declines & lost Google listings). Deepens automatically as monthly snapshots accumulate.
- Bar charts: Rating Distribution, Openings by Year, By Region, Top 12 States

### Sidebar — Ownership Tab *(Phase 5–7)*
- Stat cards: Operators, Multi-unit operators
- "Largest Multi-Unit Operators" bar chart (colored per operator)
- **"Acquisition targets — ranked"** *(Phase 7)*: every operator ranked by a **rollup score** (0–100, composite of units 35% × avg rating 25% × SBA capital 25% × tenure 15%); sortable by score / units / rating / capital / name
- Each row shows units · avg ★ · SBA capital · since-year, with a tier-colored score badge
- **Click any operator → profile modal** *(Phase 7)*: units, avg rating, reviews, SBA capital, loans, tenure, states, lenders, per-location list, and "Show all on map"
- **⬇ CSV export** of the ranked operator table *(Phase 7)*

### Sidebar — Whitespace Tab
- 16 uncovered major metros, sorted by population
- Click any row to fly map to that location

### Map Layer Toggles (top-right)
- **State density choropleth** — GeoJSON loaded from PublicaMundi CDN at runtime; state colors by location count; legend shown
- **Coverage radius** — 1 / 2 / 5 / 10 mile selectable circles; rebuilds on size change
- **Whitespace metros** — gray pins for the 16 uncovered metros
- **Color by rating** — recolors live pins green/amber/red by Google ★ tier
- **Color by operator** — recolors pins by franchisee operator (multi-unit each a distinct color)
- **Color by momentum** *(Phase 11)* — recolors pins by review velocity (🔥 hot ≥15/mo, growing, opened-this-period, listing-lost, steady); the three color modes are mutually exclusive

### Popup / Cards (per location)
- Name with green "open now" dot or amber "Coming Soon" badge
- Address, region/year/metro tags
- Google ★ rating + review count *(Phase 4)*
- Franchisee owner + entity with operator color dot + "N units" badge *(Phase 5)*
- **SBA 7(a) funding badge** — total + loan count for funded locations *(Phase 6)*
- **Estimated revenue** — FDD Item 19 maturity-cohort average by opening year (labeled estimate) *(Phase 8)*
- **Momentum badge** — 🔥/▲ review velocity, rating moves, 🆕 opened-this-period, ⚠️ listing-lost *(Phase 11)*
- Collapsible hours schedule (today's day highlighted in red)
- Phone, Directions, Details links · IG / FB / email links

---

## Data Sources

| Source | What we get | How accessed |
|---|---|---|
| `alloypersonaltraining.com/locations/` | JS array `var locations = [...]` embedded on page | `curl` + custom JS comment stripper + JSON parse |
| `alloypersonaltraining.com/wp-json/wp/v2/location` | Post dates (opening year proxy) | WordPress REST API, paginated 100/page |
| Individual location pages (`/location/[slug]/`) | Hours, email, social handles, coming_soon | `curl` batch scrape, 10 concurrent workers |
| PublicaMundi GitHub GeoJSON | US states boundaries for choropleth | Fetched at runtime by browser |
| Wisconsin DFI Franchise Search | Full 2026 Alloy FDD PDF (free, no paywall) | ASP.NET form POST (see Phase 5 below) |
| Google Places API (New) | ★ ratings + review counts + `ChIJ…` place_ids | `places:searchText` REST endpoint |
| SBA 7(a) FOIA (data.sba.gov) | Franchise-coded 7(a) loans (S4826) | CKAN `resource_show` API → CSV download |

---

## Automated Refresh *(unattended, via launchd)*

Installed by `./setup_schedule.sh` (per-user LaunchAgents in `~/Library/LaunchAgents/com.alloymap.*`). Each job runs `refresh.sh <mode>`, which runs the scrapers/matchers, rebuilds `index.html`, and **commits + pushes to `main` only if tracked data changed** (GitHub Pages auto-deploys). All runs log to `logs/`.

| Job | Schedule | Mode | What it refreshes |
|---|---|---|---|
| `com.alloymap.monthly` | 1st of month, 06:00 | `locations` | Re-scrape locations + hours/social, then Google ratings |
| `com.alloymap.quarterly` | 1st of Jan/Apr/Jul/Oct, 07:00 | `sba` | Re-pull SBA 7(a) CSV (URL resolved via CKAN API) + re-match |
| `com.alloymap.annual` | May 1, 08:00 | `fdd` | Download new FDD from WI DFI + re-parse ownership |

**Why these cadences:** locations/ratings move continuously (≈1 opening/week) → monthly; the SBA FOIA file reposts ~quarterly; the FDD is filed once a year (≈April, year-end snapshot). Ownership is therefore inherently up to ~12 months stale and SBA lags ~1 quarter — a limit of the public sources.

Each run also **snapshots the dataset + appends to `CHANGELOG.md`** (`snapshot.py`) before committing, and posts a **macOS notification** on failure or successful deploy.

**Operational notes:**
- LaunchAgents run in the user session, so git's `osxkeychain` credential helper works for `git push` while logged in. Jobs missed while the Mac is asleep/off run at next wake.
- `refresh.sh` pins `PATH` and uses `/usr/local/bin/python3` (the interpreter with `pdfplumber`).
- The monthly ratings step needs `.apikey` to persist (so don't rotate the key away if you want unattended ratings).
- A bad scrape (<90% of current location count) **aborts before any push**, so it can't overwrite good data with garbage.
- The `fdd` job is the most fragile (gov ASP.NET portal + 275-page PDF layout) — check `logs/refresh-fdd-*.log` each spring; fall back to the manual steps in Phase 5 if it fails.
- Manage jobs: `launchctl list | grep alloymap`; remove with `launchctl bootout gui/$(id -u)/com.alloymap.<job>`.

---

## Deployment

- GitHub Pages (legacy build), branch: `main`, path: `/`
- Auto-deploys on every `git push` — typically live within 60–90 seconds
- To update data: re-run scraper, rebuild `index.html`, push

### Rebuild steps (if re-scraping)
```bash
# 1. Re-extract raw locations from Alloy website
curl -s -L https://www.alloypersonaltraining.com/locations/ -o _locs.html
# then run extraction script (see git history for scrape_locations.py)

# 2. Fetch WP post dates
curl -s "https://alloypersonaltraining.com/wp-json/wp/v2/location?per_page=100&page=1&_fields=id,date" -o _dates_p1.json
curl -s "https://alloypersonaltraining.com/wp-json/wp/v2/location?per_page=100&page=2&_fields=id,date" -o _dates_p2.json

# 3. Run enrichment + scrape
python3 scrape_locations.py  # (restore from git history if needed)

# 4. Rebuild index.html (re-embeds the two const data lines in place)
python3 rebuild_index.py

# 5. Push
git add index.html alloy_enriched.json alloy_whitespace.json
git commit -m "Refresh location data"
git push
```

---

## Deployment Plan — Remaining Phases

### Phase 4 — Google Places Ratings ✅ *(COMPLETE)*

Star ratings + review counts fetched for all 169 locations and shipped.

- **API:** Uses the **Places API (New)** `places:searchText` endpoint (POST with `X-Goog-Api-Key` + `X-Goog-FieldMask` headers) — the legacy Find Place endpoint is **not** enabled on the project, so the script targets the new API. Text query is `"Alloy Personal Training {address}"`; takes the top result. This also returned canonical `ChIJ…` place_ids, which replaced the base64 proto tokens.
- **`fetch_ratings.py`:** reads key from `.apikey` / `$GOOGLE_PLACES_API_KEY` / argv; `curl` (SSL workaround); writes `rating`, `review_count`, `place_id` back into `alloy_enriched.json`; stops early on API errors.
- **Results:** 157/169 rated, avg **4.96★**, 7,160 reviews, none below 4.0. 12 unrated (coming-soon / brand-new listings).
- **Frontend (`index.html`):**
  - ★ rating + review count on **cards** and **popups** (hidden when null).
  - **Rating filter:** All / 4.5+ / 4.0+ / Below 4.0 / Unrated.
  - **"Color by rating"** map-layer toggle — recolors live pins by tier (4.5+ green, 4.0–4.5 amber, <4.0 red, unrated gray) + bottom-left legend. Independent of the open/live/soon scheme.
  - **Analytics:** "Avg Google ★" + "Below 4.0 ★" stat cards + Rating Distribution chart.
- **Gotcha for re-runs:** if the key only has *Places API (New)* enabled, the legacy endpoint returns `REQUEST_DENIED` ("calling a legacy API"). `fetch_ratings.py` already uses the new endpoint.

### Phase 5 — FDD Franchisee Ownership ✅ *(COMPLETE)*

Franchisee owner + entity for 151/169 locations, plus an Ownership tab, color-by-operator map mode, and multi-unit analytics — all from the **2026 Alloy FDD**.

- **Source obtained:** Wisconsin DFI Franchise Search (free, full PDF, no paywall). Filing **#641123, Alloy Personal Training LLC, registered 4/20/2026**. The CA DFPI / FranChimp routes are Cloudflare-gated; WI DFI is the reliable free source.
  - **How to re-download** (ASP.NET, viewstate POST — session-specific, do via `curl` with a cookie jar):
    1. GET `https://apps.dfi.wi.gov/apps/FranchiseSearch/MainSearch.aspx`, save cookies, scrape all `__VIEWSTATE*` hidden fields (split across `__VIEWSTATE`, `__VIEWSTATE1`, … per `__VIEWSTATEFIELDCOUNT`).
    2. POST `txtName=Alloy` + `btnSearch` → follow the `Object moved` redirect → results list → grab the registered filing's `details.aspx?id=…&hash=…`.
    3. GET the details page, scrape its `__VIEWSTATE*`, POST `upload_downloadFile=Download` → returns the FDD PDF (~7.4 MB).
- **Parse:** `pdfplumber` (installed via pip). FDD is 275 pages; **Exhibit D** (p150–167) = "LIST OF FRANCHISEES (as of Dec 31, 2025)" — a two-column directory. Column-aware word extraction (split at x≈300), entries delimited by their `Phone` line. → `parse_fdd.py` → 197 franchisee records (entity, facility, owner person, email, address).
- **Match:** `match_owners.py` joins franchisee records to the 169 locations by **email (exact) → zip+street-no → facility-name token overlap**. 151 matched, 0 wrong (spot-verified). Writes `owner` + `franchisee` into `alloy_enriched.json`.
- **Frontend (`index.html`):**
  - Owner + entity line on **cards** and **popups** (colored dot + "N units" badge for multi-unit operators).
  - **"Color by operator"** map-layer toggle — each multi-unit operator a distinct color, single-unit slate, unmatched gray; bottom-left legend lists top operators. Mutually exclusive with "Color by rating".
  - **New "Ownership" tab:** operator/multi-unit stat cards, "Largest Multi-Unit Operators" bar chart, and a full operator list (multi-unit then single) — click any operator to fly the map to their locations.
- **Pipeline to refresh:** `parse_fdd.py` → `match_owners.py` → `rebuild_index.py`.
- **Gotchas:** (1) zip extraction must take the *last* 5-digit group — a 5-digit street number (e.g. 25030) otherwise masks the zip. (2) Strip leading `*` footnote markers before person-name detection. (3) Exhibit D state headers occasionally mis-track across columns, so the franchisee record's `state` field is unreliable — match on email/address/facility, not state.

### Phase 6 — SBA Loan Data ✅ *(COMPLETE)*

$26.4M of SBA 7(a) financing into the Alloy system, mapped to locations + operators, with a financing analytics section.

- **Source:** SBA 7(a) FOIA dataset, **FY2020-present** CSV (data.sba.gov, ~144 MB / 374K rows, as of 2026-03-31). Direct CSV download (no auth):
  `https://data.sba.gov/en/dataset/0ff8e8e9-b967-4f4e-987c-6ac78c575087/resource/d67d3ccb-2002-4134-a288-481b51cd3479/download/foia-7a-fy2020-present-asof-260331.csv`
- **Filter:** rows where `franchisename` contains "alloy personal" — **franchise code S4826** ("Alloy Personal Traning", SBA's typo). 106 loans, FY2022–26.
- **Match (`match_sba.py`):** each loan → location by `borrzip`==location zip ∩/then franchisee-entity name (from Phase 5) → 95/106 matched to 55 locations. Writes `alloy_sba_loans.json` (embedded as `SBA_LOANS`).
- **Frontend:**
  - SBA funding badge on **cards + popups** (total + loan count) for funded locations.
  - **Analytics → "SBA 7(a) Financing"** section: stat cards (capital deployed, loans, avg size, jobs supported) + "Loans Approved by Year" + "Top SBA Lenders" charts.
  - **Ownership tab** rows show each operator's total SBA capital.
- **Pipeline:** `match_sba.py` → `rebuild_index.py` (now embeds LOCATIONS + WHITESPACE + SBA_LOANS).
- **Key finding:** Huntington National Bank originated 85 of 106 loans — the de-facto Alloy SBA lender. Loan pattern is typically two per franchisee: a small ~$25–30K startup loan + a larger ~$300–500K build-out loan.
- **Note:** the FOIA CSV (`_sba_7a.csv`) is gitignored; re-download from the URL above. Loan amounts are `grossapproval`; only loans SBA coded to franchise S4826 are captured (a franchisee financing via 504, conventional, or uncoded 7(a) won't appear).

---

## Git History

```
0556ccb  Execute Phase 2 & 3: Coming Soon pipeline, hours, Open Now, social links
4c3faf1  Fix choropleth: map state names to abbreviations
2fa8216  Add 1/2/5/10 mile radius selector for coverage circles
9573f06  Add franchise analytics, filters, choropleth, and whitespace analysis
e68b917  Add interactive map of Alloy Personal Training US locations
```

---

## Technical Notes

- **SSL in Python:** `urllib` fails SSL verification on this machine — use `curl` via `subprocess` for all HTTP fetching
- **Cloudflare emails:** `data-cfemail="hexstring"` — decode: `bytes.fromhex(s)`, first byte = XOR key, rest XOR'd = email
- **WP post type:** `location` (custom) — accessible at `/wp-json/wp/v2/location`
- **GeoJSON state property:** `f.properties.name` is the full state name (not postal code) — requires `STATE_NAME_TO_ABBR` lookup
- **Preview server:** `python3 -m http.server 8777` from project directory; config in `.claude/launch.json`
- **Hours format variants seen:** `"6AM - 8PM"`, `"5AM - 1PM, 4PM - 8PM"` (split schedule), `"5:30AM - 8PM"`, `"Closed"`, `"7 am - 12PM"` (inconsistent capitalization — handled by case-insensitive parse)
