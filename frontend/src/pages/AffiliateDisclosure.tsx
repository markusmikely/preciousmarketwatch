import { LegalPageLayout } from "@/components/shared/LegalPageLayout";

export default function AffiliateDisclosure() {
  return (
    <LegalPageLayout
      title="Affiliate Disclosure"
      subtitle="Transparency about how we earn revenue through affiliate partnerships."
      lastUpdated="December 1, 2024"
    >
      <section>
        <h2 className="font-display text-2xl font-bold text-foreground mb-4">Our Commitment to Transparency</h2>
        <p>
          At Precious Market Watch, we believe in complete transparency with our
          readers. This disclosure explains how we earn revenue through affiliate
          marketing partnerships and how this affects (or doesn't affect) our
          content.
        </p>
      </section>

      <section>
        <h2 className="font-display text-2xl font-bold text-foreground mb-4">What Are Affiliate Links?</h2>
        <p>
          Affiliate links are special URLs that track when a visitor clicks
          through from our website to a partner's website. If you make a purchase
          after clicking one of our affiliate links, we may receive a commission
          from the partner at no additional cost to you.
        </p>
      </section>

      <section>
        <h2 className="font-display text-2xl font-bold text-foreground mb-4">How We Use Affiliate Links</h2>
        <p className="mb-4">
          Affiliate links appear throughout our website in various contexts:
        </p>
        <ul className="list-disc pl-6 space-y-2">
          <li>
            <strong className="text-foreground">Dealer recommendations:</strong> Links to precious metals
            dealers and jewelry retailers in our "Top Dealers" section
          </li>
          <li>
            <strong className="text-foreground">Product mentions:</strong> Links to specific products
            mentioned in our articles and guides
          </li>
          <li>
            <strong className="text-foreground">Comparison tables:</strong> Links in our dealer and product
            comparison content
          </li>
          <li>
            <strong className="text-foreground">Review articles:</strong> Links to products and services we
            review
          </li>
        </ul>
      </section>

      <section>
        <h2 className="font-display text-2xl font-bold text-foreground mb-4">Our Affiliate Partners</h2>
        <p className="mb-4">
          We partner with reputable companies in the precious metals and jewelry
          industry, including:
        </p>
        <ul className="list-disc pl-6 space-y-2">
          <li>Major online precious metals dealers (APMEX, JM Bullion, etc.)</li>
          <li>Diamond and jewelry retailers (Blue Nile, James Allen, etc.)</li>
          <li>Gemstone specialists and certified dealers</li>
          <li>Gold IRA and retirement account providers</li>
        </ul>
      </section>

      <section>
        <h2 className="font-display text-2xl font-bold text-foreground mb-4">Editorial Independence</h2>
        <p className="mb-4">
          <strong className="text-foreground">
            Our affiliate relationships never influence our editorial content or
            recommendations.
          </strong>
        </p>
        <ul className="list-disc pl-6 space-y-2">
          <li>We select partners based on quality, reputation, and value to our readers—not commission rates</li>
          <li>We include both affiliate and non-affiliate links in our content</li>
          <li>We disclose when a link is an affiliate link</li>
          <li>Our reviews and comparisons are based on objective criteria, not affiliate status</li>
          <li>We have declined partnerships with companies that don't meet our standards</li>
        </ul>
      </section>

      <section>
        <h2 className="font-display text-2xl font-bold text-foreground mb-4">How Commissions Work</h2>
        <p className="mb-4">When you make a purchase through our affiliate links:</p>
        <ul className="list-disc pl-6 space-y-2">
          <li><strong className="text-foreground">No extra cost:</strong> You pay the same price as if you visited the site directly</li>
          <li><strong className="text-foreground">Cookie duration:</strong> Most affiliate programs track your purchase within 24-90 days of clicking our link</li>
          <li><strong className="text-foreground">Commission rates:</strong> Vary by partner, typically 1-10% of the purchase price</li>
        </ul>
      </section>

      <section>
        <h2 className="font-display text-2xl font-bold text-foreground mb-4">Why We Use Affiliate Marketing</h2>
        <p className="mb-4">Affiliate revenue helps us:</p>
        <ul className="list-disc pl-6 space-y-2">
          <li>Maintain our website and infrastructure</li>
          <li>Pay our team of writers, analysts, and editors</li>
          <li>Invest in research and content development</li>
          <li>Keep our content free for all readers</li>
        </ul>
      </section>

      <section>
        <h2 className="font-display text-2xl font-bold text-foreground mb-4">How to Identify Affiliate Links</h2>
        <p className="mb-4">We strive to make affiliate links identifiable:</p>
        <ul className="list-disc pl-6 space-y-2">
          <li>Links to dealer websites in product recommendations are typically affiliate links</li>
          <li>"Visit Dealer" and similar call-to-action buttons link to affiliate partners</li>
          <li>Articles may include a disclosure notice when they contain affiliate links</li>
        </ul>
      </section>

      <section>
        <h2 className="font-display text-2xl font-bold text-foreground mb-4">Opting Out</h2>
        <p className="mb-4">If you prefer not to support us through affiliate links, you can:</p>
        <ul className="list-disc pl-6 space-y-2">
          <li>Navigate directly to the retailer's website</li>
          <li>Clear your cookies before making a purchase</li>
          <li>Use a private/incognito browser window</li>
        </ul>
      </section>

      <section>
        <h2 className="font-display text-2xl font-bold text-foreground mb-4">FTC Compliance</h2>
        <p>
          This disclosure is provided in compliance with the Federal Trade
          Commission's guidelines on affiliate marketing and endorsements. We are
          committed to honest, transparent communication with our readers.
        </p>
      </section>

      <section>
        <h2 className="font-display text-2xl font-bold text-foreground mb-4">Questions?</h2>
        <p>
          If you have questions about our affiliate relationships or this
          disclosure, please contact us at{" "}
          <a href="mailto:affiliate@preciousmarketwatch.com" className="text-primary hover:underline">
            affiliate@preciousmarketwatch.com
          </a>
          .
        </p>
      </section>
    </LegalPageLayout>
  );
}
