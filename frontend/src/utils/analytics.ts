// frontend/src/utils/analytics.ts
export const loadGoogleAnalytics = () => {
  const GA_TRACKING_ID = 'G-2WGK87YBL6';

  // Create and inject the gtag.js script
  const script = document.createElement('script');
  script.async = true;
  script.src = `https://www.googletagmanager.com/gtag/js?id=${GA_TRACKING_ID}`;
  document.head.appendChild(script);

  // Initialize dataLayer and gtag
  window.dataLayer = window.dataLayer || [];
  function gtag(...args: unknown[]) {
    window.dataLayer.push(args);
  }
  gtag('js', new Date());
  gtag('config', GA_TRACKING_ID);

  console.log('✅ Google Analytics loaded');
};

export const hasAnalyticsConsent = (): boolean => {
  return localStorage.getItem('cookieConsent') === 'true';
};

// Extend Window interface for TypeScript
declare global {
  interface Window {
    dataLayer: unknown[];
  }
}
