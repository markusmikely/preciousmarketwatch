import * as LucideIcons from "lucide-react";
import { Shield } from "lucide-react";
import type { PageSection } from "../PageBuilder";

interface Value {
  icon?: string | null;
  title?: string | null;
  description?: string | null;
}

interface OurValuesSectionData {
  heading?: string | null;
  values?: Value[] | null;
}

function getIcon(name: string | null | undefined) {
  if (!name) return Shield;
  const camel = name
    .replace(/-/g, "_")
    .replace(/(?:^|_)([a-z])/g, (_, c: string) => c.toUpperCase());
  const Icon = (LucideIcons as Record<string, React.ComponentType<{ className?: string }>>)[
    camel || "Shield"
  ];
  return Icon ?? Shield;
}

export function OurValues({ section }: { section: PageSection }) {
  const data = section as OurValuesSectionData;
  const values = data.values ?? [];
  const heading = data.heading ?? "Our Values";
  if (values.length === 0) return null;

  return (
    <section className="py-16">
      <div className="container mx-auto px-4 lg:px-8">
        <h2 className="font-display text-2xl font-bold text-foreground mb-8 text-center">
          {heading}
        </h2>
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          {values.map((value, i) => {
            const Icon = getIcon(value.icon);
            return (
              <div
                key={i}
                className="bg-card rounded-xl border border-border p-6 text-center"
              >
                <div className="inline-flex p-4 rounded-full bg-primary/10 text-primary mb-4">
                  <Icon className="h-6 w-6" />
                </div>
                <h3 className="font-display text-lg font-semibold text-foreground mb-2">
                  {value.title ?? ""}
                </h3>
                <p className="text-sm text-muted-foreground">{value.description ?? ""}</p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
