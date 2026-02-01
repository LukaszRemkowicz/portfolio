import '@testing-library/jest-dom';

// Ensure API_URL is defined for tests to avoid constant initialization error
process.env.API_URL = 'http://localhost:8000';

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

// Mock react-i18next
jest.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        'nav.home': 'Home',
        'nav.astrophotography': 'Astrophotography',
        'nav.programming': 'Programming',
        'nav.about': 'About',
        'nav.contact': 'Contact',
        'common.en': 'EN',
        'common.pl': 'PL',
        'common.privacyPolicy': 'Privacy Policy',
        'common.cookieSettings': 'Cookie Settings',
        'common.decline': 'Decline',
        'common.accept': 'Accept',
        'footer.rights': 'Łukasz Remkowicz © 2026',
        'about.title': 'Beyond the Atmosphere.',
        'about.defaultBio':
          'Astrophotography is a technical dance with physics. My journey involves thousands of light frames, hours of integration, and a dedication to revealing what remains invisible to the naked eye.',
        'about.siteQuality': 'Site Quality',
        'about.primaryOptics': 'Primary Optics',
        'cookie.title': 'Cookie Consent',
        'cookie.description':
          'We use cookies to enhance your experience, analyze traffic, and personalize your journey through the cosmos. By using our site, you agree to our',
      };
      return translations[key] || key;
    },
    i18n: {
      changeLanguage: jest.fn(),
      language: 'en',
    },
  }),
  initReactI18next: {
    type: '3rdParty',
    init: jest.fn(),
  },
}));
