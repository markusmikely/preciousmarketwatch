import type { PageSection } from "../PageBuilder";

interface ImageTextSectionData {
  image?: { sourceUrl?: string | null; altText?: string | null } | null;
  content?: string | null;
  alignment?: string | null;
}

export function ImageText({ section }: { section: PageSection }) {
  const data = section as ImageTextSectionData;
  const alignRight = data.alignment === "right";

  return (
    <section className="py-16">
      <div className="container mx-auto px-4 lg:px-8">
        <div
          className={`grid lg:grid-cols-2 gap-12 items-center ${alignRight ? "lg:flex-row-reverse" : ""}`}
        >
          <div className={alignRight ? "lg:order-2" : ""}>
            {data.image?.sourceUrl && (
              <img
                src={data.image.sourceUrl}
                alt={data.image.altText ?? ""}
                className="rounded-xl w-full object-cover"
              />
            )}
          </div>
          <div className={alignRight ? "lg:order-1" : ""}>
            {data.content && (
              <div
                className="prose prose-lg prose-invert max-w-none text-silver"
                dangerouslySetInnerHTML={{ __html: data.content }}
              />
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
