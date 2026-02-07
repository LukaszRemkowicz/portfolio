// frontend/src/components/common/LanguageSwitcher.tsx
import React from 'react';
import { useTranslation } from 'react-i18next';
import { Globe } from 'lucide-react';
import styles from '../../styles/components/LanguageSwitcher.module.css';

const LanguageSwitcher: React.FC = () => {
  const { i18n } = useTranslation();

  const toggleLanguage = () => {
    const lang = i18n.language || 'en';
    const nextLang = lang.startsWith('en') ? 'pl' : 'en';
    i18n.changeLanguage(nextLang);
  };

  const currentLang = (i18n.language || 'en').split('-')[0];

  return (
    <button
      className={styles.switcher}
      onClick={toggleLanguage}
      aria-label='Toggle language'
    >
      <Globe className={styles.icon} />
      <span className={styles.textContainer}>
        <span
          className={`${styles.lang} ${currentLang === 'en' ? styles.active : ''}`}
        >
          EN
        </span>
        <span className={styles.separator}>|</span>
        <span
          className={`${styles.lang} ${currentLang === 'pl' ? styles.active : ''}`}
        >
          PL
        </span>
      </span>
    </button>
  );
};

export default LanguageSwitcher;
