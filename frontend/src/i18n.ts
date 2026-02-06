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
        title: 'Travel Highlights',
        subtitle:
          "Exploring the world's most remote locations in pursuit of the perfect cosmic capture.",
        adventureDate: 'ADVENTURE DATE',
        exploringCosmic: 'Exploring the cosmic wonders of',
      },
      hero: {
        subtitle: 'Documenting the Cosmos',
        titlePart1: 'The Beauty of',
        titlePart2: 'Ancient Light.',
        viewPortfolio: 'View Portfolio',
        aboutMe: 'About Me',
        defaultDescription:
          'I am a professional astrophotographer capturing the silent majesty of deep-space phenomena. My work bridges the gap between scientific observation and cinematic fine art.',
      },
      categories: {
        Landscape: 'Landscape',
        'Deep Sky': 'Deep Sky',
        Startrails: 'Startrails',
        'Solar System': 'Solar System',
        'Milky Way': 'Milky Way',
        'Northern Lights': 'Northern Lights',
      },
      gallery: {
        title: 'Latest images',
        all: 'All Works',
        astrolandscape: 'Astrolandscape',
        timelapses: 'Timelapses',
        loading: 'Loading Portfolio...',
        empty: 'No works found in this category.',
      },
      contact: {
        title: 'Direct Inquiry',
        subtitle:
          "Interested in prints or technical collaboration? Let's connect.",
        identity: 'Identity',
        namePlaceholder: 'Your Name',
        communication: 'Communication',
        emailPlaceholder: 'Email Address',
        topic: 'Topic',
        subjectPlaceholder: 'Subject',
        transmission: 'Transmission',
        messagePlaceholder: 'How can I help you?',
        submit: 'Submit Inquiry',
        sending: 'Sending...',
        success: 'Thank you! Your message has been sent successfully.',
        error:
          'Transmission failure. Please check your signal or try again later.',
        validationError:
          'One or more details in your inquiry require adjustment.',
        errors: {
          name: 'Name must be at least 2 characters long.',
          email: 'Please provide a valid email address.',
          subject: 'Subject must be at least 5 characters long.',
          message: 'Message must be at least 10 characters long.',
          honeypot: 'Please correct the errors above and try again.',
        },
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
        title: 'Ponad Atmosferą.',
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
        title: 'Najciekawsze Podróże',
        subtitle:
          'Podróże do różnych zakątków świata, w poszukiwaniu idealnego ujęcia.',
        adventureDate: 'DATA PRZYGODY',
        exploringCosmic: 'Kosmiczna przygoda w',
      },
      hero: {
        subtitle: 'Dokumentowanie Kosmosu',
        titlePart1: 'Piękno Świata',
        titlePart2: 'sprzed milionów lat.',
        viewPortfolio: 'Zobacz Portfolio',
        aboutMe: 'O mnie',
        defaultDescription:
          'Jestem profesjonalnym astrofotografem, uchwycającym cichy majestat zjawisk głębokiego nieba. Moja praca łączy obserwację naukową z artystyczną wizją.',
      },
      categories: {
        Landscape: 'Krajobraz',
        'Deep Sky': 'Głębokie Niebo',
        Startrails: 'Startrails',
        'Solar System': 'Układ Słoneczny',
        'Milky Way': 'Droga Mleczna',
        'Northern Lights': 'Zorza Polarna',
      },
      gallery: {
        title: 'Ostatnie zdjęcia',
        all: 'Wszystkie',
        astrolandscape: 'Astrokrajobraz',
        timelapses: 'Timelapsy',
        loading: 'Ładowanie portfolio...',
        empty: 'Nie znaleziono prac w tej kategorii.',
      },
      contact: {
        title: 'Zapytanie',
        subtitle: 'Interesują Cię wydruki lub współpraca? Napisz do mnie!',
        identity: 'Imię',
        namePlaceholder: 'Twoje Imię',
        communication: 'Email',
        emailPlaceholder: 'Adres Email',
        topic: 'Temat',
        subjectPlaceholder: 'Temat wiadomości',
        transmission: 'Wiadomość',
        messagePlaceholder: 'W czym mogę Ci pomóc?',
        submit: 'Wyślij zapytanie',
        sending: 'Wysyłanie...',
        success: 'Dziękujemy! Twoja wiadomość została wysłana pomyślnie.',
        error: 'Błąd transmisji. Sprawdź sygnał lub spróbuj ponownie później.',
        validationError:
          'Jedna lub więcej szczegółów zapytania wymaga korekty.',
        errors: {
          name: 'Imię musi mieć co najmniej 2 znaki.',
          email: 'Podaj prawidłowy adres email.',
          subject: 'Temat musi mieć co najmniej 5 znaków.',
          message: 'Wiadomość musi mieć co najmniej 10 znaków.',
          honeypot: 'Popraw błędy powyżej i spróbuj ponownie.',
        },
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
