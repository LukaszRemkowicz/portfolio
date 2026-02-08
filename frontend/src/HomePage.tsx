import React, { Suspense, lazy } from 'react';
import Home from './components/Home';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import StarBackground from './components/StarBackground';

// Lazy load non-critical sections
const Gallery = lazy(() => import('./components/Gallery'));
const TravelHighlights = lazy(() => import('./components/TravelHighlights'));
const About = lazy(() => import('./components/About'));
const Contact = lazy(() => import('./components/Contact'));

import ErrorBoundary from './components/common/ErrorBoundary';
import styles from './styles/components/App.module.css';
import { useProfile } from './hooks/useProfile';
import { useBackground } from './hooks/useBackground';
import { useSettings } from './hooks/useSettings';
import LoadingScreen from './components/common/LoadingScreen';
import SEO from './components/common/SEO';

const DEFAULT_PORTRAIT = '/portrait_default.png';

const HomePage: React.FC = () => {
  const {
    data: profile,
    isLoading: isProfileLoading,
    error: profileError,
  } = useProfile();
  const { data: backgroundUrl, isLoading: isBackgroundLoading } =
    useBackground();
  const { isLoading: isSettingsLoading } = useSettings();

  const isInitialLoading =
    isProfileLoading || isBackgroundLoading || isSettingsLoading;

  const error = profileError ? (profileError as Error).message : null;

  if (isInitialLoading) return <LoadingScreen />;

  // Graceful degradation: If error occurs, render content anyway with a notification
  return (
    <div className={styles.appContainer}>
      {error && (
        <div className={styles.errorBanner} role='alert'>
          {error}
          <button
            onClick={() => {
              /* Error dismissal is now handled by RQ or local state if we add one */
            }}
            className={styles.dismissError}
            aria-label='Dismiss error'
          >
            ×
          </button>
        </div>
      )}
      <StarBackground />
      <Navbar transparent />
      <main className={styles.mainContent}>
        <Home
          portraitUrl={profile?.avatar || DEFAULT_PORTRAIT}
          shortDescription={profile?.short_description || ''}
          backgroundUrl={backgroundUrl}
        />
        <SEO
          title='Home'
          description={profile?.short_description}
          image={profile?.avatar || DEFAULT_PORTRAIT}
        />
        <Suspense
          fallback={
            <LoadingScreen fullScreen={false} message='Aligning sectors...' />
          }
        >
          <ErrorBoundary>
            <TravelHighlights />
          </ErrorBoundary>
          <ErrorBoundary>
            <Gallery />
          </ErrorBoundary>
          <ErrorBoundary>
            <About profile={profile || null} />
          </ErrorBoundary>
          <ErrorBoundary>
            <Contact />
          </ErrorBoundary>
        </Suspense>
      </main>
      <Footer />
    </div>
  );
};

export default HomePage;
