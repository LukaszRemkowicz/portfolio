import React, { useState, useEffect } from 'react';
import { Cookie } from 'lucide-react';
import styles from './CookieConsent.module.css';
import { loadGoogleAnalytics } from '../../utils/analytics';

interface WindowWithCookieSettings extends Window {
  openCookieSettings?: () => void;
}

declare const window: WindowWithCookieSettings;

const CookieConsent: React.FC = () => {
  const [showBanner, setShowBanner] = useState(false);

  useEffect(() => {
    // Check if user has already consented
    const consent = localStorage.getItem('cookieConsent');
    if (consent === 'true') {
      // User previously accepted, load GA
      loadGoogleAnalytics();
    } else if (!consent) {
      // No consent stored, show banner after delay
      const timer = setTimeout(() => setShowBanner(true), 1000);
      // This return is for the timer cleanup, but we also need to expose the global function.
      // We'll handle the global function exposure and its cleanup separately.
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
  }, []); // Empty dependency array ensures this runs once on mount and cleans up on unmount

  const acceptCookies = () => {
    localStorage.setItem('cookieConsent', 'true');
    loadGoogleAnalytics();
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
              personalize your journey through the cosmos. By continuing to
              explore, you accept our use of cookies.{' '}
              <a href='#privacy' className={styles.learnMore}>
                Learn more
              </a>
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
