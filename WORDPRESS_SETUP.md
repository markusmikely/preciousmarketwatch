# PMW WordPress Setup Guide

Complete guide to setting up the Precious Market Watch WordPress backend with all required plugins and configurations.

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│   React Frontend (localhost:5173)               │
│   - MarketInsights, TopDealers, Articles, etc   │
└────────────────┬────────────────────────────────┘
                 │ GraphQL Queries
                 ▼
┌─────────────────────────────────────────────────┐
│   WPGraphQL API Endpoint                        │
│   (https://preciousmarketwatch.com/wp/graphql)  │
└────────────────┬────────────────────────────────┘
                 │ Resolves via
                 ▼
┌─────────────────────────────────────────────────┐
│   WordPress Core (PHP/MySQL)                    │
│   - Posts, Pages, Custom Post Types             │
│   - ACF Custom Fields                           │
│   - Taxonomies (Categories, Metal Types, etc)   │
└─────────────────────────────────────────────────┘
```

## Prerequisites

- **WordPress 6.4+**
- **PHP 8.0+**
- **MySQL 5.7+**
- **WP-CLI** (optional but recommended)
- **Composer** (for plugin dependencies)

## Step 1: Install WordPress Core

If not already installed:

```bash
# Using WP-CLI
wp core download --version=6.4
wp config create --dbname=pmw --dbuser=root --dbpass=password
wp db create
wp core install --url=https://preciousmarketwatch.com --title="Precious Market Watch" --admin_user=admin --admin_password=YourSecurePassword --admin_email=admin@preciousmarketwatch.com

# Or use your hosting control panel (cPanel, Plesk, etc)
```

## Step 2: Install & Activate Required Plugins

### Via WordPress Admin
1. Go to **Plugins → Add New**
2. Search for each plugin and click **Install Now** then **Activate**

### Via WP-CLI (Faster)
```bash
# Install plugins
wp plugin install wp-graphql --activate
wp plugin install advanced-custom-fields --activate
wp plugin install wp-graphql-acf --activate
wp plugin install acf-extended --activate

# Verify they're active
wp plugin list --status=active
```

### Manual (Git/Folder)
```bash
# SSH into server
cd /path/to/wordpress/wp-content/plugins/

# Clone plugins
git clone https://github.com/wp-graphql/wp-graphql.git
git clone https://github.com/WordPress/advanced-custom-fields.git
git clone https://github.com/wp-graphql/wp-graphql-acf.git
git clone https://github.com/ElmStudio/ACF-Extended.git acf-extended

# Then activate in WordPress Admin
```

## Step 3: Install PMW Custom Plugins

The custom plugins are already in the repo:
- `/backend/wp-content/plugins/pmw-core/` - Custom post types, taxonomies, ACF fields
- `/backend/wp-content/plugins/pmw-seed/` - Sample data seeder

### Activate via WP-CLI
```bash
wp plugin activate pmw-core
wp plugin activate pmw-seed
```

### Or via WordPress Admin
Plugins → find "PMW Core" and "PMW Seed" → Click Activate

## Step 4: Run the Seed Plugin

### Option A: Via Admin Interface
1. Go to WordPress Admin Dashboard
2. You'll see a blue notice: "PMW Seed Plugin: Click the button below to seed sample data"
3. Click **"Seed Database Now"**
4. Wait for completion

### Option B: Via WP-CLI
```bash
wp eval 'do_action("pmw_seed_event")'
```

### Option C: Manual Trigger
```bash
curl "https://preciousmarketwatch.com/wp-admin/admin.php?pmw_seed=run"
```

## Step 5: Verify GraphQL Endpoint

### Test the GraphQL API
1. Navigate to: `https://preciousmarketwatch.com/wp/graphql`
2. You should see the GraphQL Playground

### Run a test query:
```graphql
query {
  posts(first: 5) {
    nodes {
      title
      slug
    }
  }
}
```

Should return your seeded articles.

## Step 6: Configure Frontend Environment

In `/frontend/.env`:

```env
VITE_WORDPRESS_API_URL=https://preciousmarketwatch.com/wp/graphql
VITE_IS_PRODUCTION=false
VITE_METALS_DEV_API_KEY=your_api_key_here
```

## Plugin Configuration Details

### WPGraphQL
- **What it does:** Exposes WordPress data via GraphQL API
- **Endpoint:** `/wp/graphql`
- **Status:** ✅ Auto-enabled when activated
- **No config needed** - works out of the box

### ACF (Advanced Custom Fields)
- **What it does:** Allows custom fields on posts, pages, dealers
- **Required fields for PMW:**
  - `read_time` (text) - on Posts
  - `dealers_rating` (number) - on Dealers
  - `dealers_featured` (true/false) - on Dealers
  - `dealers_affiliateLink` (text) - on Dealers
  - `hero` (flexible content) - on Homepage
  - `newsletter` (group) - on Homepage

**Note:** PMW Core plugin registers these fields automatically when activated.

### WPGraphQL for ACF
- **What it does:** Exposes ACF fields in GraphQL queries
- **Status:** ✅ Auto-enables ACF fields in GraphQL
- **No config needed** - works automatically once ACF and WPGraphQL are active

### PMW Core Plugin
- **What it does:**
  - Registers custom post types: `dealer`, `affiliate-product`
  - Registers custom taxonomies: `pmw-metal-type`, `pmw-gemstone-type`, `pmw-dealer-category`
  - Registers ACF field groups for each post type
  - Exposes everything to GraphQL

**Activation order matters:** PMW Core must be active BEFORE PMW Seed runs.

### PMW Seed Plugin
- **What it does:**
  - Creates sample articles with categories
  - Creates sample dealers with ratings
  - Sets up homepage
  - Creates default taxonomy terms
  - Activates all dependencies

**Use:** Run once on fresh installation. Can be deactivated after.

## Post Types & Fields

### Posts (WordPress Native)
```
Title: "Gold Reaches New Highs"
Content: Full article text
Excerpt: Short summary
Categories: [Gold, Precious Metals]
Featured Image: Hero image
ACF Fields:
  - read_time: "5 min read"
```

### Dealers (Custom Post Type)
```
Title: "APMEX"
Content: Full description
Excerpt: Short bio
ACF Fields:
  - dealers_rating: 4.8 (number)
  - dealers_featured: true (checkbox)
  - dealers_affiliateLink: "https://apmex.com?ref=pmw"
Metal Types: [Gold, Silver, Platinum]
Gemstone Types: [Diamonds]
```

## GraphQL Query Examples

### Fetch Articles by Category
```graphql
query GetGoldArticles {
  posts(where: { categoryName: "gold" }, first: 10) {
    nodes {
      id
      title
      slug
      date
      excerpt
      content
      categories {
        nodes {
          name
          slug
        }
      }
      featuredImage {
        node {
          sourceUrl
          altText
        }
      }
      author {
        node {
          name
          avatar {
            url
          }
        }
      }
      articleMeta {
        readTime
      }
    }
  }
}
```

### Fetch All Dealers
```graphql
query GetDealers {
  dealers(first: 50) {
    nodes {
      id
      title
      excerpt
      dealers {
        rating
        featured
        affiliateLink
      }
      metalTypes {
        nodes {
          name
        }
      }
      gemstoneTypes {
        nodes {
          name
        }
      }
    }
  }
}
```

## Content Management

### Creating Articles
1. Go to WordPress Admin → **Posts**
2. Click **Add New**
3. Fill in:
   - **Title**
   - **Content** (full article text)
   - **Excerpt** (short summary for cards)
   - **Featured Image** (hero image)
   - **Categories** (Gold, Silver, Gemstones, etc)
   - **Read Time** (ACF field) - "5 min read"
4. Click **Publish**

### Creating Dealers
1. Go to WordPress Admin → **Dealers**
2. Click **Add New**
3. Fill in:
   - **Title** (Dealer name)
   - **Description** (Full text about dealer)
   - **Rating** (ACF) - 0 to 5
   - **Featured** (ACF checkbox) - tick if featured
   - **Affiliate Link** (ACF) - Full URL with ref parameter
   - **Metal Types** - Select which metals they sell
   - **Gemstone Types** - Select which gemstones
4. Click **Publish**

## Troubleshooting

### Frontend shows white screen / no data

**Check 1: Is GraphQL endpoint accessible?**
```bash
curl -X POST https://preciousmarketwatch.com/wp/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ posts(first: 1) { nodes { title } } }"}'
```

Should return JSON with article data.

**Check 2: Are plugins active?**
```bash
wp plugin list --status=active | grep -E "(graphql|acf|pmw)"
```

Should show all of these as "active".

**Check 3: Does .htaccess block GraphQL?**
```bash
cat .htaccess
```

Should NOT have rules blocking `/wp/graphql`. The line should rewrite to index.php except for WP files:
```apache
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteCond %{REQUEST_URI} !^/wp-
RewriteRule . /index.php [L]
```

### Posts don't appear in GraphQL

**Check 1:** Post is published (not draft)
```bash
wp post list --post_type=post --post_status=publish
```

**Check 2:** ACF fields are set
```bash
wp post meta list <POST_ID>
```

Should show `read_time` field.

**Check 3:** Flush rewrite rules
```bash
wp rewrite flush
```

### ACF fields don't show in GraphQL

**Check:** Ensure ACF field group is set to "Show in GraphQL"
1. WordPress Admin → **ACF → Field Groups**
2. Edit each group
3. Scroll to bottom → **Settings**
4. Ensure "Show in GraphQL" is enabled
5. Save

The PMW Core plugin does this automatically, but double-check if you're adding custom fields.

## Database Backup & Restore

### Backup
```bash
# Using WP-CLI
wp db export /path/to/backup.sql

# Or native MySQL
mysqldump -u root -p pmw_database > /path/to/backup.sql
```

### Restore
```bash
# Using WP-CLI
wp db import /path/to/backup.sql

# Or native MySQL
mysql -u root -p pmw_database < /path/to/backup.sql
```

## Performance Optimization

### Enable Query Caching
Add to `wp-config.php`:
```php
// Enable query cache if using object caching
define( 'WP_CACHE', true );
```

### Optimize Database
```bash
wp db optimize
```

### Clear Rewrite Rules
```bash
wp rewrite flush
```

## Security Checklist

- [ ] Change default WordPress admin username
- [ ] Use strong admin password
- [ ] Disable file editing: `define( 'DISALLOW_FILE_EDIT', true );`
- [ ] Hide WordPress version: Remove version from headers
- [ ] Limit login attempts
- [ ] Use HTTPS everywhere
- [ ] Keep plugins updated
- [ ] Regular database backups

## Next Steps

1. **Create content**
   - Write articles in WordPress Admin
   - Add dealers with affiliate links
   - Add featured images to all posts

2. **Set up SEO**
   - Install Yoast SEO or Rank Math
   - Optimize article meta descriptions
   - Set up XML sitemaps

3. **Configure email**
   - Set up SMTP for WordPress notifications
   - Configure newsletter signup form

4. **Analytics**
   - Add Google Analytics 4
   - Set up tracking on affiliate links

5. **Go live**
   - Point domain to server
   - Test all pages load correctly
   - Verify GraphQL API works
   - Monitor error logs

---

**Setup Date:** February 23, 2026  
**WordPress Version:** 6.4+  
**PHP Version:** 8.0+  
**Last Updated:** February 23, 2026
