# Backend - Precious Market Watch

Headless WordPress setup with GraphQL API for content management.

## 🏗️ Architecture
- **CMS**: WordPress 6.0+
- **GraphQL**: WPGraphQL plugin
- **Custom Post Types**: Articles, Market Data, AI Runs
- **Authentication**: JWT for API access
- **Caching**: Redis object cache

## 📦 Installation
```bash
cd backend
# Using Docker
docker-compose up -d

# Or manual setup
# 1. Download WordPress
# 2. Install in web server
# 3. Configure wp-config.php
```

## 🔧 WordPress Configuration

```php
// wp-config.php additions
define('WP_GRAPHQL_API_CACHE', true);
define('JWT_AUTH_SECRET_KEY', 'your-secret-key');
define('DISABLE_WP_CRON', true); // Use external cron
```

## 📡 GraphQL API Endpoints

```graphql
# Query articles
query GetArticles {
  articles {
    nodes {
      id
      title
      content
      aiGenerated
      marketData {
        goldPrice
        silverPrice
      }
    }
  }
}

# Mutations for AI content
mutation CreateArticle {
  createArticle(input: {
    title: "Gold Market Analysis"
    content: "..."
    status: PUBLISH
  }) {
    article {
      id
      link
    }
  }
}
```

## 🔌 Custom Plugins

```text
backend/wp-content/plugins/
├── precious-market-api/      # Custom REST endpoints
├── ai-content-importer/      # AI content ingestion
├── market-data-sync/         # Price data synchronization
└── social-media-auto-post/   # Auto-posting to social
```

[Continue with API documentation, custom endpoints, webhooks...]