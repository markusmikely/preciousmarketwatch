import type { PageSection } from "../PageBuilder";

interface RichTextSectionData {
  content?: string | null;
}

export function RichTextSection({ section }: { section: PageSection }) {
  const data = section as RichTextSectionData;
  if (!data.content) return null;

  return (
    <section className="py-16">
      <div className="container mx-auto px-4 lg:px-8">
        <div
          className="prose prose-lg prose-invert max-w-none text-silver"
          dangerouslySetInnerHTML={{ __html: data.content }}
        />
      </div>
    </section>
  );
}
