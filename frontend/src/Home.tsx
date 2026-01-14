import React from "react";
import styles from "./styles/components/App.module.css";
import { HomeProps } from "./types";

const Home: React.FC<HomeProps> = ({ portraitUrl, shortDescription }) => {
  return (
    <div className={styles.heroContainer}>
      <div className={styles.heroGlowLeft}></div>
      <div className={styles.planetIcon}>
        <svg width="200" height="200" viewBox="0 0 200 200">
          <circle
            cx="100"
            cy="100"
            r="80"
            fill="none"
            stroke="white"
            strokeWidth="0.5"
            strokeDasharray="4 4"
          />
          <circle cx="100" cy="100" r="40" fill="url(#planetGradient)" />
          <defs>
            <radialGradient id="planetGradient">
              <stop offset="0%" stopColor="#38bdf8" />
              <stop offset="100%" stopColor="#1e1b4b" />
            </radialGradient>
          </defs>
        </svg>
      </div>

      <h1 className={styles.heroTitle}>
        Capturing the <span className={styles.accent}>Cosmos</span>
      </h1>

      <p className={styles.heroSub}>
        I am a dedicated astrophotographer exploring the silent beauty of our
        universe through long-exposure imagery. My work bridges the gap between
        scientific observation and fine art.
      </p>

      <div className={styles.heroActions}>
        <a href="#gallery" className={styles.primaryBtn}>
          View Collection
        </a>
        <a href="#about" className={styles.secondaryBtn}>
          My Story
        </a>
      </div>
    </div>
  );
};

export default Home;
