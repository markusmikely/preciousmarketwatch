import { gql } from "graphql-request";

/**
 * Fetch a WordPress page by slug with page_sections flexible content.
 * ACF layouts: hero, rich_text, team_grid, pipeline_steps, stats_bar,
 * cta_block, link_cards, data_sources, faq, image_text
 *
 * Supports both naming conventions:
 * - Fallback (no ACF PRO): Page_PageSections_Sections_HeroLayout etc.
 * - ACF PRO + WPGraphQL ACF: Page_PageSections_Sections_Hero etc.
 */
const SECTION_FRAGMENTS = `
  __typename
  fieldGroupName
  ... on Page_PageSections_Sections_HeroLayout { heading subheading backgroundImage { sourceUrl altText } ctaLabel ctaUrl }
  ... on Page_PageSections_Sections_Hero { heading subheading backgroundImage { sourceUrl altText } ctaLabel ctaUrl }
  ... on Page_PageSections_Sections_RichTextLayout { content }
  ... on Page_PageSections_Sections_RichText { content }
  ... on Page_PageSections_Sections_TeamGridLayout { heading showTiers filterStatus }
  ... on Page_PageSections_Sections_TeamGrid { heading showTiers filterStatus }
  ... on Page_PageSections_Sections_PipelineStepsLayout { heading steps { label description agentRole } }
  ... on Page_PageSections_Sections_PipelineSteps { heading steps { label description agentRole } }
  ... on Page_PageSections_Sections_StatsBarLayout { stats { label value } }
  ... on Page_PageSections_Sections_StatsBar { stats { label value } }
  ... on Page_PageSections_Sections_CtaBlockLayout { heading body buttonLabel buttonUrl }
  ... on Page_PageSections_Sections_CtaBlock { heading body buttonLabel buttonUrl }
  ... on Page_PageSections_Sections_LinkCardsLayout { cards { label description url icon } }
  ... on Page_PageSections_Sections_LinkCards { cards { label description url icon } }
  ... on Page_PageSections_Sections_DataSourcesLayout { items { name description url } }
  ... on Page_PageSections_Sections_DataSources { items { name description url } }
  ... on Page_PageSections_Sections_FaqLayout { items { question answer } }
  ... on Page_PageSections_Sections_Faq { items { question answer } }
  ... on Page_PageSections_Sections_ImageTextLayout { image { sourceUrl altText } content alignment }
  ... on Page_PageSections_Sections_ImageText { image { sourceUrl altText } content alignment }
`;

export const GET_PAGE_QUERY = gql`
  query GetPage($slug: ID!) {
    page(id: $slug, idType: URI) {
      id
      title
      slug
      pageSections {
        sections {
          ${SECTION_FRAGMENTS}
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
