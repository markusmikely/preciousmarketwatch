// UTM tracking parameters for affiliate links
export function addUtmParams(url: string, source: string = "preciousmarketwatch", medium: string = "affiliate", campaign: string = "dealer_referral"): string {
  const separator = url.includes("?") ? "&" : "?";
  return `${url}${separator}utm_source=${source}&utm_medium=${medium}&utm_campaign=${campaign}&utm_content=${encodeURIComponent(window.location.pathname)}`;
}

export function trackAffiliateClick(dealerName: string, category: string) {
  // Analytics tracking placeholder - integrate with your analytics provider
  console.log(`Affiliate click: ${dealerName} - ${category}`);
}
