import { gql } from "graphql-request";

/**
 * Fetch a WordPress page by slug with page_sections flexible content.
 * ACF layouts: hero, rich_text, team_grid, pipeline_steps, stats_bar,
 * cta_block, link_cards, data_sources, faq, image_text
 *
 * Note: Layout type names (e.g. Page_PageSections_Sections_HeroLayout) depend on
 * WPGraphQL ACF schema. Run GraphQL introspection if fragments fail.
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
          ... on Page_PageSections_Sections_HeroLayout {
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
          ... on Page_PageSections_Sections_RichTextLayout {
            fieldGroupName
            content
          }
          ... on Page_PageSections_Sections_TeamGridLayout {
            fieldGroupName
            heading
            showTiers
            filterStatus
          }
          ... on Page_PageSections_Sections_PipelineStepsLayout {
            fieldGroupName
            heading
            steps {
              label
              description
              agentRole
            }
          }
          ... on Page_PageSections_Sections_StatsBarLayout {
            fieldGroupName
            stats {
              label
              value
            }
          }
          ... on Page_PageSections_Sections_CtaBlockLayout {
            fieldGroupName
            heading
            body
            buttonLabel
            buttonUrl
          }
          ... on Page_PageSections_Sections_LinkCardsLayout {
            fieldGroupName
            cards {
              label
              description
              url
              icon
            }
          }
          ... on Page_PageSections_Sections_DataSourcesLayout {
            fieldGroupName
            items {
              name
              description
              url
            }
          }
          ... on Page_PageSections_Sections_FaqLayout {
            fieldGroupName
            items {
              question
              answer
            }
          }
          ... on Page_PageSections_Sections_ImageTextLayout {
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
