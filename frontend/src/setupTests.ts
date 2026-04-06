import '@testing-library/jest-dom';
import { TextEncoder, TextDecoder } from 'util';

Object.defineProperty(global, 'TextEncoder', {
  value: TextEncoder,
});

Object.defineProperty(global, 'TextDecoder', {
  value: TextDecoder,
});

const mockProjectOwner = process.env.PROJECT_OWNER || 'Portfolio Owner';

window.__PUBLIC_ENV__ = {
  API_URL:
    process.env.API_URL || process.env.VITE_API_URL || 'http://localhost:8000',
  GA_TRACKING_ID: process.env.VITE_GA_TRACKING_ID || 'G-TEST',
  PROJECT_OWNER: mockProjectOwner,
  SITE_DOMAIN: process.env.SITE_DOMAIN || 'portfolio.local',
};

// Ensure API_URL is defined for tests that directly use process.env (legacy paths)
// Main env access is now via import.meta.env (shimmed in jest.config.js globals)

// Mock window.matchMedia for components that use it (e.g., animations, responsive hooks)
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  }),
});

// Mock crypto.randomUUID for JSDOM
Object.defineProperty(window, 'crypto', {
  value: {
    randomUUID: () => 'test-uuid-' + Math.random().toString(36).substring(2, 9),
  },
});

// Suppress React Router v6 future flag warnings in tests
// This can be done by configuring the router in individual tests or globally if using Data Router,
// but for standard BrowserRouter usage in tests, we can suppress the warning via console mock or by setting a global flag if supported.
// Actually, the most reliable way in v6 is to mock the console or (better) ignore these specific warnings.
const originalWarn = console.warn;
console.warn = (...args) => {
  if (args[0] && typeof args[0] === 'string') {
    if (
      args[0].includes('React Router Future Flag Warning') ||
      args[0].includes('Profile not found, using fallbacks') ||
      args[0].includes('Background image not found')
    ) {
      return;
    }
  }
  originalWarn(...args);
};

// Mock react-helmet-async
jest.mock('react-helmet-async', () => {
  return {
    Helmet: ({ children }: { children?: React.ReactNode }) =>
      children as React.ReactElement | null,
    HelmetProvider: ({ children }: { children?: React.ReactNode }) =>
      children as React.ReactElement | null,
  };
});

