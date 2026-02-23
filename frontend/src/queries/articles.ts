import { gql } from 'graphql-request';

export const ARTICLES_QUERY = gql`
  query GetArticles($first: Int!, $after: String) {
    posts(first: $first, after: $after, where: { orderby: { field: DATE, order: DESC } }) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        id
        title
        slug
        date
        excerpt
        content
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
        categories {
          nodes {
            name
            slug
          }
        }
        articleMeta {
          readTime
        }
      }
    }
  }
`;

export const ARTICLES_BY_CATEGORY = gql`
  query GetArticlesByCategory($categorySlug: String!, $first: Int!) {
    posts(
      first: $first
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
  }
`;

export const ARTICLE_BY_SLUG = gql`
  query GetArticleBySlug($slug: String!) {
    postBy(slug: $slug) {
      id
      title
      slug
      date
      excerpt
      content
      featuredImage {
        node {
          sourceUrl
          altText
        }
      }
      author {
        node {
          name
          description
          avatar {
            url
          }
        }
      }
      categories {
        nodes {
          name
          slug
        }
      }
      articleMeta {
        readTime
      }
    }
  }
`;

export const RELATED_ARTICLES = gql`
  query GetRelatedArticles($categorySlug: String!, $slug: String!, $first: Int!) {
    posts(
      first: $first
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
