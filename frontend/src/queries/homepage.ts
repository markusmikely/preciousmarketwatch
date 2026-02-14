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
          link
          uri
        }
      }
      newsletter {
        email
      }
    }
  }
  dealers {
    nodes {
      dealers {
        rating
        reviewLink
        shortDescription
        featured
        affiliateLink
        logo {
          uri
          title
        }
      }
    }
  }
  marketInsights {
    nodes {
      title
      slug
      date
    }
  }
}
`;

