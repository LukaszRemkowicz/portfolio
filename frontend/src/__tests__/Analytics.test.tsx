// frontend/src/__tests__/Analytics.test.tsx

describe('Google Analytics Utility', () => {
  const GA_ID = 'G-TEST-ID';
  let analytics: typeof import('../utils/analytics');

  beforeEach(() => {
    jest.resetModules();
    process.env.GA_TRACKING_ID = GA_ID;
    process.env.ENABLE_GA = 'true';

    // Clear DOM and global state
    document.head.innerHTML = '';
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    delete (window as any).gtag;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    delete (window as any).dataLayer;

    // Isolate module to pick up the env var
    jest.isolateModules(() => {
      analytics = require('../utils/analytics');
    });
  });

  test('loadGoogleAnalytics injects the gtag script into the document head', () => {
    // JSDOM (our test environment) does NOT load or execute external scripts by default.
    // No real network requests are sent to Google during this test.
    analytics.loadGoogleAnalytics();

    const script = document.querySelector('script');
    expect(script).toBeTruthy();

    const src = script?.getAttribute('src');
    expect(src).toContain('googletagmanager.com/gtag/js');
    expect(src).toContain(GA_ID);
    expect(script?.async).toBe(true);
  });

  test('loadGoogleAnalytics initializes dataLayer and gtag stub', () => {
    analytics.loadGoogleAnalytics();

    expect(window.dataLayer).toBeDefined();
    expect(typeof window.gtag).toBe('function');
  });

  test('trackPageView captures events in dataLayer via gtag stub', () => {
    analytics.loadGoogleAnalytics();
    const path = '/home';

    analytics.trackPageView(path);

    // Verify that the call was captured in dataLayer (since it's a stub)
    // The stub pushes the arguments object
    const lastEvent = Array.from(window.dataLayer[window.dataLayer.length - 1]);
    expect(lastEvent[0]).toBe('event');
    expect(lastEvent[1]).toBe('page_view');
    expect(lastEvent[2]).toEqual({ page_path: path });
  });

  test('loadGoogleAnalytics does not inject the script twice', () => {
    analytics.loadGoogleAnalytics();
    const initialScriptCount = document.querySelectorAll('script').length;

    analytics.loadGoogleAnalytics();
    expect(document.querySelectorAll('script').length).toBe(initialScriptCount);
  });

  test('gtag initialization logic runs on script load', () => {
    analytics.loadGoogleAnalytics();
    const script = document.querySelector('script') as HTMLScriptElement;

    // Manually trigger the onload event
    if (script.onload) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (script as any).onload();
    }

    // Verify that dataLayer has the 'js' and 'config' calls
    // Convert arguments objects to arrays for easier comparison
    const events = Array.from(window.dataLayer).map(arg =>
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      Array.from(arg as any)
    );
    expect(events.some(e => e[0] === 'js')).toBe(true);
    expect(events.some(e => e[0] === 'config' && e[1] === GA_ID)).toBe(true);
  });

  describe('Switch Logic', () => {
    test.each(['false', '0', 'no', 'undefined', ''])(
      'does not load GA when ENABLE_GA is "%s"',
      val => {
        jest.resetModules();
        process.env.ENABLE_GA = val;
        let localAnalytics: typeof import('../utils/analytics');
        jest.isolateModules(() => {
          localAnalytics = require('../utils/analytics');
        });

        localAnalytics!.loadGoogleAnalytics();
        expect(document.querySelector('script')).toBeNull();
        expect(window.dataLayer).toBeUndefined();
      }
    );

    test.each(['true', 'TRUE', 'True', 'TrUe'])(
      'enables GA when ENABLE_GA is "%s" (case-insensitive)',
      val => {
        jest.resetModules();
        process.env.ENABLE_GA = val;
        let localAnalytics: typeof import('../utils/analytics');
        jest.isolateModules(() => {
          localAnalytics = require('../utils/analytics');
        });

        localAnalytics!.loadGoogleAnalytics();
        expect(document.querySelector('script')).toBeTruthy();
      }
    );
  });
});
