import { gql } from 'graphql-request';

/**
 * Fetches articles and dealers for a metal investment page.
 * Articles filtered by category slug (e.g. "gold", "silver").
 * Dealers are filtered client-side by metalTypes.
 */
export const METAL_PAGE_QUERY = gql`
  query MetalPageData($categorySlug: String!, $articlesFirst: Int!, $dealersFirst: Int!) {
    posts(
      first: $articlesFirst
      where: { categoryName: $categorySlug, orderby: { field: DATE, order: DESC } }
    ) {
      nodes {
        id
        title
        slug
        date
        excerpt
        featuredImage {
          node {
            sourceUrl
            altText
          }
        }
        author {
          node {
            name
          }
        }
        categories {
          nodes {
            name
          }
        }
        articleMeta {
          readTime
        }
      }
    }
    dealers(first: $dealersFirst, where: { orderby: { field: DATE, order: DESC } }) {
      nodes {
        id
        title
        slug
        excerpt
        dealers {
          rating
          reviewLink
          shortDescription
          featured
          affiliateLink
          logo {
            sourceUrl
            altText
          }
        }
        dealerCategories {
          nodes {
            name
          }
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
`;
