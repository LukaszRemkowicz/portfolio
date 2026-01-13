import React, { useEffect, useState } from "react";
import Home from "./Home";
import About from "./About";
import Contact from "./Contact";
import Navbar from "./Navbar";
import Footer from "./Footer";
import Gallery from "./Gallery";
import PrelectionsAndCourses from "./PrelectionsAndCourses";
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
        const profileData: UserProfile = await fetchProfile();
        setProfile(profileData);

        const background: string | null = await fetchBackground();
        setBackgroundUrl(background);
      } catch (e: unknown) {
        console.error("Failed to load initial data:", e);
        setError("Failed to load page content. Please try again later.");
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  const heroViewportStyle: React.CSSProperties = backgroundUrl
    ? {
        backgroundImage: `url(${backgroundUrl})`,
        backgroundSize: "cover",
        backgroundPosition: "center",
        backgroundAttachment: "fixed",
      }
    : {};

  if (loading)
    return <div className={styles["loading-indicator"]}>Loading...</div>;
  if (error) return <div className={styles["error-message"]}>{error}</div>;

  return (
    <>
      <div className={styles["hero-viewport"]} style={heroViewportStyle}>
        <Navbar transparent />
        <main className={styles["main-content"]}>
          <Home
            portraitUrl={profile?.avatar || DEFAULT_PORTRAIT}
            firstName={profile?.first_name || ""}
            lastName={profile?.last_name || ""}
          />
        </main>
        <Gallery />
      </div>
      <About profile={profile} />
      {profile?.prelections && <PrelectionsAndCourses />}
      <Contact />
      <Footer />
    </>
  );
};

export default HomePage;
