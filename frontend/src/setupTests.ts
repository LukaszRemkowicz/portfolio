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
