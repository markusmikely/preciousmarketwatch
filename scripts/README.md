# PMW Migration Scripts

**Note:** Metal price history loading is handled by the **PMW Metals Seed** WordPress plugin. Activate it to create the table and load all four metals (gold: FreeGoldAPI; silver/platinum/palladium: Metals.dev).

## Daily Price Update

Triggers the WordPress cron endpoint to upsert today's prices:

```bash
PMW_CRON_SECRET=xxx PMW_SITE_URL=https://www.preciousmarketwatch.com/wp npm run daily-price-update
```

Or run via GitHub Actions (schedule: 06:00 UTC). Required secrets: `PMW_CRON_SECRET`, `PMW_SITE_URL`.

## Prerequisites

- Node.js 18+
- MySQL database (same as WordPress)

## Run Scripts (optional)

```bash
cd scripts
npm install
DATABASE_URL="mysql://user:pass@host:3306/dbname" npm run load-gold
# Or: npm run load-all-metals
```
