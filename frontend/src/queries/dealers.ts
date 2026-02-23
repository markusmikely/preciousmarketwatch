import { gql } from 'graphql-request';

export const DEALERS_QUERY = gql`
  query GetDealers($first: Int!, $after: String) {
    dealers(first: $first, after: $after, where: { orderby: { field: DATE, order: DESC } }) {
      pageInfo {
        hasNextPage
        endCursor
      }
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
            slug
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

export const DEALERS_BY_FEATURED = gql`
  query GetFeaturedDealers($first: Int!) {
    dealers(
      first: $first
      where: { orderby: { field: DATE, order: DESC } }
    ) {
      nodes {
        id
        title
        slug
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

export const DEALER_BY_SLUG = gql`
  query GetDealerBySlug($slug: String!) {
    dealerBy(slug: $slug) {
      id
      title
      slug
      content
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
`;
