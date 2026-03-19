// frontend/src/App.tsx
import React, { Suspense, lazy } from 'react';
import { Routes, Route } from 'react-router-dom';
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
      <ErrorBoundary>
        <Routes>
          <Route path={APP_ROUTES.HOME} element={<HomePage />} />
          <Route
            path={APP_ROUTES.ASTROPHOTOGRAPHY}
            element={
              <MainLayout>
                <Suspense fallback={<LoadingScreen fullScreen={false} />}>
                  <AstroGallery />
                </Suspense>
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
                <Suspense fallback={<LoadingScreen fullScreen={false} />}>
                  <Programming />
                </Suspense>
              </MainLayout>
            }
          />
          <Route
            path={`${APP_ROUTES.TRAVEL_HIGHLIGHTS}/:countrySlug/:placeSlug/:dateSlug`}
            element={
              <MainLayout>
                <Suspense fallback={<LoadingScreen fullScreen={false} />}>
                  <TravelHighlightsPage />
                </Suspense>
              </MainLayout>
            }
          />

          <Route
            path={APP_ROUTES.PRIVACY}
            element={
              <MainLayout>
                <Suspense fallback={<LoadingScreen fullScreen={false} />}>
                  <PrivacyPolicy />
                </Suspense>
              </MainLayout>
            }
          />
        </Routes>
      </ErrorBoundary>
      <ClientOnly>
        <CookieConsent onAccept={() => setHasConsented(true)} />
      </ClientOnly>
    </>
  );
};

export default App;
