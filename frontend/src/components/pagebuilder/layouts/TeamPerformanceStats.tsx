import type { PageSection } from "../PageBuilder";

interface Stat {
  label?: string | null;
  value?: string | null;
}

interface TeamPerformanceStatsSectionData {
  stats?: Stat[] | null;
}

export function TeamPerformanceStats({ section }: { section: PageSection }) {
  const data = section as TeamPerformanceStatsSectionData;
  const stats = data.stats ?? [];
  if (stats.length === 0) return null;

  return (
    <section className="py-16">
      <div className="container mx-auto px-4 lg:px-8">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          {stats.map((stat, i) => (
            <div key={i} className="text-center">
              <span className="font-display text-4xl font-bold text-primary block mb-2">
                {stat.value ?? ""}
              </span>
              <span className="text-muted-foreground">{stat.label ?? ""}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
