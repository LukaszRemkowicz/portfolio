// frontend/src/App.tsx
import React, { Suspense, lazy } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import HomePage from './HomePage';
import { hasAnalyticsConsent } from './utils/analytics';
import { useGoogleAnalytics } from './hooks/useGoogleAnalytics';
import MainLayout from './components/MainLayout';
import ScrollToHash from './components/common/ScrollToHash';
import ErrorBoundary from './components/common/ErrorBoundary';
import CookieConsent from './components/common/CookieConsent';
import ClientOnly from './components/common/ClientOnly';
import ClientDocumentGuards from './components/common/ClientDocumentGuards';
import { APP_ROUTES } from './api/constants';
import styles from './styles/components/App.module.css';

const AstroGallery = lazy(() => import('./components/AstroGallery'));
const Shop = lazy(() => import('./components/Shop'));
const Programming = lazy(() => import('./components/Programming'));
const TravelHighlightsPage = lazy(
  () => import('./components/TravelHighlightsPage')
);
const PrivacyPolicy = lazy(() => import('./components/PrivacyPolicy'));

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
      <div className={`${styles.appContainer} ${styles.astroBg}`}>
        <ErrorBoundary>
          <Routes>
            <Route path={APP_ROUTES.HOME} element={<HomePage />} />
            <Route
              path={APP_ROUTES.ASTROPHOTOGRAPHY}
              element={
                <RouteSuspense>
                  <MainLayout>
                    <AstroGallery />
                  </MainLayout>
                </RouteSuspense>
              }
            >
              {/* Child route so /astrophotography/:slug is a valid path.
                AstroGallery reads the :slug param and opens the modal. */}
              <Route path=':slug' element={null} />
            </Route>
            <Route
              path={APP_ROUTES.SHOP}
              element={
                <RouteSuspense>
                  <MainLayout>
                    <Shop />
                  </MainLayout>
                </RouteSuspense>
              }
            />
            <Route
              path={APP_ROUTES.PROGRAMMING}
              element={
                <RouteSuspense>
                  <MainLayout>
                    <Programming />
                  </MainLayout>
                </RouteSuspense>
              }
            />
            <Route
              path={`${APP_ROUTES.TRAVEL_HIGHLIGHTS}/:countrySlug/:placeSlug/:dateSlug`}
              element={
                <RouteSuspense>
                  <MainLayout>
                    <TravelHighlightsPage />
                  </MainLayout>
                </RouteSuspense>
              }
            />

            <Route
              path={APP_ROUTES.PRIVACY}
              element={
                <RouteSuspense>
                  <MainLayout>
                    <PrivacyPolicy />
                  </MainLayout>
                </RouteSuspense>
              }
            />
            {/* Catch-all: Redirect to home or show 404 */}
            <Route
              path='*'
              element={<Navigate to={APP_ROUTES.HOME} replace />}
            />
          </Routes>
        </ErrorBoundary>
      </div>
      <ClientOnly>
        <CookieConsent onAccept={() => setHasConsented(true)} />
      </ClientOnly>
    </>
  );
};

// This stays null intentionally to avoid flashing a generic route-level loader
// while route components handle their own loading states.
const RouteSuspense: React.FC<React.PropsWithChildren> = ({ children }) => (
  <Suspense fallback={null}>{children}</Suspense>
);

export default App;
