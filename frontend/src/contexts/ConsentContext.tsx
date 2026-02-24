import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  useEffect,
  type ReactNode,
} from "react";
import {
  type ConsentState,
  CONSENT_STORAGE_KEY,
  defaultConsentState,
  isAnalyticsGranted,
} from "@/types/consent";

function loadStoredConsent(): ConsentState {
  try {
    const raw = localStorage.getItem(CONSENT_STORAGE_KEY);
    if (!raw) return defaultConsentState;
    const parsed = JSON.parse(raw) as Partial<ConsentState>;
    return {
      choice: parsed.choice ?? "pending",
      analytics: Boolean(parsed.analytics),
      marketing: Boolean(parsed.marketing),
      preferences: Boolean(parsed.preferences),
      updatedAt: parsed.updatedAt ?? "",
    };
  } catch {
    return defaultConsentState;
  }
}

function saveConsent(state: ConsentState): void {
  try {
    localStorage.setItem(CONSENT_STORAGE_KEY, JSON.stringify(state));
  } catch {
    // ignore
  }
}

interface ConsentContextValue {
  consent: ConsentState;
  acceptAll: () => void;
  rejectNonEssential: () => void;
  saveCustom: (options: { analytics: boolean; marketing: boolean; preferences: boolean }) => void;
  /** Re-open the cookie banner (e.g. from Cookie Policy page) */
  reopenBanner: () => void;
  analyticsGranted: boolean;
  /** True after consent has been read from localStorage */
  hydrated: boolean;
  /** True when the cookie banner should be visible (pending choice or reopened from Cookie Policy) */
  showBanner: boolean;
}

const ConsentContext = createContext<ConsentContextValue | null>(null);

export function ConsentProvider({ children }: { children: ReactNode }) {
  const [consent, setConsent] = useState<ConsentState>(defaultConsentState);
  const [hydrated, setHydrated] = useState(false);
  const [forceShowBanner, setForceShowBanner] = useState(false);

  useEffect(() => {
    setConsent(loadStoredConsent());
    setHydrated(true);
  }, []);

  const persist = useCallback((next: ConsentState) => {
    setConsent(next);
    saveConsent(next);
  }, []);

  const acceptAll = useCallback(() => {
    persist({
      choice: "accepted",
      analytics: true,
      marketing: true,
      preferences: true,
      updatedAt: new Date().toISOString(),
    });
  }, [persist]);

  const rejectNonEssential = useCallback(() => {
    persist({
      choice: "rejected",
      analytics: false,
      marketing: false,
      preferences: false,
      updatedAt: new Date().toISOString(),
    });
  }, [persist]);

  const saveCustom = useCallback(
    (options: { analytics: boolean; marketing: boolean; preferences: boolean }) => {
      persist({
        choice: "custom",
        analytics: options.analytics,
        marketing: options.marketing,
        preferences: options.preferences,
        updatedAt: new Date().toISOString(),
      });
      setForceShowBanner(false);
    },
    [persist]
  );

  const reopenBanner = useCallback(() => {
    setForceShowBanner(true);
  }, []);

  const acceptAllCb = useCallback(() => {
    acceptAll();
    setForceShowBanner(false);
  }, [acceptAll]);
  const rejectCb = useCallback(() => {
    rejectNonEssential();
    setForceShowBanner(false);
  }, [rejectNonEssential]);

  const value = useMemo<ConsentContextValue>(
    () => ({
      consent,
      acceptAll: acceptAllCb,
      rejectNonEssential: rejectCb,
      saveCustom,
      reopenBanner,
      analyticsGranted: isAnalyticsGranted(consent),
      hydrated,
      showBanner: consent.choice === "pending" || forceShowBanner,
    }),
    [consent, acceptAllCb, rejectCb, saveCustom, reopenBanner, hydrated, forceShowBanner]
  );

  return (
    <ConsentContext.Provider value={value}>
      {children}
    </ConsentContext.Provider>
  );
}

export function useConsent(): ConsentContextValue {
  const ctx = useContext(ConsentContext);
  if (!ctx) throw new Error("useConsent must be used within ConsentProvider");
  return ctx;
}

