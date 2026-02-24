# PMW Remaining Tasks

> **Note:** The project uses **React + Vite** (not Next.js). Task specs referencing `getStaticProps`, `pages/api`, `app/layout.tsx`, etc. need to be adapted.

## Completed This Session

### Backend: Charts & current values
- **Metals Seed** (Tools → Metals Seed): Shows current prices table (latest from `metal_prices`), 30-day chart (Chart.js), and link to Market Data.
- **Market Data** (WP admin sidebar): ACF options page with USD/GBP/24h-change per metal, populated by daily cron.

### GraphQL integration for metal pages
- **Gold, Silver, Platinum, Palladium** pages now fetch articles from WPGraphQL (by category slug: gold, silver, platinum, palladium).
- **Gold** also fetches dealers filtered by metal type.
- Fallback content shown when GraphQL returns no data.
- New: `frontend/src/queries/metalPages.ts`, `frontend/src/components/metals/useMetalPageData.ts`.

---

## Remaining (from v3.0 task list)

### Section 3 — Caching ✅
- **CACHE-01** — Cloudflare (manual setup) — see `docs/CACHING.md`
- **CACHE-02** — Cloudflare cache rules (manual) — see `docs/CACHING.md`
- **CACHE-03** — `frontend/public/_headers` for CDN (HTML + `/assets/*` immutable)
- **CACHE-04** — API Cache-Control with `s-maxage` and `stale-while-revalidate` on prices/history and gems
- **CACHE-05** — Gems transients + invalidation on save; prices/history transients + invalidation on cron; see `docs/CACHING.md` for WPGraphQL Smart Cache

### Section 4 — Cookie consent & analytics ✅
- **CONSENT-01 to 05** — React consent context + banner (Accept all / Reject / Custom); stored in localStorage; "Change preferences" on Cookie Policy
- **ANALYTICS-01** — GA4 with Consent Mode v2 (default denied); loads when user accepts analytics; `VITE_GA4_MEASUREMENT_ID`
- **ANALYTICS-02** — Microsoft Clarity loads when analytics accepted; `VITE_CLARITY_PROJECT_ID`
- **ANALYTICS-03** — `robots.txt` with Sitemap; GSC setup described in `docs/ANALYTICS.md`
- **ANALYTICS-04** — Privacy, Cookie, Affiliate disclosure pages present and linked
- **ANALYTICS-05** — Performance baseline process in `docs/PERFORMANCE.md`

### Section 5 — Homepage ✅
- **HOME-01** — Coverage stats from GraphQL: `CoverageStats` on homepage with counts from `COVERAGE_STATS_QUERY` (posts, dealers); metals fixed at 4
- **HOME-02** — Mailchimp newsletter: WordPress REST `POST /pmw/v1/subscribe` in pmw-core; set `PMW_MAILCHIMP_API_KEY` and `PMW_MAILCHIMP_LIST_ID` in wp-config
- **HOME-03** — AI dealer reviews: `AIDealerReviews` section on homepage (independent/AI-verified copy, dealer highlights, link to Top Dealers & Editorial Standards)

### Section 6–10
- Metal hero from GraphQL, dealer filters, contact form, affiliate setup, pre-launch checklist, etc.

---

## WordPress category setup for metal pages

For GraphQL articles to appear on metal pages, create WordPress categories:

- Slug: `gold`, `silver`, `platinum`, `palladium`
- Assign posts to these categories as needed
