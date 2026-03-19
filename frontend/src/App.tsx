// frontend/src/App.tsx
import React, { Suspense, lazy } from 'react';
import { Routes, Route } from 'react-router-dom';
const HomePage = lazy(() => import('./HomePage'));
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
import ClientOnly from './components/common/ClientOnly';
import ClientDocumentGuards from './components/common/ClientDocumentGuards';
import { APP_ROUTES } from './api/constants';
import './styles/components/App.module.css';

// Client-only: renders null, wires GA on the client
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
    <>
      <ClientOnly>
        <AnalyticsTracker hasConsented={hasConsented} />
        <ScrollToHash />
        <ClientDocumentGuards />
      </ClientOnly>
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
            >
              {/* Child route so /astrophotography/:slug is a valid path.
                  AstroGallery reads the :slug param and opens the modal. */}
              <Route path=':slug' element={null} />
            </Route>
            <Route
              path={APP_ROUTES.PROGRAMMING}
              element={
                <MainLayout>
                  <Programming />
                </MainLayout>
              }
            />
            <Route
              path={`${APP_ROUTES.TRAVEL_HIGHLIGHTS}/:countrySlug/:placeSlug/:dateSlug`}
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
      <ClientOnly>
        <CookieConsent onAccept={() => setHasConsented(true)} />
      </ClientOnly>
    </>
  );
};

export default App;
