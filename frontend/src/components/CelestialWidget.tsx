import React from "react";
import styles from "../styles/components/CelestialWidget.module.css";

/**
 * TODO: Connect to backend API to fetch real moon phase and weather conditions.
 */
const CelestialWidget: React.FC = () => {
  return (
    <div className={styles.widget}>
      <div className={styles.moonContainer}>
        <svg viewBox="0 0 100 100" className={styles.moonIcon}>
          <circle
            cx="50"
            cy="50"
            r="45"
            fill="none"
            stroke="currentColor"
            strokeWidth="1"
          />
          <path
            d="M50,5 A45,45 0 0,1 50,95 A30,45 0 0,0 50,5"
            fill="currentColor"
          />
        </svg>
      </div>
      <div className={styles.data}>
        <span className={styles.label}>MOON PHASE</span>
        <span className={styles.value}>Waxing Gibbous</span>
        <div className={styles.conditions}>
          <span className={styles.statusDot}></span>
          <span className={styles.statusText}>Excellent Visibility</span>
        </div>
      </div>
    </div>
  );
};

export default CelestialWidget;
