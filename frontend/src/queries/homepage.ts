import { gql } from 'graphql-request';

export const HOMEPAGE_QUERY = gql`
  query HomepageData {
    homepage: page(id: "/", idType: URI) {
      title
      uri
      homepageSettings {
        hero {
          title
          subtitle
          backgroundImage {
            sourceUrl
          }
        }
        newsletter {
          email
        }
      }
    }
    dealers(first: 4, where: { orderby: { field: DATE, order: DESC } }) {
      nodes {
        id
        title
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
    posts(first: 4, where: { orderby: { field: DATE, order: DESC } }) {
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
  }
`;
