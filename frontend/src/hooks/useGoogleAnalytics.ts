import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { loadGoogleAnalytics, trackPageView } from '../utils/analytics';

export const useGoogleAnalytics = (hasConsented: boolean) => {
  const location = useLocation();

  useEffect(() => {
    if (hasConsented) {
      loadGoogleAnalytics();
      trackPageView(location.pathname + location.search);
    }
  }, [hasConsented, location.pathname, location.search]);
};
