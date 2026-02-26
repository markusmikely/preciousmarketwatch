import { HeroSection } from "./layouts/HeroSection";
import { RichTextSection } from "./layouts/RichTextSection";
import { TeamGrid } from "./layouts/TeamGrid";
import { PipelineSteps } from "./layouts/PipelineSteps";
import { StatsBar } from "./layouts/StatsBar";
import { TeamPerformanceStats } from "./layouts/TeamPerformanceStats";
import { OurValues } from "./layouts/OurValues";
import { CtaBlock } from "./layouts/CtaBlock";
import { LinkCards } from "./layouts/LinkCards";
import { DataSourcesList } from "./layouts/DataSourcesList";
import { FaqAccordion } from "./layouts/FaqAccordion";
import { ImageText } from "./layouts/ImageText";

export interface PageSection {
  __typename?: string;
  fieldGroupName?: string;
  [key: string]: unknown;
}

const LAYOUT_MAP: Record<string, React.ComponentType<{ section: PageSection; page?: { title?: string; breadcrumbLabel?: string | null } | null }>> = {
  hero: HeroSection,
  rich_text: RichTextSection,
  team_grid: TeamGrid,
  pipeline_steps: PipelineSteps,
  stats_bar: StatsBar,
  team_performance_stats: TeamPerformanceStats,
  our_values: OurValues,
  cta_block: CtaBlock,
  link_cards: LinkCards,
  data_sources: DataSourcesList,
  faq: FaqAccordion,
  image_text: ImageText,
};

/** Derive layout key from GraphQL __typename (ACF flexible content) */
function getLayoutKey(typename: string | undefined): string | null {
  if (!typename) return null;
  const lower = typename.toLowerCase();
  if (lower.includes("hero")) return "hero";
  if (lower.includes("richtext") || lower.includes("rich_text")) return "rich_text";
  if (lower.includes("teamgrid") || lower.includes("team_grid")) return "team_grid";
  if (lower.includes("pipelinesteps") || lower.includes("pipeline_steps")) return "pipeline_steps";
  if (lower.includes("statsbar") || lower.includes("stats_bar")) return "stats_bar";
  if (lower.includes("teamperformancestats") || lower.includes("team_performance_stats")) return "team_performance_stats";
  if (lower.includes("ourvalues") || lower.includes("our_values")) return "our_values";
  if (lower.includes("ctablock") || lower.includes("cta_block")) return "cta_block";
  if (lower.includes("linkcards") || lower.includes("link_cards")) return "link_cards";
  if (lower.includes("datasources") || lower.includes("data_sources")) return "data_sources";
  if (lower.includes("faq")) return "faq";
  if (lower.includes("imagetext") || lower.includes("image_text")) return "image_text";
  return null;
}

interface PageBuilderProps {
  sections: PageSection[] | null | undefined;
  page?: { title?: string; breadcrumbLabel?: string | null } | null;
}

export function PageBuilder({ sections, page }: PageBuilderProps) {
  if (!sections || sections.length === 0) return null;

  return (
    <>
      {sections.map((section, i) => {
        const layoutKey = getLayoutKey(section.__typename) ?? getLayoutKey(section.fieldGroupName ?? "");
        const Component = layoutKey ? LAYOUT_MAP[layoutKey] : null;
        if (!Component) return null;
        return <Component key={i} section={section} page={page} />;
      })}
    </>
  );
}
