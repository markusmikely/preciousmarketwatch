import { gql } from "graphql-request";

export const GET_ALL_TOOLS_QUERY = gql`
  query GetAllTools($first: Int = 50) {
    tools(first: $first) {
      nodes {
        id
        slug
        title
        excerpt
        featuredImage {
          node {
            sourceUrl
            altText
          }
        }
        toolStatus
        implementation
        embedCode
        reactComponent
        displayOrder
        isFeatured
        metalRelevance
        affiliatePartner
        affiliateCtaText
        affiliateCtaUrl
        showDisclaimer
        disclaimerText
        toolTypes {
          nodes {
            name
            slug
          }
        }
      }
    }
  }
`;

export const GET_TOOL_BY_SLUG_QUERY = gql`
  query GetTool($slug: ID!) {
    tool(id: $slug, idType: SLUG) {
      id
      slug
      title
      content
      excerpt
      featuredImage {
        node {
          sourceUrl
          altText
        }
      }
      toolStatus
      implementation
      embedCode
      reactComponent
      affiliatePartner
      affiliateCtaText
      affiliateCtaUrl
      affiliateCtaPosition
      showDisclaimer
      disclaimerText
      metalRelevance
      toolTypes {
        nodes {
          name
          slug
        }
      }
    }
  }
`;

export const GET_DEALER_COMPARISON_QUERY = gql`
  query GetDealerComparison {
    dealerComparison
  }
`;
