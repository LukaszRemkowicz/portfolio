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
        noDescription: 'No description available for this image.',
        scanning: 'Scanning deep space sectors...',
        syncCosmos: 'Synchronizing with the Cosmos',
        compiling: 'Compiling projects...',
        gallery: 'Gallery',
        gallerySubtitle:
          'Filter by category or explore images using the tags below.',
        exploreTags: 'Explore Tags',
        tags: 'Tags',
        allTags: 'All Tags',
        categories: 'Categories',
        noImagesFound: 'No images found for this filter.',
        noImagesHint:
          'Try selecting a different category or tag to see more images.',
      },
      programming: {
        title: 'Project Archive',
        subtitle:
          'A collection of software engineering projects, from microservices to creative frontend experiments.',
        source: 'Source',
        liveDemo: 'Live Demo',
        empty:
          'The archives appear to be empty. Check back later for new transmissions.',
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
      travel: {
        adventureDate: 'ADVENTURE DATE',
        exploringCosmic: 'Exploring the cosmic wonders of',
      },
      categories: {
        Landscape: 'Landscape',
        'Deep Sky': 'Deep Sky',
        Startrails: 'Startrails',
        'Solar System': 'Solar System',
        'Milky Way': 'Milky Way',
        'Northern Lights': 'Northern Lights',
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
        noDescription:
          'Niestety nie ma jeszcze opisu zdjecia dla jezyka Polskiego.',
        scanning: 'Skanowanie sektorów głębokiego kosmosu...',
        syncCosmos: 'Synchronizacja z kosmosem',
        compiling: 'Kompilowanie projektów...',
        gallery: 'Galeria',
        gallerySubtitle:
          'Filtruj według kategorii lub przeglądaj zdjęcia za pomocą tagów poniżej.',
        exploreTags: 'Przeglądaj Tagi',
        tags: 'Tagi',
        allTags: 'Wszystkie Tagi',
        categories: 'Kategorie',
        noImagesFound: 'Nie znaleziono zdjęć dla tego filtra.',
        noImagesHint:
          'Spróbuj wybrać inną kategorię lub tag, aby zobaczyć więcej zdjęć.',
      },
      programming: {
        title: 'Archiwum Projektów',
        subtitle:
          'Kolekcja projektów inżynierii oprogramowania, od mikroserwisów po kreatywne eksperymenty frontendowe.',
        source: 'Kod źródłowy',
        liveDemo: 'Demo Live',
        empty: 'Archiwa wydają się być puste. Wróć później po nowe transmisje.',
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
      travel: {
        adventureDate: 'DATA PRZYGODY',
        exploringCosmic: 'Kosmiczna przygoda w',
      },
      categories: {
        Landscape: 'Krajobraz',
        'Deep Sky': 'Głębokie Niebo',
        Startrails: 'Startrails',
        'Solar System': 'Układ Słoneczny',
        'Milky Way': 'Droga Mleczna',
        'Northern Lights': 'Zorza Polarna',
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
