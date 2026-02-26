import { gql } from "graphql-request";

/**
 * Fetch a WordPress page by slug with page_sections flexible content.
 * Schema types: Page_Pagesections_PageSections_* (lowercase 's' in Pagesections)
 */
export const GET_PAGE_QUERY = gql`
  query GetPage($slug: ID!) {
    page(id: $slug, idType: URI) {
      id
      title
      slug
      pageSections {
        sections {
          __typename
          ... on Page_Pagesections_PageSections_Hero {
            fieldGroupName
            heading
            subheading
            backgroundImage {
              sourceUrl
              altText
            }
            ctaLabel
            ctaUrl
          }
          ... on Page_Pagesections_PageSections_RichText {
            fieldGroupName
            content
          }
          ... on Page_Pagesections_PageSections_TeamGrid {
            fieldGroupName
            heading
            showTiers
            filterStatus
            agents {
              id
              slug
              displayName
              title
              role
              tier
              bio
              personality
              quirks
              specialisms
              status
              eta
              displayOrder
              avatarImageUrl
              avatarVideoUrl
            }
          }
          ... on Page_Pagesections_PageSections_PipelineSteps {
            fieldGroupName
            heading
            steps {
              label
              description
              agentRole
            }
          }
          ... on Page_Pagesections_PageSections_StatsBar {
            fieldGroupName
            stats {
              label
              value
            }
          }
          ... on Page_Pagesections_PageSections_CtaBlock {
            fieldGroupName
            heading
            body
            buttonLabel
            buttonUrl
          }
          ... on Page_Pagesections_PageSections_LinkCards {
            fieldGroupName
            cards {
              label
              description
              url
              icon
            }
          }
          ... on Page_Pagesections_PageSections_DataSources {
            fieldGroupName
            items {
              name
              description
              url
            }
          }
          ... on Page_Pagesections_PageSections_Faq {
            fieldGroupName
            items {
              question
              answer
            }
          }
          ... on Page_Pagesections_PageSections_ImageText {
            fieldGroupName
            image {
              sourceUrl
              altText
            }
            content
            alignment
          }
        }
      }
    }
  }
`;

export const GET_SITE_SETTINGS_QUERY = gql`
  query GetSiteSettings {
    siteSettings {
      siteTagline
      navCtaLabel
      navCtaUrl
      footerAboutText
      footerColumns {
        label
        links {
          label
          url
        }
      }
      socialLinks {
        twitterUrl
        linkedinUrl
        youtubeUrl
      }
      cookieNoticeText
      analyticsNotice
    }
  }
`;
