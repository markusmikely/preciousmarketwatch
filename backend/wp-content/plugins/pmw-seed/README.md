# PMW Seed Data Plugin

This plugin seeds initial content for Precious Market Watch (articles, dealers, categories, and pages).

## What It Creates

### Pages
- **Home** - Set as the site front page
- **Precious Metals** - Category page for precious metals content
- **Gemstones** - Category page for gemstones content

### Categories (Post Taxonomy)
- Precious Metals
- Gemstones
- Gold, Silver, Platinum, Palladium
- Diamonds, Rubies, Sapphires, Emeralds
- Market Analysis
- Investment

### Sample Articles (6 total)
Each article includes proper categorization and excerpt. Articles cover:
- Gold market analysis
- Silver industrial demand
- Platinum supply trends
- Diamond market impacts
- Sapphire investment
- Colored gemstone trends

### Sample Dealers (6 total)
Each dealer includes:
- Name and description
- Star rating
- Metal types (Gold, Silver, Platinum, etc.)
- Gemstone types (Diamonds, etc.)
- Featured flag

Dealers seeded:
- APMEX (4.8 stars) ⭐ Featured
- JM Bullion (4.7 stars) ⭐ Featured
- Blue Nile (4.5 stars) ⭐ Featured
- James Allen (4.6 stars)
- SD Bullion (4.4 stars)
- Augusta Precious Metals (4.7 stars)

## How to Use

### First Time Setup

1. **Activate the plugin** in WordPress admin
   - Go to Plugins → Installed Plugins
   - Find "PMW Seed Data"
   - Click "Activate"

2. **Plugin runs automatically** on activation
   - All content is created in the database
   - A success notice appears in WordPress admin
   - You can now deactivate the plugin

3. **Verify content was created**
   - Go to Posts → All Posts (you should see 6 articles)
   - Go to Dealers (custom post type) (you should see 6 dealers)
   - Go to Pages → All Pages (you should see Home, Precious Metals, Gemstones)

### Frontend Should Now Work

After seeding, your frontend GraphQL queries will return real data:

```graphql
{
  posts(first: 10) {
    nodes {
      title
      slug
      excerpt
    }
  }
  
  dealers(first: 10) {
    nodes {
      title
      metalTypes { nodes { name } }
      gemstoneTypes { nodes { name } }
    }
  }
}
```

## If You Need to Re-seed

You can activate the plugin again anytime to add/update content:

1. Go to Plugins → Installed Plugins
2. If deactivated, click "Activate" for PMW Seed Data
3. Plugin will re-run seeding (skips existing content)
4. Deactivate again when done

## What's NOT Created

This plugin does NOT create:
- Product catalog entries (you add these manually as needed)
- WooCommerce products (if using WooCommerce)
- Custom ACF field configurations (pmw-core plugin handles this)
- Required WordPress plugins (install via Plugins → Add New)

## Required Plugins

Make sure these are installed and active:
- ✅ Advanced Custom Fields (ACF)
- ✅ ACF Extended
- ✅ WP GraphQL
- ✅ WP GraphQL for ACF

If any are missing, the plugin will still work but some fields won't be populated.

## Troubleshooting

### Frontend Still Shows Blank Pages
1. Deactivate and reactivate the plugin
2. Check WordPress admin → Posts (should show articles)
3. Check WordPress admin → Dealers (should show dealers)
4. Check browser console for GraphQL errors
5. Check wp-admin → Settings → Reading (Front page should be "Home")

### GraphQL Returns 404
The GraphQL endpoint needs content. If blank after seeding:
1. Re-run the seed plugin by reactivating it
2. Check that WordPress permalinks are set (Settings → Permalinks → Save Changes)
3. Verify ACF plugin is installed

### Categories Not Appearing in Frontend
Categories are created automatically. If they don't appear:
1. Make sure the plugin fully activated
2. Go to Posts → Categories to verify they exist
3. Check that articles are assigned to categories

## Notes

- This plugin is safe to activate multiple times (it skips existing content)
- You can manually delete any seeded content (articles, dealers, pages) without breaking anything
- Once content is seeded, you can deactivate this plugin
- To add more articles/dealers, use WordPress admin or create them programmatically

## Questions?

Check the PMW Core plugin for custom post types and taxonomy definitions.
