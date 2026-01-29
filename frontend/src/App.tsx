// frontend/src/App.tsx
import React, { Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import HomePage from './HomePage';
import { hasAnalyticsConsent } from './utils/analytics';
import { useGoogleAnalytics } from './hooks/useGoogleAnalytics';

// Lazy load larger components
const AstroGallery = lazy(() => import('./components/AstroGallery'));
const Programming = lazy(() => import('./components/Programming'));
const TravelHighlightsPage = lazy(
  () => import('./components/TravelHighlightsPage')
);
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const PrivacyPolicy = lazy(() => import('./components/PrivacyPolicy') as any);
import MainLayout from './components/MainLayout';
import LoadingScreen from './components/common/LoadingScreen';
import ScrollToHash from './components/common/ScrollToHash';
import ErrorBoundary from './components/common/ErrorBoundary';
import CookieConsent from './components/common/CookieConsent';
import { APP_ROUTES } from './api/constants';
import './styles/components/App.module.css';

const AnalyticsTracker: React.FC<{ hasConsented: boolean }> = ({
  hasConsented,
}) => {
  useGoogleAnalytics(hasConsented);
  return null;
};

const App: React.FC = () => {
  const [hasConsented, setHasConsented] = React.useState(() =>
    hasAnalyticsConsent()
  );

  return (
    <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <AnalyticsTracker hasConsented={hasConsented} />
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
