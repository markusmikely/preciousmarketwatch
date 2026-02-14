import { LegalPageLayout } from "@/components/shared/LegalPageLayout";

export default function Privacy() {
  return (
    <LegalPageLayout
      title="Privacy Policy"
      subtitle="How we collect, use, and protect your personal information."
      lastUpdated="December 1, 2024"
    >
      <h2>Introduction</h2>
      <p>
        Precious Market Watch ("we," "our," or "us") respects your privacy and
        is committed to protecting your personal data. This privacy policy
        explains how we collect, use, disclose, and safeguard your information
        when you visit our website.
      </p>

      <h2>Information We Collect</h2>
      <h3>Information You Provide</h3>
      <ul>
        <li>
          <strong>Contact information:</strong> Name, email address when you
          subscribe to our newsletter or contact us
        </li>
        <li>
          <strong>Communication data:</strong> Messages you send us through our
          contact forms
        </li>
        <li>
          <strong>Account information:</strong> If you create an account,
          including your preferences and settings
        </li>
      </ul>

      <h3>Information Collected Automatically</h3>
      <ul>
        <li>
          <strong>Usage data:</strong> Pages visited, time spent on site,
          referral sources
        </li>
        <li>
          <strong>Device information:</strong> Browser type, operating system,
          device identifiers
        </li>
        <li>
          <strong>Location data:</strong> General geographic location based on
          IP address
        </li>
        <li>
          <strong>Cookies:</strong> See our Cookie Policy for details
        </li>
      </ul>

      <h2>How We Use Your Information</h2>
      <p>We use the information we collect to:</p>
      <ul>
        <li>Send you our newsletter and market updates (with your consent)</li>
        <li>Respond to your inquiries and provide customer support</li>
        <li>Improve our website and content</li>
        <li>Analyze usage patterns and optimize user experience</li>
        <li>Comply with legal obligations</li>
        <li>Prevent fraud and ensure security</li>
      </ul>

      <h2>Information Sharing</h2>
      <p>
        We do not sell your personal information. We may share your information
        with:
      </p>
      <ul>
        <li>
          <strong>Service providers:</strong> Companies that help us operate our
          website (hosting, analytics, email delivery)
        </li>
        <li>
          <strong>Legal requirements:</strong> When required by law or to
          protect our rights
        </li>
        <li>
          <strong>Business transfers:</strong> In connection with a merger,
          acquisition, or sale of assets
        </li>
      </ul>

      <h2>Your Rights</h2>
      <p>Depending on your location, you may have the right to:</p>
      <ul>
        <li>Access the personal information we hold about you</li>
        <li>Correct inaccurate information</li>
        <li>Delete your personal information</li>
        <li>Object to or restrict certain processing</li>
        <li>Data portability</li>
        <li>Withdraw consent at any time</li>
      </ul>

      <h2>Data Security</h2>
      <p>
        We implement appropriate technical and organizational measures to
        protect your personal information, including:
      </p>
      <ul>
        <li>Encryption of data in transit and at rest</li>
        <li>Regular security assessments</li>
        <li>Access controls and authentication</li>
        <li>Employee training on data protection</li>
      </ul>

      <h2>Data Retention</h2>
      <p>
        We retain your personal information only for as long as necessary to
        fulfill the purposes for which it was collected, including legal,
        accounting, or reporting requirements.
      </p>

      <h2>Third-Party Links</h2>
      <p>
        Our website may contain links to third-party sites, including affiliate
        partner sites. We are not responsible for the privacy practices of
        these sites. We encourage you to review their privacy policies.
      </p>

      <h2>Children's Privacy</h2>
      <p>
        Our website is not intended for children under 16 years of age. We do
        not knowingly collect personal information from children.
      </p>

      <h2>Changes to This Policy</h2>
      <p>
        We may update this privacy policy from time to time. We will notify you
        of any material changes by posting the new policy on this page and
        updating the "Last updated" date.
      </p>

      <h2>Contact Us</h2>
      <p>
        If you have questions about this privacy policy or our data practices,
        please contact us at{" "}
        <a href="mailto:privacy@preciousmarketwatch.com">
          privacy@preciousmarketwatch.com
        </a>
        .
      </p>
    </LegalPageLayout>
  );
}
