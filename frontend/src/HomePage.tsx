import React, { useEffect, useState } from "react";
import Home from "./Home";
import About from "./About";
import Contact from "./Contact";
import Navbar from "./Navbar";
import Footer from "./Footer";
import Gallery from "./Gallery";
import StarBackground from "./StarBackground";
import styles from "./styles/components/App.module.css";
import { fetchProfile } from "./api/services";
import { UserProfile } from "./types";

const DEFAULT_PORTRAIT = "/portrait_default.png";

const HomePage: React.FC = () => {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadData = async (): Promise<void> => {
      setLoading(true);
      try {
        const profileData = await fetchProfile();
        setProfile(profileData);
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
