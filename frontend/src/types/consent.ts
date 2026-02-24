/**
 * Cookie consent categories (CONSENT-01 to 05).
 * Necessary is always true and not user-toggleable.
 */
export type ConsentCategory = "necessary" | "analytics" | "marketing" | "preferences";

export interface ConsentState {
  /** User has made a choice (accepted, rejected, or custom) */
  choice: "pending" | "accepted" | "rejected" | "custom";
  /** Per-category consent. necessary is always true. */
  analytics: boolean;
  marketing: boolean;
  preferences: boolean;
  /** When the user made this choice (ISO string) */
  updatedAt: string;
}

export const CONSENT_STORAGE_KEY = "pmw_consent";

export const defaultConsentState: ConsentState = {
  choice: "pending",
  analytics: false,
  marketing: false,
  preferences: false,
  updatedAt: "",
};

export function isAnalyticsGranted(state: ConsentState): boolean {
  return state.analytics === true;
}
