// frontend/src/utils/analytics.ts
declare global {
  interface Window {
    dataLayer: unknown[][];
    gtag: (...args: unknown[]) => void;
    __ga_inited?: boolean;
  }
}

const GA_TRACKING_ID = 'G-2WGK87YBL6';

/**
 * Initializes Google Analytics if consent is granted.
 * Handles race conditions, avoids shadowing the global gtag,
 * and ensures idempotency across React renders.
 */
export const loadGoogleAnalytics = () => {
  // Guard against multiple initializations
  if (window.__ga_inited) return;

  // 1) Initialize dataLayer
  window.dataLayer = window.dataLayer || [];

  // 2) Initialize helper function ONLY if real GA library hasn't loaded yet
  if (typeof window.gtag !== 'function') {
    window.gtag = function () {
      // eslint-disable-next-line prefer-rest-params
      window.dataLayer.push(Array.from(arguments));
    };
  }

  const src = `https://www.googletagmanager.com/gtag/js?id=${GA_TRACKING_ID}`;
  const scriptExists = document.querySelector(`script[src="${src}"]`);

  const initDataLayer = () => {
    if (window.__ga_inited) return;
    window.__ga_inited = true;

    window.gtag('js', new Date());
    window.gtag('config', GA_TRACKING_ID, {
      debug_mode: process.env.NODE_ENV === 'development',
      send_page_view: false,
    });

    // Trigger the initial page view once GA is ready,
    // as we disabled automatic page views.
    trackPageView(window.location.pathname + window.location.search);

    console.log('✅ GA fully initialized (config + first pview)');
  };

  if (!scriptExists) {
    const script = document.createElement('script');
    script.async = true;
    script.src = src;
    script.onload = initDataLayer;
    document.head.appendChild(script);
  } else {
    // Pro-level refinement: if script exists, wait for its 'load' event
    // and attempt init immediately if it happens to be already loaded.
    const s = scriptExists as HTMLScriptElement;
    s.addEventListener('load', initDataLayer, { once: true });
    initDataLayer();
  }
};

/**
 * Manually tracks a page view. Useful for SPAs where route changes
 * don't trigger a full page reload.
 */
export const trackPageView = (path: string) => {
  if (!window.__ga_inited) return;
  window.gtag('event', 'page_view', {
    page_path: path,
  });
};

export const hasAnalyticsConsent = (): boolean => {
  return localStorage.getItem('cookieConsent') === 'true';
};
