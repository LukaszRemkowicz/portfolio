import React, { useEffect, Suspense, lazy } from "react";
import Home from "./components/Home";
import Navbar from "./components/Navbar";
import Footer from "./components/Footer";
import StarBackground from "./components/StarBackground";

// Lazy load non-critical sections
const Gallery = lazy(() => import("./components/Gallery"));
const About = lazy(() => import("./components/About"));
const Contact = lazy(() => import("./components/Contact"));

import styles from "./styles/components/App.module.css";
import { useAppStore } from "./store/useStore";
import LoadingScreen from "./components/common/LoadingScreen";

const DEFAULT_PORTRAIT = "/portrait_default.png";

const HomePage: React.FC = () => {
  const {
    profile,
    backgroundUrl,
    isInitialLoading: loading,
    error,
    loadInitialData,
  } = useAppStore();

  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  if (loading) return <LoadingScreen />;
  if (error) return <div className={styles.error}>{error}</div>;

  return (
    <div className={styles.appContainer}>
      <StarBackground />
      <Navbar transparent />
      <main className={styles.mainContent}>
        <Home
          portraitUrl={profile?.avatar || DEFAULT_PORTRAIT}
          shortDescription={profile?.short_description || ""}
          backgroundUrl={backgroundUrl}
        />
      </main>
      <Suspense
        fallback={
          <LoadingScreen fullScreen={false} message="Aligning sectors..." />
        }
      >
        <Gallery />
        <About profile={profile} />
        <Contact />
      </Suspense>
      <Footer />
    </div>
  );
};

export default HomePage;
