// frontend/src/i18n.server.ts
//
// Server-safe i18n factory.
// Creates a fresh i18next instance per request — no browser globals,
// no LanguageDetector, no localStorage.
// Used in entry-server.tsx (Phase 1+).

import i18next from 'i18next';
import { initReactI18next } from 'react-i18next';
import en from '../public/locales/en/translation.json';
import pl from '../public/locales/pl/translation.json';

type SupportedLanguage = 'en' | 'pl';

function detectLanguage(_acceptLanguage: string): SupportedLanguage {
  return 'en';
}

export async function createServerI18n(acceptLanguage = 'en') {
  const instance = i18next.createInstance();
  const lng = detectLanguage(acceptLanguage);

  await instance.use(initReactI18next).init({
    lng,
    fallbackLng: 'en',
    resources: {
      en: { translation: en },
      pl: { translation: pl },
    },
    interpolation: { escapeValue: false },
    debug: false,
  });

  return instance;
}
