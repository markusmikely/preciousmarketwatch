# Caching (Section 3)

## Implemented in code

- **CACHE-04 — API Cache-Control**  
  REST responses set appropriate headers:
  - `GET /pmw/v1/prices/history`: `max-age=3600`, `s-maxage=3600`, `stale-while-revalidate=86400`
  - `GET /pmw/v1/gems`: `max-age=86400`, `s-maxage=86400`, `stale-while-revalidate=604800`  
  The cron endpoint `POST /pmw/v1/cron/price-update` is not cached.

- **CACHE-05 — WordPress transients**  
  - Gems: `pmw_gems_index` / `pmw_gems_index_stale`; invalidated on `save_post_gem_index`.
  - Prices history: transients keyed by metal/range/currency (1h TTL); invalidated when the daily price cron runs.
  - Optional: install [WPGraphQL Smart Cache](https://github.com/wp-graphql/wp-graphql-smart-cache) for GraphQL if you use it heavily.

- **CACHE-03 — Static build**  
  `frontend/public/_headers` is deployed with the SPA so the CDN can cache:
  - `/`: short cache for HTML
  - `/assets/*`: long cache + `immutable` for hashed assets

---

## Manual setup (you add keys to environment variables as needed)

### CACHE-01 — Cloudflare

1. Add the site to Cloudflare (DNS and/or proxy).
2. In **Dashboard → Caching → Configuration**, enable caching and choose a **Caching Level** (e.g. Standard).
3. Any Cloudflare-specific keys (e.g. API token for cache purge) can be added to your environment; the app does not require them for the above behaviour.

### CACHE-02 — Cloudflare cache rules

1. **Dashboard → Caching → Cache Rules** (or **Page Rules** on older plans).
2. Add rules, for example:
   - **Backend API** (e.g. `api.yoursite.com` or `yoursite.com/wp-json/pmw/*`):  
     If URI Path matches `/wp-json/pmw/v1/prices/*` or `/wp-json/pmw/v1/gems` → **Eligible for cache**, **TTL** Respect origin (`Cache-Control` from WordPress).
   - **Frontend** (SPA):  
     If URI Path matches `/assets/*` → **Eligible for cache**, **TTL** 1 year (or Respect origin to use `_headers`).  
     If URI is `/` or other HTML → **Eligible for cache**, **TTL** short (e.g. 5 minutes) or Respect origin.

These steps are done in the Cloudflare dashboard; no code or env keys are required unless you automate purge via API (then you’d add a Cloudflare API token to your env).
