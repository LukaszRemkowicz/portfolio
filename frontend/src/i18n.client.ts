// frontend/src/i18n.client.ts
//
// Browser-only i18n initialisation (singleton).
// Uses LanguageDetector (localStorage + navigator) — browser APIs only.
// Do NOT import this file in any server (SSR) path.

import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import HttpApi from 'i18next-http-backend';
import en from '../public/locales/en/translation.json';
import pl from '../public/locales/pl/translation.json';

declare global {
  interface Window {
    __INITIAL_LANGUAGE__?: string;
  }
}

const initialLanguage =
  typeof window !== 'undefined' ? window.__INITIAL_LANGUAGE__ : undefined;

i18n
  .use(HttpApi)
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    lng: initialLanguage,
    resources: {
      en: { translation: en },
      pl: { translation: pl },
    },
    fallbackLng: 'en',
    debug: false,
    interpolation: {
      escapeValue: false,
    },
    detection: {
      order: ['htmlTag', 'localStorage', 'navigator'],
      caches: ['localStorage'],
    },
    backend: {
      loadPath: '/locales/{{lng}}/{{ns}}.json',
    },
  });

export default i18n;
