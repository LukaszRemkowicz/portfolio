import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { loadGoogleAnalytics, trackPageView } from '../utils/analytics';

export const useGoogleAnalytics = (hasConsented: boolean) => {
  const location = useLocation();

  useEffect(() => {
    if (hasConsented) {
      // Defer non-critical analytics to preserve main-thread availability during boot
      const timeout = setTimeout(() => {
        loadGoogleAnalytics();
        trackPageView(location.pathname + location.search);
      }, 3500);
      return () => clearTimeout(timeout);
    }
  }, [hasConsented, location.pathname, location.search]);
};
