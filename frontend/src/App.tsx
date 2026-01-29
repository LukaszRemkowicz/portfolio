// frontend/src/App.tsx
import React, { Suspense, lazy, useEffect } from 'react';
import {
  BrowserRouter as Router,
  Routes,
  Route,
  useLocation,
} from 'react-router-dom';
import HomePage from './HomePage';
import { trackPageView, hasAnalyticsConsent } from './utils/analytics';
import { useGoogleAnalytics } from './hooks/useGoogleAnalytics';

// Component to handle tracking on route change
const AnalyticsTracker: React.FC<{ enabled: boolean }> = ({ enabled }) => {
  const location = useLocation();

  useEffect(() => {
    if (!enabled) return;
    trackPageView(location.pathname + location.search);
  }, [enabled, location.pathname, location.search]);

  return null;
};

// Lazy load larger components
const AstroGallery = lazy(() => import('./components/AstroGallery'));
const Programming = lazy(() => import('./components/Programming'));
const TravelHighlightsPage = lazy(
  () => import('./components/TravelHighlightsPage')
);
const PrivacyPolicy = lazy(() => import('./components/PrivacyPolicy'));
import MainLayout from './components/MainLayout';
import LoadingScreen from './components/common/LoadingScreen';
import ScrollToHash from './components/common/ScrollToHash';
import ErrorBoundary from './components/common/ErrorBoundary';
import CookieConsent from './components/common/CookieConsent';
import { APP_ROUTES } from './api/constants';
import './styles/components/App.module.css';

const App: React.FC = () => {
  const [hasConsented, setHasConsented] = React.useState(() =>
    hasAnalyticsConsent()
  );

  // Initialize GA if consented
  useGoogleAnalytics(hasConsented);

  return (
    <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <AnalyticsTracker enabled={hasConsented} />
      <ScrollToHash />
      <Suspense fallback={<LoadingScreen />}>
        <ErrorBoundary>
          <Routes>
            <Route path={APP_ROUTES.HOME} element={<HomePage />} />
            <Route
              path={APP_ROUTES.ASTROPHOTOGRAPHY}
              element={
                <MainLayout>
                  <AstroGallery />
                </MainLayout>
              }
            />
            <Route
              path={APP_ROUTES.PROGRAMMING}
              element={
                <MainLayout>
                  <Programming />
                </MainLayout>
              }
            />
            <Route
              path={`${APP_ROUTES.TRAVEL_HIGHLIGHTS}/:countrySlug/:placeSlug?`}
              element={
                <MainLayout>
                  <TravelHighlightsPage />
                </MainLayout>
              }
            />
            <Route
              path={APP_ROUTES.PRIVACY}
              element={
                <MainLayout>
                  <PrivacyPolicy />
                </MainLayout>
              }
            />
          </Routes>
        </ErrorBoundary>
      </Suspense>
      <CookieConsent onAccept={() => setHasConsented(true)} />
    </Router>
  );
};

export default App;
