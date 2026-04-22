// frontend/src/i18n.server.ts
//
// Server-safe i18n factory.
// Creates a fresh i18next instance per request — no browser globals,
// no LanguageDetector, no localStorage.
// Used in entry-server.tsx (Phase 1+).

import i18next from 'i18next';
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { initReactI18next } from 'react-i18next';
import { detectLanguage } from './shared/i18n/detectLanguage';

const appRoot = process.cwd();

function loadTranslation(language: 'en' | 'pl') {
  const translationPath = path.join(
    appRoot,
    'public',
    'locales',
    language,
    'translation.json'
  );
  return JSON.parse(readFileSync(translationPath, 'utf-8'));
}

const en = loadTranslation('en');
const pl = loadTranslation('pl');

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
