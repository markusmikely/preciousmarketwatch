# Performance Baseline (ANALYTICS-05)

Establish and monitor a performance baseline for the Precious Market Watch frontend.

## Core Web Vitals

- **LCP (Largest Contentful Paint)**: Aim for &lt; 2.5s.
- **INP / FID (Interaction to Next Paint)**: Aim for &lt; 100ms.
- **CLS (Cumulative Layout Shift)**: Aim for &lt; 0.1.

## How to measure

1. **Chrome DevTools → Lighthouse**
   - Run in Incognito with "Simulated throttling" (or no throttling for local).
   - Record Performance score and Core Web Vitals.

2. **PageSpeed Insights**  
   - https://pagespeed.web.dev/  
   - Enter production URL for field and lab data.

3. **Google Search Console**
   - After GSC is set up, use **Experience → Core Web Vitals** for real-user data.

## Baseline checklist

- [ ] Run Lighthouse on key routes: `/`, `/precious-metals/gold`, `/gemstones`, `/privacy`.
- [ ] Note scores and LCP/INP/CLS; store in a spreadsheet or doc for comparison.
- [ ] Re-run after major frontend or hosting changes.
- [ ] Optional: add Lighthouse CI to the deploy pipeline (e.g. in `.github/workflows`) to fail or warn on regressions.

## Frontend optimizations already in place

- Vite build: code splitting, hashed asset names, minification.
- `_headers`: long cache for `/assets/*`, short cache for HTML.
- Lazy loading and efficient data fetching (React Query, GraphQL) help keep LCP and INP in check.

No code changes are required for ANALYTICS-05; this doc defines the process.
