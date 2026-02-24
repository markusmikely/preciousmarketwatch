import { useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { useConsent } from "@/contexts/ConsentContext";
import { ChevronDown, ChevronUp, Cookie } from "lucide-react";

export function CookieConsentBanner() {
  const { consent, acceptAll, rejectNonEssential, saveCustom, hydrated, showBanner } = useConsent();
  const [customOpen, setCustomOpen] = useState(false);
  const [customAnalytics, setCustomAnalytics] = useState(consent.analytics);
  const [customMarketing, setCustomMarketing] = useState(consent.marketing);
  const [customPreferences, setCustomPreferences] = useState(consent.preferences);

  if (!hydrated || !showBanner) return null;

  const handleSaveCustom = () => {
    saveCustom({
      analytics: customAnalytics,
      marketing: customMarketing,
      preferences: customPreferences,
    });
    setCustomOpen(false);
  };

  return (
    <div
      role="dialog"
      aria-label="Cookie consent"
      className="fixed bottom-0 left-0 right-0 z-50 border-t border-silver/20 bg-navy p-4 shadow-lg sm:p-6"
    >
      <div className="container mx-auto flex max-w-4xl flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex gap-3 sm:gap-4">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/20 text-primary">
            <Cookie className="h-5 w-5" />
          </div>
          <div>
            <h2 className="font-display text-lg font-semibold text-silver-light">
              We value your privacy
            </h2>
            <p className="mt-1 text-sm text-silver">
              We use cookies for essential site function, analytics, and preferences. You can choose
              which categories to allow. See our{" "}
              <Link to="/cookies" className="underline hover:text-primary">
                Cookie Policy
              </Link>
              .
            </p>
          </div>
        </div>

        <div className="flex flex-col gap-2 sm:shrink-0 sm:items-end">
          <div className="flex flex-wrap gap-2">
            <Button
              variant="default"
              size="sm"
              onClick={acceptAll}
              className="bg-primary text-primary-foreground"
            >
              Accept all
            </Button>
            <Button variant="outline" size="sm" onClick={rejectNonEssential}>
              Reject non-essential
            </Button>
          </div>

          <Collapsible open={customOpen} onOpenChange={setCustomOpen}>
            <CollapsibleTrigger asChild>
              <Button variant="ghost" size="sm" className="text-silver hover:text-silver-light">
                {customOpen ? (
                  <>
                    <ChevronUp className="mr-1 h-4 w-4" />
                    Hide options
                  </>
                ) : (
                  <>
                    <ChevronDown className="mr-1 h-4 w-4" />
                    Customize
                  </>
                )}
              </Button>
            </CollapsibleTrigger>
            <CollapsibleContent>
              <div className="mt-3 flex flex-col gap-2 rounded-lg border border-silver/20 bg-navy-light/50 p-3 text-sm">
                <label className="flex cursor-pointer items-center gap-2 text-silver-light">
                  <Checkbox
                    checked={customAnalytics}
                    onCheckedChange={(v) => setCustomAnalytics(Boolean(v))}
                  />
                  Analytics (e.g. Google Analytics, Clarity)
                </label>
                <label className="flex cursor-pointer items-center gap-2 text-silver-light">
                  <Checkbox
                    checked={customMarketing}
                    onCheckedChange={(v) => setCustomMarketing(Boolean(v))}
                  />
                  Marketing
                </label>
                <label className="flex cursor-pointer items-center gap-2 text-silver-light">
                  <Checkbox
                    checked={customPreferences}
                    onCheckedChange={(v) => setCustomPreferences(Boolean(v))}
                  />
                  Preferences
                </label>
                <Button variant="secondary" size="sm" onClick={handleSaveCustom} className="mt-2">
                  Save choices
                </Button>
              </div>
            </CollapsibleContent>
          </Collapsible>
        </div>
      </div>
    </div>
  );
}
