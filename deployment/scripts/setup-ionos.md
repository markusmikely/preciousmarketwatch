# IONOS Bootstrap Guide — Precious Market Watch

One-time manual setup to get WordPress live on IONOS Web Hosting Plus.
After this, GitHub Actions handles all deployments.

---

## Prerequisites

- IONOS control panel access
- FTP client (Cyberduck, FileZilla, or similar)
- Your IONOS FTP credentials (from control panel → Hosting → FTP Accounts)

---

## Step 1 — Create the MySQL Database

1. Log in to [IONOS Control Panel](https://my.ionos.co.uk)
2. Go to **Hosting → MySQL Databases**
3. Click **Create Database**
4. Note down:
   - Database name (e.g. `db12345678`)
   - Database user
   - Database password
   - Database host (e.g. `db12345678.hosting-data.io`)

---

## Step 2 — Upload WordPress Core Files

Connect via FTP to your IONOS account and upload the `backend/` directory contents
into a `/wp/` subdirectory on the server.

**Target structure on IONOS:**
```
/ (web root)
├── index.html          ← FE build (already there)
├── assets/             ← FE assets (already there)
└── wp/                 ← WordPress lives here
    ├── wp-admin/
    ├── wp-content/
    ├── wp-includes/
    ├── wp-config.php
    └── index.php
```

**Upload via FTP:**
```bash
# Using lftp (or use Cyberduck/FileZilla GUI)
lftp -u YOUR_FTP_USER,YOUR_FTP_PASS YOUR_FTP_HOST
mkdir wp
mirror -R ./backend/ /wp/ --exclude=.env --exclude=backup/
```

> ⚠️ Do NOT upload the `.env` file — you'll create it directly on the server in Step 3.

---

## Step 3 — Create .env on the Server

Via IONOS File Manager (or FTP), create the file `/wp/.env` with your production values:

```env
DB_NAME=your_ionos_db_name
DB_USER=your_ionos_db_user
DB_PASSWORD=your_ionos_db_password
DB_HOST=your_ionos_db_host.hosting-data.io

WP_HOME=https://preciousmarketwatch.com
WP_SITEURL=https://preciousmarketwatch.com/wp
```

> 📝 Use the values from Step 1. `WP_HOME` is your site root (no `/wp`), `WP_SITEURL` is where WP core files live.

---

## Step 4 — Run WordPress Install Wizard

Visit: `https://preciousmarketwatch.com/wp/wp-admin/install.php`

Complete the wizard:
- **Site title:** Precious Market Watch
- **Username / Password:** Pick something strong — store in your password manager
- **Email:** Your admin email

---

## Step 5 — Activate Plugins

Log in to wp-admin at `https://preciousmarketwatch.com/wp/wp-admin`

Go to **Plugins → Installed Plugins** and activate:
- ✅ Advanced Custom Fields (ACF)
- ✅ ACF Extended
- ✅ WPGraphQL
- ✅ WPGraphQL for ACF

---

## Step 6 — Configure WPGraphQL

1. Go to **GraphQL → Settings** in wp-admin
2. Enable **GraphQL Endpoint** (default: `/graphql`)
3. Set **GraphQL IDE** to enabled (useful for testing)
4. Test your endpoint at: `https://preciousmarketwatch.com/wp/graphql`

---

## Step 7 — Configure GitHub Actions Secrets

In your GitHub repo → **Settings → Secrets and variables → Actions**, add:

| Secret | Value |
|---|---|
| `IONOS_FTP_HOST` | Your IONOS FTP host (e.g. `home123456789.1and1-data.host`) |
| `IONOS_FTP_USER` | Your IONOS FTP username |
| `IONOS_FTP_PASS` | Your IONOS FTP password |
| `METALS_DEV_API_KEY` | Your metals.dev API key |
| `WORDPRESS_API_URL` | `https://preciousmarketwatch.com/wp/graphql` |

---

## Step 8 — Verify the Pipeline

Push a small change to `master` (e.g. update a README) and check:
- GitHub Actions → should see both workflow runs
- FTP deploy logs should show files synced

---

## Done 🎉

WordPress is live. The GitHub Actions pipeline will handle all future deployments:
- Changes to `frontend/` → auto-deploys the FE build
- Changes to `backend/wp-content/` → auto-syncs plugins & themes
