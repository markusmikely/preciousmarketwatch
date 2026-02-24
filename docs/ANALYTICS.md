# Analytics & SEO (Section 4)

## Implemented

### Cookie consent (CONSENT-01 to 05)
- **React-only** consent: no WordPress plugins.
- **Banner**: Accept all, Reject non-essential, Customize (analytics, marketing, preferences). Necessary cookies always on.
- **Storage**: Choice and per-category consent stored in `localStorage` under `pmw_consent`.
- **Cookie Policy** (`/cookies`): "Change cookie preferences" reopens the banner.
- **Footer**: Links to Privacy, Terms, Affiliate Disclosure, Cookie Policy.

### GA4 gated by consent (ANALYTICS-01)
- **Consent Mode v2**: In `index.html`, `gtag('consent', 'default', …)` runs before any Google script with `analytics_storage` and `ad_storage` denied.
- **When user accepts analytics**: `AnalyticsLoader` updates consent to granted and loads `gtag/js` + `gtag('config', GA_MEASUREMENT_ID)`.
- **Env**: `VITE_GA4_MEASUREMENT_ID` (e.g. `G-XXXXXXXXXX`). Leave empty to disable GA4.

### Microsoft Clarity gated by consent (ANALYTICS-02)
- Clarity script is injected only when the user has accepted **analytics** cookies.
- **Env**: `VITE_CLARITY_PROJECT_ID`. Leave empty to disable Clarity.

### GSC, sitemap, robots.txt (ANALYTICS-03)
- **robots.txt**: In `frontend/public/robots.txt` (deployed at `/robots.txt`). Allows major crawlers; includes `Sitemap: https://preciousmarketwatch.com/wp/wp-sitemap.xml` (WordPress sitemap). Adjust the Sitemap URL if your WordPress is at a different path or you use a different sitemap.
- **Google Search Console**: Add the property, verify ownership, and submit the sitemap URL. No code changes required.

### Legal pages (ANALYTICS-04)
- **Privacy Policy** (`/privacy`), **Terms of Service** (`/terms`), **Affiliate Disclosure** (`/affiliate-disclosure`), **Cookie Policy** (`/cookies`) exist and are linked in the footer and from the consent banner.

### Performance baseline (ANALYTICS-05)
- See `docs/PERFORMANCE.md` for how to establish and monitor a performance baseline (Lighthouse, Core Web Vitals).
