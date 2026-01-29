// frontend/src/utils/analytics.ts
declare global {
  interface Window {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    dataLayer: any[];
    gtag: (...args: unknown[]) => void;
  }
}

const GA_TRACKING_ID = process.env.GA_TRACKING_ID || '';

/**
 * Simplified Google Analytics loader.
 * Uses a standard stub to capture events before the library loads.
 */
export const loadGoogleAnalytics = () => {
  if (document.querySelector(`script[src*="gtag/js?id=${GA_TRACKING_ID}"]`)) {
    return;
  }

  // 1. Stub (Standard Google pattern)
  window.dataLayer = window.dataLayer || [];
  window.gtag = function () {
    // eslint-disable-next-line prefer-rest-params
    window.dataLayer.push(arguments);
  };

  // 2. Load script
  const script = document.createElement('script');
  script.async = true;
  script.src = `https://www.googletagmanager.com/gtag/js?id=${GA_TRACKING_ID}`;
  script.onload = () => {
    if (!GA_TRACKING_ID) return;
    window.gtag('js', new Date());
    window.gtag('config', GA_TRACKING_ID, {
      send_page_view: true,
    });
  };

  document.head.appendChild(script);
};

/**
 * Manually tracks a page view (Simplified for verification).
 */
export const trackPageView = (path: string) => {
  // Pass-through if gtag exists, otherwise it hits the stub
  if (typeof window.gtag === 'function') {
    window.gtag('event', 'page_view', {
      page_path: path,
    });
  }
};

export const hasAnalyticsConsent = (): boolean => {
  return localStorage.getItem('cookieConsent') === 'true';
};
