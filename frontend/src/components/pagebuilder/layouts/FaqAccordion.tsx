import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import type { PageSection } from "../PageBuilder";

interface FaqItem {
  question?: string | null;
  answer?: string | null;
}

interface FaqSectionData {
  items?: FaqItem[] | null;
}

export function FaqAccordion({ section }: { section: PageSection }) {
  const data = section as FaqSectionData;
  const items = data.items ?? [];
  if (items.length === 0) return null;

  return (
    <section className="py-16 bg-muted/30">
      <div className="container mx-auto px-4 lg:px-8">
        <h2 className="font-display text-2xl font-bold text-foreground mb-8">Frequently Asked Questions</h2>
        <Accordion type="single" collapsible className="max-w-2xl">
          {items.map((item, i) => (
            <AccordionItem key={i} value={`faq-${i}`}>
              <AccordionTrigger className="text-left">{item.question ?? ""}</AccordionTrigger>
              <AccordionContent>
                <div className="prose prose-sm prose-invert max-w-none text-muted-foreground">
                  {item.answer ?? ""}
                </div>
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </div>
    </section>
  );
}
