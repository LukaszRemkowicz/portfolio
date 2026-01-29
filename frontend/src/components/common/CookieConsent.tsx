import { Link } from 'react-router-dom';
import React, { useState, useEffect } from 'react';
import { Cookie } from 'lucide-react';
import styles from './CookieConsent.module.css';

interface WindowWithCookieSettings extends Window {
  openCookieSettings?: () => void;
}

declare const window: WindowWithCookieSettings;

interface CookieConsentProps {
  onAccept: () => void;
}

const CookieConsent: React.FC<CookieConsentProps> = ({ onAccept }) => {
  const [showBanner, setShowBanner] = useState(false);

  // Initialize state from local storage
  useEffect(() => {
    // Check if user has already consented
    const consent = localStorage.getItem('cookieConsent');
    if (!consent) {
      // No consent stored, show banner after delay
      const timer = setTimeout(() => setShowBanner(true), 1000);
      return () => clearTimeout(timer);
    }
  }, []);

  useEffect(() => {
    // Expose global function to reopen banner (for Cookie Settings button)
    window.openCookieSettings = () => {
      setShowBanner(true);
    };

    return () => {
      delete window.openCookieSettings;
    };
  }, []);

  const acceptCookies = () => {
    localStorage.setItem('cookieConsent', 'true');
    onAccept();
    setShowBanner(false);
  };

  const declineCookies = () => {
    localStorage.setItem('cookieConsent', 'false');
    setShowBanner(false);
  };

  if (!showBanner) return null;

  return (
    <div className={styles.cookieBanner}>
      <div className={styles.container}>
        <div className={styles.content}>
          <div className={styles.iconWrapper}>
            <Cookie className={styles.icon} />
          </div>
          <div className={styles.textContent}>
            <h4 className={styles.title}>Cookie Consent</h4>
            <p className={styles.description}>
              We use cookies to enhance your experience, analyze traffic, and
              personalize your journey through the cosmos. By using our site,
              you agree to our{' '}
              <Link to='/privacy-policy' className={styles.learnMore}>
                Privacy Policy
              </Link>
              .
            </p>
          </div>
        </div>
        <div className={styles.actions}>
          <button onClick={declineCookies} className={styles.declineBtn}>
            Decline
          </button>
          <button onClick={acceptCookies} className={styles.acceptBtn}>
            Accept
          </button>
        </div>
      </div>
    </div>
  );
};

export default CookieConsent;
