import React from "react";
import styles from "../styles/components/App.module.css";
import { HomeProps } from "../types";
import ShootingStars from "./ShootingStars";

const Home: React.FC<HomeProps> = ({
  portraitUrl,
  shortDescription,
  backgroundUrl,
}) => {
  return (
    <header
      className={styles.heroSection}
      style={
        backgroundUrl
          ? {
            backgroundImage: `linear-gradient(rgba(2, 4, 10, 0.8), rgba(2, 4, 10, 0.8)), url(${backgroundUrl})`,
            backgroundSize: "cover",
            backgroundPosition: "center",
          }
          : undefined
      }
    >
      <ShootingStars />
      <div className={styles.heroContent}>
        <span className={styles.heroSubtitle}>Documenting the Cosmos</span>
        <h1 className={styles.heroTitle}>
          The Beauty of <br />
          <span className={styles.heroTitleAccent}>Ancient Light.</span>
        </h1>
        <p className={styles.heroDescription}>
          {shortDescription ||
            "I am a professional astrophotographer capturing the silent majesty of deep-space phenomena. My work bridges the gap between scientific observation and cinematic fine art."}
        </p>

        {portraitUrl && (
          <div className={styles.portraitWrapper}>
            <img
              src={portraitUrl}
              alt="Portrait"
              className={styles.heroPortrait}
            />
          </div>
        )}

        <div className={styles.heroActions}>
          <a href="/astrophotography" className={styles.primaryBtn}>
            View Portfolio
          </a>
          <a href="#about" className={styles.secondaryBtn}>
            About Me
          </a>
        </div>
      </div>
    </header>
  );
};

export default Home;
