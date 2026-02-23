# GraphQL Integration for PMW Frontend

## Overview
Integrated GraphQL queries and hooks to fetch dynamic content from WordPress for all main content pages.

## New Files Created

### Queries (`/src/queries/`)
- **`articles.ts`** - GraphQL queries for articles
  - `ARTICLES_QUERY` - Fetch paginated articles
  - `ARTICLES_BY_CATEGORY` - Filter articles by category
  - `ARTICLE_BY_SLUG` - Fetch single article for detail view
  - `RELATED_ARTICLES` - Get related articles by category

- **`dealers.ts`** - GraphQL queries for dealers
  - `DEALERS_QUERY` - Fetch paginated dealers
  - `DEALERS_BY_FEATURED` - Get featured dealers
  - `DEALER_BY_SLUG` - Fetch single dealer details

### Hooks (`/src/hooks/`)
- **`useGraphQL.ts`** - Reusable hook for GraphQL queries
  - `useGraphQL()` - Main hook with loading/error states
  - `useGraphQLQuery()` - Simplified variant

### Components (`/src/components/`)
- **`shared/DataFetchStateHandler.tsx`** - Shared component for handling:
  - Loading states with spinner
  - Error states with retry button
  - Graceful fallback rendering

## Updated Pages

### ✅ MarketInsights.tsx
- Fetches articles from GraphQL with pagination
- Search and filter by category
- Fallback to hardcoded articles if GraphQL fails
- Loading indicators and error handling
- Shows featured article + related articles grid

### ✅ TopDealers.tsx
- Fetches dealers from GraphQL
- Filter by specialty/category
- Featured dealers section
- Error handling with retry
- Trust badges section

### ✅ Article.tsx (Dynamic Single Article)
- Fetches article by slug from GraphQL
- Displays full article content
- Fetches related articles automatically
- Author bio from WordPress
- Sidebar with featured dealer
- Newsletter signup
- Share buttons

## Remaining Pages to Integrate

These pages can use similar patterns. Currently using fallback/mock data:

### Category Pages (Medium Priority)
- **PreciousMetals.tsx** - Use `ARTICLES_BY_CATEGORY` with categorySlug="precious-metals"
- **Gemstones.tsx** - Use `ARTICLES_BY_CATEGORY` with categorySlug="gemstones"

### Metal-Specific Pages (Medium Priority)
- **Gold/Silver/Platinum/Palladium** - Use `ARTICLES_BY_CATEGORY` with metal name
- Filter to show articles related to that specific metal

### Gemstone-Specific Pages (Medium Priority)
- **Diamonds/Rubies/Sapphires/Emeralds** - Use `ARTICLES_BY_CATEGORY` with gemstone name
- Filter to show articles related to that specific stone

### Static Pages (No GraphQL Needed)
- About, Contact, Privacy, Terms, EditorialStandards, AffiliateDisclosure, Cookies, JewelryInvestment
- These can stay as-is with fallback/mock content

## Data Flow Pattern

```
Page Component
  ↓
useGraphQL Hook (fetch data, handle loading/errors)
  ↓
DataFetchStateHandler (UI for loading/error states)
  ↓
Transform data (map WordPress fields to component props)
  ↓
Render components with fallback data if needed
```

## Error Handling Strategy

1. **Network Error** → Show error message with "Try Again" button
2. **Invalid Data** → Use fallback/mock data silently
3. **Missing Fields** → Provide sensible defaults (empty strings, placeholders)
4. **Graceful Degradation** → Page shows something even if all APIs fail

## TypeScript Types

Added proper typing for GraphQL responses:
- `WpArticle` - WordPress article structure
- `WpDealer` - WordPress dealer structure
- `UseGraphQLResult` - Hook return type

## Testing Checklist

- [ ] MarketInsights loads articles from GraphQL
- [ ] Search and filter work correctly
- [ ] TopDealers page displays dealers
- [ ] Individual articles load by slug
- [ ] Related articles fetch correctly
- [ ] Error states show proper messages
- [ ] Fallback content displays if GraphQL fails
- [ ] Category filters work on category pages
- [ ] Performance is acceptable (load times)

## Next Steps

1. **Phase 1 (Done)**
   - ✅ Homepage (already integrated)
   - ✅ MarketInsights (integrated)
   - ✅ TopDealers (integrated)
   - ✅ Article (integrated)

2. **Phase 2 (Ready to implement)**
   - PreciousMetals/Gemstones category pages
   - Individual metal/gemstone pages
   - Product catalog if needed

3. **Phase 3 (Future)**
   - SEO optimization (structured data)
   - Caching strategy
   - Pagination for large result sets
   - Advanced filtering/sorting

## Environment Variables

Make sure WordPress GraphQL is enabled and endpoint is set:

```env
VITE_WORDPRESS_API_URL=https://www.preciousmarketwatch.com/wp/graphql
```

## Notes

- All queries include proper error boundaries
- Components gracefully degrade if data is missing
- Fallback data ensures pages always render
- Search/filter works on client side after fetch
- Related articles auto-fetch based on category
