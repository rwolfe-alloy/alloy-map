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
| `index.html` | The complete map app — ~145KB, all data embedded |
| `alloy_enriched.json` | Master dataset — 169 locations with all fields (see schema below) |
| `alloy_locations.json` | Original clean locations (lat/lng/address/phone/url) — kept as source of truth |
| `alloy_whitespace.json` | 16 major metros (500k+ pop) with no Alloy within 50 miles |
| `fetch_ratings.py` | Phase 4 — fetches Google Places ★ rating + review count per location (needs API key) |
| `rebuild_index.py` | Re-embeds `alloy_enriched.json` + `alloy_whitespace.json` into `index.html` (replaces the two `const` data lines in place — no template file) |
| `.gitignore` | Excludes `.apikey` and `_*` scratch files from commits |

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

---

## Features Built

### Map
- Leaflet + MarkerCluster (CARTO light basemap)
- **Red pins** — live locations
- **Green pins** — currently open (timezone-aware, refreshes every 60s)
- **Dashed amber pins** — coming soon locations
- **Gray pins** — whitespace metros (toggleable layer)

### Sidebar — Locations Tab
- **Status pills:** All 169 / Live 144 / Soon 25
- **Open Now toggle** — filters to currently open locations, per-state IANA timezone
- **Filters:** Region, State, Year Opened, Density (≥5 / 2–4 / single-market)
- **Search:** name + address full-text
- **Cards** show: region tag, year tag, metro tag, "Open now" or "Opening [year]" badge, phone, directions, IG/FB links, email

### Sidebar — Analytics Tab
- Stat cards: Total, States, Pipeline (coming soon count), Opened 2025–26
- Bar charts: Openings by Year, By Region, Top 12 States

### Sidebar — Whitespace Tab
- 16 uncovered major metros, sorted by population
- Click any row to fly map to that location

### Map Layer Toggles (top-right)
- **State density choropleth** — GeoJSON loaded from PublicaMundi CDN at runtime; state colors by location count; legend shown
- **Coverage radius** — 1 / 2 / 5 / 10 mile selectable circles; rebuilds on size change
- **Whitespace metros** — gray pins for the 16 uncovered metros

### Popup (per location)
- Name with green "open now" dot or amber "Coming Soon" badge
- Address, region/year/metro tags
- Collapsible hours schedule (today's day highlighted in red)
- Phone, Directions, Details links
- IG / FB / email links

---

## Data Sources

| Source | What we get | How accessed |
|---|---|---|
| `alloypersonaltraining.com/locations/` | JS array `var locations = [...]` embedded on page | `curl` + custom JS comment stripper + JSON parse |
| `alloypersonaltraining.com/wp-json/wp/v2/location` | Post dates (opening year proxy) | WordPress REST API, paginated 100/page |
| Individual location pages (`/location/[slug]/`) | Hours, email, social handles, coming_soon | `curl` batch scrape, 10 concurrent workers |
| PublicaMundi GitHub GeoJSON | US states boundaries for choropleth | Fetched at runtime by browser |

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

### Phase 5 — FDD Franchisee Ownership
- **Data source:** Public Franchise Disclosure Documents filed with state regulators
  - CA: DFPI portal — https://docqnet.dfpi.ca.gov/
  - WA: DFI — https://www.dfi.wa.gov/
  - MD, IL, NY, VA also require FDD registration (free PDF downloads)
  - Item 20 = complete franchisee list with name, address, phone, open/closed dates
- **What to build:**
  - Parse Item 20 tables from FDD PDFs (likely need `pdfplumber` or `pypdf2`)
  - Match franchisees to locations by address/city
  - Add `owner_name` field to enriched dataset
  - Color-code map pins by owner (multi-unit operators show as same color)
  - New "Ownership" tab: table of franchisees sortable by unit count
  - Analytics: "Multi-unit operators" chart

### Phase 6 — SBA Loan Data
- **Source:** Treasury/SBA public loan data (7a loans by franchisee)
- Signals capital commitment and financing method per franchisee

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
