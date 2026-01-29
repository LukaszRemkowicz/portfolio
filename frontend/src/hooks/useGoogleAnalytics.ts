import { useEffect } from 'react';
import { loadGoogleAnalytics } from '../utils/analytics';

/**
 * Custom hook to initialize Google Analytics when consent is granted.
 * @param hasConsented - Boolean indicating if user has accepted cookies.
 */
export const useGoogleAnalytics = (hasConsented: boolean) => {
  useEffect(() => {
    if (hasConsented) {
      loadGoogleAnalytics();
    }
  }, [hasConsented]);
};
