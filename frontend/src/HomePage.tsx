import React, { useEffect, useState, Suspense, lazy } from "react";
import Home from "./components/Home";
import Navbar from "./components/Navbar";
import Footer from "./components/Footer";
import StarBackground from "./components/StarBackground";

// Lazy load non-critical sections
const Gallery = lazy(() => import("./components/Gallery"));
const About = lazy(() => import("./components/About"));
const Contact = lazy(() => import("./components/Contact"));

import styles from "./styles/components/App.module.css";
import { fetchProfile, fetchBackground } from "./api/services";
import { UserProfile } from "./types";
import { NetworkError, ServerError } from "./api/errors";

const DEFAULT_PORTRAIT = "/portrait_default.png";

const HomePage: React.FC = () => {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [backgroundUrl, setBackgroundUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadData = async (): Promise<void> => {
      setLoading(true);
      try {
        const [profileData, bgUrl] = await Promise.all([
          fetchProfile(),
          fetchBackground(),
        ]);
        setProfile(profileData);
        setBackgroundUrl(bgUrl);
      } catch (e: unknown) {
        if (e instanceof NetworkError) {
          setError("Signal lost. Please check your network connection and retry.");
        } else if (e instanceof ServerError) {
          setError("The cosmic archives are temporarily unreachable. Our engineers are investigating.");
        } else {
          setError("An unexpected anomaly occurred while loading the cosmos.");
        }
        console.error("Critical failure:", e);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  if (loading) return <div className={styles.loading}>Loading...</div>;
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
      <Suspense fallback={<div className={styles.loading}>Loading section...</div>}>
        <Gallery />
        <About profile={profile} />
        <Contact />
      </Suspense>
      <Footer />
    </div>
  );
};

export default HomePage;
