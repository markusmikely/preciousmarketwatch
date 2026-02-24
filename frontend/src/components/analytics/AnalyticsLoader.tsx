import { useEffect, useRef } from "react";
import { useConsent } from "@/contexts/ConsentContext";

declare global {
  interface Window {
    dataLayer: unknown[];
    gtag: (...args: unknown[]) => void;
    clarity?: (method: string, ...args: unknown[]) => void;
  }
}

const GA_MEASUREMENT_ID = import.meta.env.VITE_GA4_MEASUREMENT_ID as string | undefined;
const CLARITY_PROJECT_ID = import.meta.env.VITE_CLARITY_PROJECT_ID as string | undefined;

function loadGA4() {
  if (!GA_MEASUREMENT_ID || typeof window.gtag !== "function") return;
  const script = document.createElement("script");
  script.async = true;
  script.src = `https://www.googletagmanager.com/gtag/js?id=${GA_MEASUREMENT_ID}`;
  document.head.appendChild(script);
  script.onload = () => {
    window.gtag("js", new Date());
    window.gtag("config", GA_MEASUREMENT_ID, { send_page_view: true });
  };
}

function loadClarity() {
  if (!CLARITY_PROJECT_ID || window.clarity) return;
  const script = document.createElement("script");
  script.async = true;
  script.innerHTML = `
    (function(c,l,a,r,i,t,y){c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);})(window,document,"clarity","script","${CLARITY_PROJECT_ID}");
  `;
  document.head.appendChild(script);
}

/**
 * ANALYTICS-01: GA4 gated by consent (Consent Mode v2).
 * ANALYTICS-02: Microsoft Clarity gated by consent.
 * When user grants analytics consent, we update gtag consent and load GA4 + Clarity.
 */
export function AnalyticsLoader() {
  const { analyticsGranted } = useConsent();
  const gaLoaded = useRef(false);
  const clarityLoaded = useRef(false);

  useEffect(() => {
    if (!analyticsGranted) return;

    // Update Consent Mode so GA uses cookies and full tracking
    if (typeof window.gtag === "function") {
      window.gtag("consent", "update", {
        analytics_storage: "granted",
        ad_storage: "granted",
        ad_user_data: "granted",
        ad_personalization: "granted",
      });
    }

    if (GA_MEASUREMENT_ID && !gaLoaded.current) {
      gaLoaded.current = true;
      loadGA4();
    }

    if (CLARITY_PROJECT_ID && !clarityLoaded.current) {
      clarityLoaded.current = true;
      loadClarity();
    }
  }, [analyticsGranted]);

  return null;
}