// Mock react-i18next
jest.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const testLang =
        (globalThis as { __TEST_I18N_LANGUAGE__?: string })
          .__TEST_I18N_LANGUAGE__ || 'en';
      const translations: Record<string, string> = {
        'nav.home': 'Home',
        'nav.astrophotography': 'Astrophotography',
        'nav.shop': 'Shop',
        'nav.programming': 'Programming',
        'nav.about': 'About',
        'nav.contact': 'Contact',
        'common.en': 'EN',
        'common.pl': 'PL',
        'common.privacyPolicy': 'Privacy Policy',
        'common.cookieSettings': 'Cookie Settings',
        'common.decline': 'Decline',
        'common.accept': 'Accept',
        'common.gallery': 'Gallery',
        'common.gallerySubtitle':
          'Filter by category or explore images using the tags below.',
        'common.exploreTags': 'Explore Tags',
        'common.categories': 'Categories',
        'common.loadMoreGallery': 'Load more',
        'common.loadingMore': 'Loading more...',
        'common.scanning': 'Scanning deep space sectors...',
        'common.syncCosmos': 'Synchronizing with the Cosmos',
        'common.compiling': 'Compiling projects...',
        'common.noImagesFound': 'No images found for this filter.',
        'common.noImagesHint':
          'Try selecting a different category or tag to see more images.',
        'footer.rights': `${mockProjectOwner} © 2026`,
        'about.title': 'Beyond the Atmosphere.',
        'about.defaultBio':
          'Astrophotography is a technical dance with physics. My journey involves thousands of light frames, hours of integration, and a dedication to revealing what remains invisible to the naked eye.',
        'about.siteQuality': 'Site Quality',
        'about.primaryOptics': 'Primary Optics',
        'about.totalTimeSpent': 'Total time spent',
        'about.totalTimeSpentTooltip':
          'This is the total integration time of the images on this website',
        'cookie.title': 'Cookie Consent',
        'cookie.description':
          'We use cookies to enhance your experience, analyze traffic, and personalize your journey through the cosmos. By using our site, you agree to our',
        'travel.adventureDate': 'ADVENTURE DATE',
        'travel.exploringCosmic': 'Exploring the cosmic wonders of',
        'programming.title': 'Project Archive',
        'programming.subtitle':
          'A collection of software engineering projects, from microservices to creative frontend experiments.',
        'programming.source': 'Source',
        'programming.liveDemo': 'Live Demo',
        'programming.empty':
          'The archives appear to be empty. Check back later for new transmissions.',
        'shop.metaTitle': 'Shop',
        'shop.metaDescription':
          'A preview of future shop collections, formats, and limited-edition astrophotography releases.',
        'shop.kicker': 'Placeholder storefront',
        'shop.title': 'Collect the night sky in print.',
        'shop.subtitle':
          'This static preview page maps out how the future shop can present limited editions, print formats, and educational releases without needing live commerce data yet.',
        'shop.primaryCta': 'Browse placeholders',
        'shop.secondaryCta': 'Request a custom print',
        'shop.placeholderBadge': 'Placeholder',
        'shop.productEyebrow': 'Curated release',
        'shop.viewProduct': 'View product',
        'shop.loading': 'Loading catalog...',
        'shop.error': 'Catalog is temporarily out of orbit.',
        'shop.empty': 'No releases are available yet.',
        'categories.Landscape': 'Landscape',
        'categories.Deep Sky': 'Deep Sky',
        'categories.Startrails': 'Startrails',
        'categories.Solar System': 'Solar System',
        'categories.Milky Way': 'Milky Way',
        'categories.Northern Lights': 'Northern Lights',
        'categories.Galaxy': 'Galaxy',
        'categories.Nebula': 'Nebula',
        'categories.Star': 'Star',
        'common.tags': 'Tags',
        'common.allTags': 'All Tags',
        'privacy.title': 'Privacy Policy & Cookie Notice',
        'privacy.lastUpdated': 'Last updated: January 29, 2026',
        'privacy.introduction.title': 'Introduction',
        'privacy.introduction.body':
          'This website is a personal portfolio showcasing my astrophotography, travel photography, and software development work. I respect your privacy and am committed to being transparent about how this site collects and uses data.',
        'privacy.dataCollected.title': 'What Data We Collect',
        'privacy.dataCollected.intro':
          'This website uses Google Analytics to understand how visitors interact with the site. The following data is collected:',
        'privacy.dataCollected.items.anonymous.label': 'Anonymous usage data:',
        'privacy.dataCollected.items.anonymous.value':
          'Pages viewed, time spent on pages, browser type, device type',
        'privacy.dataCollected.items.geo.label': 'Geographic location:',
        'privacy.dataCollected.items.geo.value':
          'Country and city (approximate, based on IP address)',
        'privacy.dataCollected.items.referral.label': 'Referral source:',
        'privacy.dataCollected.items.referral.value':
          'How you arrived at this website',
        'privacy.dataCollected.note.label': 'Important:',
        'privacy.dataCollected.note.value':
          'No personally identifiable information (PII) is collected. I cannot identify individual visitors.',
        'privacy.cookiesUsed.title': 'Cookies Used',
        'privacy.cookiesUsed.intro':
          'Google Analytics sets the following cookies on your browser:',
        'privacy.cookiesUsed.purpose': 'Purpose:',
        'privacy.cookiesUsed.expiration': 'Expiration:',
        'privacy.cookiesUsed.cookies.ga.purpose':
          'Distinguishes unique visitors',
        'privacy.cookiesUsed.cookies.ga.expiration': '2 years',
        'privacy.cookiesUsed.cookies.gid.purpose':
          'Distinguishes unique visitors',
        'privacy.cookiesUsed.cookies.gid.expiration': '24 hours',
        'privacy.cookiesUsed.cookies.gat.purpose': 'Throttles request rate',
        'privacy.cookiesUsed.cookies.gat.expiration': '1 minute',
        'privacy.whyCookies.title': 'Why We Use Cookies',
        'privacy.whyCookies.intro': 'Analytics cookies help me understand:',
        'privacy.whyCookies.items.popularContent':
          'Which content is most popular (astrophotography vs. travel vs. programming)',
        'privacy.whyCookies.items.navigation': 'How visitors navigate the site',
        'privacy.whyCookies.items.devices':
          'What devices and browsers are being used',
        'privacy.whyCookies.items.performance':
          'Whether the site is performing well',
        'privacy.whyCookies.outro':
          'This information helps me improve the website and create better content for visitors.',
        'privacy.rights.title': 'Your Choices & Rights',
        'privacy.rights.optOutTitle': 'Opt-Out Options:',
        'privacy.rights.items.cookieSettings.label': 'Cookie Settings:',
        'privacy.rights.items.cookieSettings.value':
          'Click "Cookie Settings" in the footer to change your consent at any time',
        'privacy.rights.items.browserSettings.label': 'Browser Settings:',
        'privacy.rights.items.browserSettings.value':
          'Configure your browser to block cookies (note: this may affect site functionality)',
        'privacy.rights.items.googleOptOut.label': 'Google Analytics Opt-Out:',
        'privacy.rights.items.googleOptOut.prefix': 'Install the',
        'privacy.rights.items.googleOptOut.link':
          'Google Analytics Opt-out Browser Add-on',
        'privacy.retention.title': 'Data Retention',
        'privacy.retention.body':
          'Google Analytics data is retained for 26 months by default. After this period, aggregated data is automatically deleted.',
        'privacy.thirdParty.title': 'Third-Party Services',
        'privacy.thirdParty.intro':
          'For more detailed information, please refer to the privacy policies of these services, paying attention to specific sections, such as "How we use your information" or "Third-party services".',
        'privacy.thirdParty.uses': 'This website uses:',
        'privacy.thirdParty.googleAnalytics.label': 'Google Analytics:',
        'privacy.thirdParty.googleAnalytics.value':
          'Web analytics service by Google LLC.',
        'privacy.thirdParty.googleAnalytics.link': 'Google Privacy Policy',
        'privacy.contact.title': 'Contact',
        'privacy.contact.body':
          'If you have questions about this privacy policy or how your data is handled, please contact me via the contact form on this website.',
        'privacy.footer':
          'This privacy policy is effective as of the date stated above and will remain in effect except with respect to any changes in its provisions in the future.',
      };
      const polishPrivacyTranslations: Record<string, string> = {
        'privacy.title': 'Polityka Prywatności i Plików Cookie',
        'privacy.lastUpdated': 'Ostatnia aktualizacja: 29 stycznia 2026',
        'privacy.introduction.title': 'Wprowadzenie',
        'privacy.introduction.body':
          'Ta strona jest osobistym portfolio prezentującym moją astrofotografię, fotografię podróżniczą i projekty programistyczne. Szanuję Twoją prywatność i zależy mi na przejrzystym wyjaśnieniu, w jaki sposób ta witryna zbiera i wykorzystuje dane.',
      };

      if (testLang === 'pl' && polishPrivacyTranslations[key]) {
        return polishPrivacyTranslations[key];
      }

      return translations[key] || key;
    },
    i18n: {
      changeLanguage: jest.fn(),
      language:
        (globalThis as { __TEST_I18N_LANGUAGE__?: string })
          .__TEST_I18N_LANGUAGE__ || 'en',
    },
  }),
  initReactI18next: {
    type: '3rdParty',
    init: jest.fn(),
  },
}));

// Mock React Query
jest.mock('@tanstack/react-query', () => {
  const originalModule = jest.requireActual('@tanstack/react-query');
  return {
    ...originalModule,
    useQueryClient: () => ({
      prefetchQuery: jest.fn(),
      invalidateQueries: jest.fn(),
    }),
    useInfiniteQuery: jest.fn().mockReturnValue({
      data: undefined,
      isLoading: false,
      error: null,
      isFetching: false,
      isFetchingNextPage: false,
      hasNextPage: false,
      fetchNextPage: jest.fn(),
    }),
    useQuery: jest.fn().mockReturnValue({
      data: undefined,
      isLoading: false,
      error: null,
      isFetching: false,
      refetch: jest.fn(),
    }),
  };
});
