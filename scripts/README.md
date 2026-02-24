# PMW Migration Scripts

**Note:** Metal price history loading is now handled by the **PMW Metals Seed** WordPress plugin. Install and activate it from the WordPress admin; it creates the `metal_prices` table and loads gold from FreeGoldAPI. No Node.js or GitHub Actions required.

The scripts below remain available for local/CI use if needed.

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
