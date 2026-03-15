import React, { Suspense, lazy, useState } from 'react';
import Home from './components/Home';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import StarBackground from './components/StarBackground';
import SEO from './components/common/SEO';

// Lazy load non-critical sections
const Gallery = lazy(() => import('./components/Gallery'));
const TravelHighlights = lazy(() => import('./components/TravelHighlights'));
const About = lazy(() => import('./components/About'));
const Contact = lazy(() => import('./components/Contact'));

import ErrorBoundary from './components/common/ErrorBoundary';
import styles from './styles/components/App.module.css';
import LoadingScreen from './components/common/LoadingScreen';
import { useProfile } from './hooks/useProfile';
import { useBackground } from './hooks/useBackground';

const HomePage: React.FC = () => {
  const {
    data: profile,
    isLoading: isProfileLoading,
    error: profileError,
  } = useProfile();
  const {
    data: backgroundUrl,
    isLoading: isBackgroundLoading,
    error: backgroundError,
  } = useBackground();
  const [isErrorDismissed, setIsErrorDismissed] = useState(false);

  const rawError = profileError || backgroundError;
  const error =
    !isErrorDismissed && rawError
      ? 'The cosmic archives are temporarily unreachable.'
      : null;

  if (isProfileLoading || isBackgroundLoading) {
    return <LoadingScreen message='Synchronizing...' />;
  }

  // Graceful degradation: If error occurs, render content anyway with a notification
  return (
    <div className={styles.appContainer}>
      <SEO />
      {error && (
        <div className={styles.errorBanner} role='alert'>
          {error}
          <button
            onClick={() => setIsErrorDismissed(true)}
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
          portraitUrl={profile?.avatar || ''}
          shortDescription={profile?.short_description || ''}
          backgroundUrl={backgroundUrl}
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
