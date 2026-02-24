#!/usr/bin/env npx tsx
/**
 * METAL-03 — Daily Price Update
 *
 * Triggers the WordPress cron endpoint to upsert today's metal prices
 * and update the Market Data ACF options.
 *
 * Run: PMW_CRON_SECRET=xxx PMW_SITE_URL=https://www.preciousmarketwatch.com npm run daily-price-update
 * Or: Add to .env and run: npm run daily-price-update
 */

const CRON_SECRET = process.env.PMW_CRON_SECRET;
const SITE_URL = process.env.PMW_SITE_URL || process.env.VITE_WORDPRESS_API_URL || 'https://www.preciousmarketwatch.com/wp';

async function run() {
  if (!CRON_SECRET) {
    console.error('[dailyPriceUpdate] PMW_CRON_SECRET is required');
    process.exit(1);
  }

  const url = `${SITE_URL.replace(/\/$/, '')}/wp-json/pmw/v1/cron/price-update`;
  const timestamp = new Date().toISOString();

  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${CRON_SECRET}`,
        'Content-Type': 'application/json',
      },
    });

    const body = await res.json();

    if (!res.ok) {
      console.error(`[${timestamp}] FAILED HTTP ${res.status}:`, body?.message || body?.error || body);
      process.exit(1);
    }

    console.log(`[${timestamp}] OK`, JSON.stringify(body, null, 2));
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    console.error(`[${timestamp}] ERROR:`, msg);
    process.exit(1);
  }
}

run();
