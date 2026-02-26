import { gql } from "graphql-request";

export const GET_NEWS_ARTICLES_QUERY = gql`
  query GetNewsArticlesByCategory($first: Int = 20, $categorySlug: String!) {
    newsArticles(
      first: $first
      where: {
        taxQuery: {
          taxArray: [
            {
              taxonomy: PMW_NEWS_CATEGORY
              field: SLUG
              terms: [$categorySlug]
            }
          ]
        }
      }
    ) {
      nodes {
        id
        slug
        title
        excerpt
        date
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
        newsCategories {
          nodes {
            name
            slug
          }
        }
      }
    }
  }
`;

export const GET_NEWS_ARTICLES_SIMPLE_QUERY = gql`
  query GetNewsArticlesSimple($first: Int = 20) {
    newsArticles(first: $first) {
      nodes {
        id
        slug
        title
        excerpt
        date
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
        newsCategories {
          nodes {
            name
            slug
          }
        }
      }
    }
  }
`;

export const GET_NEWS_ARTICLE_BY_SLUG_QUERY = gql`
  query GetNewsArticleBySlug($slug: ID!) {
    newsArticle(id: $slug, idType: SLUG) {
      id
      slug
      title
      content
      excerpt
      date
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
      newsCategories {
        nodes {
          name
          slug
        }
      }
    }
  }
`;
