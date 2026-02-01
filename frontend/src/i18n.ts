// frontend/src/i18n.ts
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

const resources = {
  en: {
    translation: {
      nav: {
        home: 'Home',
        astrophotography: 'Astrophotography',
        programming: 'Programming',
        about: 'About',
        contact: 'Contact',
      },
      common: {
        en: 'EN',
        pl: 'PL',
        privacyPolicy: 'Privacy Policy',
        cookieSettings: 'Cookie Settings',
        decline: 'Decline',
        accept: 'Accept',
      },
      footer: {
        rights: 'Łukasz Remkowicz © 2026',
      },
      about: {
        title: 'Beyond the Atmosphere.',
        defaultBio:
          'Astrophotography is a technical dance with physics. My journey involves thousands of light frames, hours of integration, and a dedication to revealing what remains invisible to the naked eye.',
        siteQuality: 'Site Quality',
        primaryOptics: 'Primary Optics',
      },
      cookie: {
        title: 'Cookie Consent',
        description:
          'We use cookies to enhance your experience, analyze traffic, and personalize your journey through the cosmos. By using our site, you agree to our',
      },
    },
  },
  pl: {
    translation: {
      nav: {
        home: 'Start',
        astrophotography: 'Astrofotografia',
        programming: 'Programowanie',
        about: 'O mnie',
        contact: 'Kontakt',
      },
      common: {
        en: 'EN',
        pl: 'PL',
        privacyPolicy: 'Polityka Prywatności',
        cookieSettings: 'Ustawienia Cookies',
        decline: 'Odrzuć',
        accept: 'Akceptuj',
      },
      footer: {
        rights: 'Łukasz Remkowicz © 2026',
      },
      about: {
        title: 'Poza Atmosferę.',
        defaultBio:
          'Astrofotografia to techniczny taniec z fizyką. Moja podróż składa się z tysięcy klatek, godzin integracji i poświęcenia w odkrywaniu tego, co pozostaje niewidoczne dla gołego oka.',
        siteQuality: 'Jakość Nieba',
        primaryOptics: 'Główna Optyka',
      },
      cookie: {
        title: 'Zgoda na Cookies',
        description:
          'Używamy plików cookie, aby ulepszyć Twoje doświadczenie, analizować ruch i spersonalizować Twoją podróż przez kosmos. Korzystając z naszej strony, akceptujesz naszą',
      },
    },
  },
};

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false,
    },
    detection: {
      order: ['localStorage', 'navigator'],
      caches: ['localStorage'],
    },
  });

export default i18n;
