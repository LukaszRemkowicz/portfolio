// frontend/src/i18n.client.ts
//
// Browser-only i18n initialisation (singleton).
// Uses an explicit initial language snapshot from SSR.
// Do NOT import this file in any server (SSR) path.

import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import HttpApi from 'i18next-http-backend';
import LanguageDetector from 'i18next-browser-languagedetector';

declare global {
  interface Window {
    __INITIAL_LANGUAGE__?: string;
  }
}

function normalizeLanguage(lang?: string): string | undefined {
  if (!lang) return undefined;
  const tag = lang.split(',')[0].split('-')[0].split('_')[0].toLowerCase();
  if (tag === 'pl') return 'pl';
  if (tag === 'en') return 'en';
  return undefined;
}

const initialLanguage =
  typeof window !== 'undefined'
    ? normalizeLanguage(window.__INITIAL_LANGUAGE__)
    : undefined;

export const i18nReady = i18n
  .use(HttpApi)
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    lng: initialLanguage, // If set by SSR, i18next uses this first
    fallbackLng: 'en',
    supportedLngs: ['en', 'pl'],
    detection: {
      order: ['querystring', 'cookie', 'localStorage', 'navigator'],
      caches: ['localStorage', 'cookie'],
      lookupCookie: 'i18next',
      lookupLocalStorage: 'i18nextLng',
      cookieMinutes: 525600, // 1 year
      cookieOptions: {
        sameSite: 'lax',
      },
    },
    debug: false,
    interpolation: {
      escapeValue: false,
    },
    backend: {
      loadPath: '/locales/{{lng}}/{{ns}}.json',
    },
  });

export default i18n;
