import type { PageSection } from "../PageBuilder";

interface Item {
  name?: string | null;
  description?: string | null;
  url?: string | null;
}

interface DataSourcesSectionData {
  items?: Item[] | null;
}

export function DataSourcesList({ section }: { section: PageSection }) {
  const data = section as DataSourcesSectionData;
  const items = data.items ?? [];
  if (items.length === 0) return null;

  return (
    <section className="py-16">
      <div className="container mx-auto px-4 lg:px-8">
        <h2 className="font-display text-2xl font-bold text-foreground mb-8">Data Sources</h2>
        <ul className="space-y-4 max-w-2xl">
          {items.map((item, i) => (
            <li key={i} className="border-l-2 border-primary/30 pl-4">
              {item.url ? (
                <a
                  href={item.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-medium text-foreground hover:text-primary"
                >
                  {item.name ?? "Source"}
                </a>
              ) : (
                <span className="font-medium text-foreground">{item.name ?? "Source"}</span>
              )}
              {item.description && (
                <p className="text-sm text-muted-foreground mt-1">{item.description}</p>
              )}
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
