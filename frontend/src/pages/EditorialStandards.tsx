import { LegalPageLayout } from "@/components/shared/LegalPageLayout";
import { CmsPage } from "@/components/cms/CmsPage";

function EditorialStandardsFallback() {
  return (
    <LegalPageLayout
      title="Editorial Standards"
      subtitle="Our commitment to accuracy, integrity, and transparency in all our content."
      lastUpdated="December 1, 2024"
    >
      <h2>Our Editorial Mission</h2>
      <p>
        Precious Market Watch is committed to providing accurate, unbiased, and
        actionable information about precious metals and gemstone markets. Our
        editorial team operates independently from our business operations,
        ensuring that our content serves the interests of our readers above all
        else.
      </p>

      <h2>Independence & Integrity</h2>
      <p>
        Our editorial content is never influenced by advertisers, affiliate
        partners, or any commercial relationships. We maintain strict separation
        between our editorial and business teams to ensure:
      </p>
      <ul>
        <li>
          <strong>No pay-for-play coverage:</strong> Companies cannot pay for
          favorable reviews or articles
        </li>
        <li>
          <strong>Unbiased recommendations:</strong> Our dealer and product
          recommendations are based solely on quality and value
        </li>
        <li>
          <strong>Transparent conflicts:</strong> Any potential conflicts of
          interest are disclosed prominently
        </li>
      </ul>

      <h2>Fact-Checking Process</h2>
      <p>
        Every piece of content published on Precious Market Watch undergoes
        rigorous fact-checking:
      </p>
      <ul>
        <li>
          <strong>Primary sources:</strong> We verify all market data from
          reputable exchanges and financial institutions
        </li>
        <li>
          <strong>Expert review:</strong> Technical content is reviewed by
          certified gemologists and precious metals experts
        </li>
        <li>
          <strong>Multiple verification:</strong> Key facts are confirmed
          through at least two independent sources
        </li>
        <li>
          <strong>Regular updates:</strong> Pricing and market data is updated
          in real-time or as frequently as possible
        </li>
      </ul>

      <h2>Corrections Policy</h2>
      <p>
        We take accuracy seriously and promptly correct any errors in our
        content:
      </p>
      <ul>
        <li>
          <strong>Immediate correction:</strong> Factual errors are corrected as
          soon as they are identified
        </li>
        <li>
          <strong>Transparent updates:</strong> Significant corrections include
          a note explaining what was changed and when
        </li>
        <li>
          <strong>Reader feedback:</strong> We encourage readers to report
          potential errors via our contact form
        </li>
      </ul>

      <h2>Affiliate Disclosure</h2>
      <p>
        Precious Market Watch participates in affiliate programs with select
        precious metals dealers and jewelry retailers. This means:
      </p>
      <ul>
        <li>
          We may earn a commission when you make a purchase through our links
        </li>
        <li>
          This commission comes at no additional cost to you
        </li>
        <li>
          Affiliate relationships never influence our editorial recommendations
        </li>
        <li>
          All affiliate links are clearly labeled
        </li>
      </ul>

      <h2>Content Categories</h2>
      <h3>News & Analysis</h3>
      <p>
        Objective reporting on market movements, industry developments, and
        economic factors affecting precious metals and gemstones.
      </p>

      <h3>Investment Guides</h3>
      <p>
        Educational content designed to help investors make informed decisions.
        These guides are based on established investment principles and expert
        insights.
      </p>

      <h3>Product Reviews</h3>
      <p>
        Honest assessments of investment products, dealers, and services. Our
        reviews are conducted independently and are not influenced by
        advertising relationships.
      </p>

      <h3>Sponsored Content</h3>
      <p>
        Any sponsored or paid content is clearly labeled as such. Sponsored
        content must meet our editorial standards and is reviewed for accuracy,
        but readers should understand it represents the views of the sponsor.
      </p>

      <h2>Expert Contributors</h2>
      <p>
        Our content is created and reviewed by qualified professionals:
      </p>
      <ul>
        <li>Certified gemologists (GIA, AGS)</li>
        <li>Precious metals market analysts</li>
        <li>Financial advisors and investment professionals</li>
        <li>Industry veterans with decades of experience</li>
      </ul>

      <h2>Contact Our Editorial Team</h2>
      <p>
        If you have questions about our editorial standards, wish to report an
        error, or have feedback on our content, please contact us at{" "}
        <a href="mailto:editorial@preciousmarketwatch.com">
          editorial@preciousmarketwatch.com
        </a>
        .
      </p>
    </LegalPageLayout>
  );
}

export default function EditorialStandards() {
  return (
    <CmsPage
      slug="editorial-standards"
      breadcrumbs={[{ label: "Home", href: "/" }, { label: "Editorial Standards" }]}
      fallback={<EditorialStandardsFallback />}
    />
  );
}
