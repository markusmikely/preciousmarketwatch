# PMW Migration Scripts

One-time migrations for metal price history. Uses the **WordPress database** (MySQL).

## Prerequisites

- Node.js 18+
- MySQL database (same as WordPress: `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`)
- Or set `DATABASE_URL=mysql://user:pass@host:3306/dbname`

## Setup

```bash
cd scripts
npm install
```

## Run Scripts

**Gold** (FreeGoldAPI — no API key):
```bash
DATABASE_URL="mysql://..." npm run load-gold
```

**Silver, Platinum, Palladium** (require API URLs that return `[{date, price, source?}]`):
```bash
DATABASE_URL="mysql://..." SILVER_API_URL="https://..." npm run load-silver
DATABASE_URL="mysql://..." PLATINUM_API_URL="https://..." npm run load-platinum
DATABASE_URL="mysql://..." PALLADIUM_API_URL="https://..." npm run load-palladium
```

**All metals** (silver/platinum/palladium skip if URLs not set):
```bash
DATABASE_URL="mysql://..." npm run load-all-metals
```

## GitHub Action

Workflow: `.github/workflows/load-metal-history.yml`

Trigger: **Actions → Load Metal Price History → Run workflow** (manual, one-time)

### Required secrets

| Secret | Required | Description |
|--------|----------|-------------|
| `DATABASE_URL` | Yes* | `mysql://user:pass@host:3306/dbname` |
| `DB_HOST` | Yes* | If not using DATABASE_URL |
| `DB_USER` | Yes* | |
| `DB_PASSWORD` | Yes* | |
| `DB_NAME` | Yes* | |
| `FREEGOLDAPI_URL` | No | Defaults to FreeGoldAPI |
| `SILVER_API_URL` | No | Skip silver if not set |
| `PLATINUM_API_URL` | No | Skip platinum if not set |
| `PALLADIUM_API_URL` | No | Skip palladium if not set |

*Use `DATABASE_URL` **or** `DB_HOST` + `DB_USER` + `DB_PASSWORD` + `DB_NAME`.
