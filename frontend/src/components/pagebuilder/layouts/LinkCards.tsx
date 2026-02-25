import { Link } from "react-router-dom";
import { FileText } from "lucide-react";
import * as LucideIcons from "lucide-react";
import type { PageSection } from "../PageBuilder";

interface Card {
  label?: string | null;
  description?: string | null;
  url?: string | null;
  icon?: string | null;
}

interface LinkCardsSectionData {
  cards?: Card[] | null;
}

function getIcon(name: string | null | undefined) {
  if (!name) return FileText;
  const camel = name.replace(/-/g, "_").replace(/(?:^|_)([a-z])/g, (_, c) => c.toUpperCase());
  const Icon = (LucideIcons as Record<string, React.ComponentType<{ className?: string }>>)[
    camel || "FileText"
  ];
  return Icon ?? FileText;
}

export function LinkCards({ section }: { section: PageSection }) {
  const data = section as LinkCardsSectionData;
  const cards = data.cards ?? [];
  if (cards.length === 0) return null;

  return (
    <section className="py-16">
      <div className="container mx-auto px-4 lg:px-8">
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {cards.map((card, i) => {
            const Icon = getIcon(card.icon);
            const href = card.url ?? "#";
            const isInternal = href.startsWith("/") && !href.startsWith("//");
            const cn = "block bg-card rounded-xl border border-border p-6 hover:border-primary/50 transition-colors";
            const content = (
              <>
                <div className="inline-flex p-3 rounded-lg bg-primary/10 text-primary mb-4">
                  <Icon className="h-6 w-6" />
                </div>
                <h3 className="font-display text-lg font-semibold text-foreground mb-2">{card.label ?? ""}</h3>
                {card.description && <p className="text-sm text-muted-foreground">{card.description}</p>}
              </>
            );
            return isInternal ? (
              <Link key={i} to={href} className={cn}>
                {content}
              </Link>
            ) : (
              <a key={i} href={href} className={cn} target="_blank" rel="noopener noreferrer">
                {content}
              </a>
            );
          })}
        </div>
      </div>
    </section>
  );
}
