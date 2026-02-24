import { LegalPageLayout } from "@/components/shared/LegalPageLayout";
import { Button } from "@/components/ui/button";
import { useConsent } from "@/contexts/ConsentContext";

export default function Cookies() {
  const { reopenBanner } = useConsent();
  return (
    <LegalPageLayout
      title="Cookie Policy"
      subtitle="Information about how we use cookies and similar technologies."
      lastUpdated="December 1, 2024"
    >
      <h2>What Are Cookies?</h2>
      <p>
        Cookies are small text files that are stored on your device when you
        visit a website. They help websites remember your preferences and
        understand how you use the site.
      </p>

      <h2>How We Use Cookies</h2>
      <p>
        Precious Market Watch uses cookies and similar technologies for the
        following purposes:
      </p>

      <h3>Essential Cookies</h3>
      <p>
        These cookies are necessary for the website to function properly. They
        enable basic features like page navigation and access to secure areas.
        The website cannot function properly without these cookies.
      </p>

      <h3>Analytics Cookies</h3>
      <p>
        We use analytics cookies to understand how visitors interact with our
        website. This helps us improve our content and user experience. These
        cookies collect information such as:
      </p>
      <ul>
        <li>Pages visited and time spent on each page</li>
        <li>How you arrived at our website (referral source)</li>
        <li>Your general geographic location</li>
        <li>Your device and browser type</li>
      </ul>

      <h3>Preference Cookies</h3>
      <p>
        These cookies remember your preferences and settings, such as:
      </p>
      <ul>
        <li>Language preferences</li>
        <li>Display settings</li>
        <li>Whether you've dismissed certain notifications</li>
      </ul>

      <h3>Marketing Cookies</h3>
      <p>
        These cookies track your activity across websites to deliver more
        relevant advertising. They may be set by our advertising partners.
      </p>

      <h3>Affiliate Cookies</h3>
      <p>
        When you click on affiliate links, our partners may set cookies to
        track your purchase. These cookies help us earn commission when you
        make a qualifying purchase. See our Affiliate Disclosure for more
        information.
      </p>

      <h2>Third-Party Cookies</h2>
      <p>
        We use services from third parties that may set their own cookies:
      </p>
      <ul>
        <li>
          <strong>Google Analytics (GA4):</strong> Website analytics and traffic
          analysis
        </li>
        <li>
          <strong>Microsoft Clarity:</strong> Session recordings and heatmaps to
          improve user experience
        </li>
        <li>
          <strong>Social media platforms:</strong> Share buttons and embedded
          content
        </li>
        <li>
          <strong>Affiliate networks:</strong> Tracking affiliate purchases
        </li>
        <li>
          <strong>Advertising networks:</strong> Personalized advertising
        </li>
      </ul>

      <h2>Managing Cookies</h2>
      <p>
        You can update your cookie preferences at any time using the button below. 
        This will reopen the cookie consent banner so you can accept or reject categories.
      </p>
      <p className="mt-2">
        <Button variant="outline" size="sm" onClick={reopenBanner}>
          Change cookie preferences
        </Button>
      </p>
      <p className="mt-4">
        You also have these options for managing cookies:
      </p>

      <h3>Browser Settings</h3>
      <p>
        Most web browsers allow you to control cookies through their settings.
        You can typically:
      </p>
      <ul>
        <li>View what cookies are stored on your device</li>
        <li>Delete all or specific cookies</li>
        <li>Block all cookies or cookies from specific sites</li>
        <li>Block third-party cookies</li>
        <li>Set preferences for certain types of cookies</li>
      </ul>

      <h3>Opt-Out Links</h3>
      <ul>
        <li>
          <strong>Google Analytics:</strong> Install the{" "}
          <a
            href="https://tools.google.com/dlpage/gaoptout"
            target="_blank"
            rel="noopener noreferrer"
          >
            Google Analytics Opt-out Browser Add-on
          </a>
        </li>
        <li>
          <strong>Advertising cookies:</strong> Visit{" "}
          <a
            href="https://www.aboutads.info/choices/"
            target="_blank"
            rel="noopener noreferrer"
          >
            aboutads.info/choices
          </a>{" "}
          or{" "}
          <a
            href="https://www.youronlinechoices.eu/"
            target="_blank"
            rel="noopener noreferrer"
          >
            youronlinechoices.eu
          </a>
        </li>
      </ul>

      <h2>Impact of Disabling Cookies</h2>
      <p>
        If you disable cookies, some features of our website may not function
        properly. Essential cookies are required for basic functionality.
      </p>

      <h2>Updates to This Policy</h2>
      <p>
        We may update this Cookie Policy from time to time to reflect changes
        in our practices or for legal reasons. We encourage you to review this
        policy periodically.
      </p>

      <h2>Contact Us</h2>
      <p>
        If you have questions about our use of cookies, please contact us at{" "}
        <a href="mailto:privacy@preciousmarketwatch.com">
          privacy@preciousmarketwatch.com
        </a>
        .
      </p>
    </LegalPageLayout>
  );
}
