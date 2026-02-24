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

### Section 3 — Caching
- **CACHE-01** — Cloudflare (manual setup)
- **CACHE-02** — Cloudflare cache rules (manual)
- **CACHE-03** — ISR: N/A for Vite SPA; consider CDN caching of static build
- **CACHE-04** — API Cache-Control: already set on `/pmw/v1/prices/history`, `/pmw/v1/gems`
- **CACHE-05** — WordPress transients / WPGraphQL Smart Cache

### Section 4 — Cookie consent & analytics
- **CONSENT-01 to 05** — Implement in React (not WP plugins)
- **ANALYTICS-01** — GA4 gated by consent
- **ANALYTICS-02** — Microsoft Clarity gated by consent
- **ANALYTICS-03** — GSC, sitemap, robots.txt
- **ANALYTICS-04** — Privacy, Cookie, Affiliate disclosure pages
- **ANALYTICS-05** — Performance baseline

### Section 5 — Homepage
- **HOME-01** — Coverage stats from GraphQL
- **HOME-02** — Mailchimp newsletter (needs API route; Vite has no `/api`, could use WordPress REST)
- **HOME-03** — AI dealer reviews

### Section 6–10
- Metal hero from GraphQL, dealer filters, contact form, affiliate setup, pre-launch checklist, etc.

---

## WordPress category setup for metal pages

For GraphQL articles to appear on metal pages, create WordPress categories:

- Slug: `gold`, `silver`, `platinum`, `palladium`
- Assign posts to these categories as needed
