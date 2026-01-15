import React, { useEffect, useState } from "react";
import Home from "./components/Home";
import About from "./components/About";
import Contact from "./components/Contact";
import Navbar from "./components/Navbar";
import Footer from "./components/Footer";
import Gallery from "./components/Gallery";
import StarBackground from "./components/StarBackground";
import styles from "./styles/components/App.module.css";
import { fetchProfile, fetchBackground } from "./api/services";
import { UserProfile } from "./types";

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
        console.error("Failed to load initial data:", e);
        setError("Failed to load page content.");
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
      <Gallery />
      <About profile={profile} />
      <Contact />
      <Footer />
    </div>
  );
};

export default HomePage;
