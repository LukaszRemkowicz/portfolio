import React from "react";
import styles from "./styles/components/ExperienceStats.module.css";

/**
 * TODO: Connect to backend API to fetch real experience statistics.
 */
const ExperienceStats: React.FC = () => {
  return (
    <div className={styles.stats}>
      <div className={styles.stat}>
        <span className={styles.number}>1.5M</span>
        <span className={styles.label}>PIXELS CAPTURED</span>
      </div>
      <div className={styles.divider}></div>
      <div className={styles.stat}>
        <span className={styles.number}>04</span>
        <span className={styles.label}>COUNTRIES TRAVELLED</span>
      </div>
      <div className={styles.divider}></div>
      <div className={styles.stat}>
        <span className={styles.number}>08</span>
        <span className={styles.label}>FEATURED GALLERIES</span>
      </div>
    </div>
  );
};

export default ExperienceStats;
