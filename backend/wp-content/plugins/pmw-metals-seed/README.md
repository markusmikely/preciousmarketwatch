# PMW Metals Seed

One-time migration plugin: creates `wp_metal_prices` table and loads historical precious metals data.

## Install

1. Activate the plugin (Tools → Plugins → PMW Metals Seed → Activate)
2. Or use **Tools → Metals Seed** and click "Seed / Re-run Now"

On activation, the table is created and gold data is loaded from FreeGoldAPI.

## Table: `wp_metal_prices`

| Column      | Type          | Description                    |
|-------------|---------------|--------------------------------|
| id          | BIGINT        | Primary key                    |
| metal       | VARCHAR(20)   | gold, silver, platinum, palladium |
| date        | DATE          | Price date                     |
| price_usd   | DECIMAL(12,4) | Price per troy oz USD          |
| price_gbp   | DECIMAL(12,4) | Optional GBP                   |
| source      | VARCHAR(100)  | API/source name                |
| granularity | VARCHAR(10)   | daily, monthly, etc.           |
| created_at  | TIMESTAMP     | Insert time                    |

Unique on `(metal, date)`. Idempotent: re-running skips existing rows.

## Data sources

- **Gold**: FreeGoldAPI (no key), 1990–present
- **Silver, Platinum, Palladium**: Optional — add to `wp-config.php`:

```php
define('PMW_SILVER_API_URL', 'https://your-api.com/silver.json');
define('PMW_PLATINUM_API_URL', 'https://your-api.com/platinum.json');
define('PMW_PALLADIUM_API_URL', 'https://your-api.com/palladium.json');
```

URL must return JSON: `[{date: "YYYY-MM-DD", price: number, source?: string}]`.

## Optional: FreeGoldAPI URL override

```php
define('PMW_FREEGOLDAPI_URL', 'https://freegoldapi.com/data/latest.json');
```
