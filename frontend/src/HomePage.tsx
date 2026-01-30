import React, { useEffect, Suspense, lazy } from 'react';
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
import { useAppStore } from './store/useStore';
import LoadingScreen from './components/common/LoadingScreen';

const DEFAULT_PORTRAIT = '/portrait_default.png';

const HomePage: React.FC = () => {
  const profile = useAppStore(state => state.profile);
  const backgroundUrl = useAppStore(state => state.backgroundUrl);
  const loading = useAppStore(state => state.isInitialLoading);
  const error = useAppStore(state => state.error);
  const loadInitialData = useAppStore(state => state.loadInitialData);

  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  if (loading) return <LoadingScreen />;

  // Graceful degradation: If error occurs, render content anyway with a notification
  return (
    <div className={styles.appContainer}>
      {error && (
        <div className={styles.errorBanner} role='alert'>
          {error}
          <button
            onClick={() => useAppStore.getState().clearError()}
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
            <About profile={profile} />
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
