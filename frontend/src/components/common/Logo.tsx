import React from "react";
import { Link } from "react-router-dom";
import styles from "../../styles/components/Logo.module.css";

const Logo: React.FC = () => {
  return (
    <Link to="/" className={styles.logo}>
      <div className={styles.logoMarkWrapper}>
        <svg
          width="48"
          height="48"
          viewBox="0 0 100 100"
          className={styles.logoMark}
        >
          {/* Technical Circle Background */}
          <circle
            cx="50"
            cy="50"
            r="48"
            className={styles.logoCircleBg}
            stroke="white"
            strokeWidth="0.5"
            opacity="0.1"
          />
          {/* Coordinate Ring */}
          <circle
            cx="50"
            cy="50"
            r="44"
            stroke="#38bdf8"
            strokeWidth="0.5"
            fill="none"
            opacity="0.3"
            strokeDasharray="1 3"
            className={styles.logoCoordRing}
            aria-hidden="true"
          />

          <g className={styles.celestialElements} aria-hidden="true">
            {/* Crescent Moon */}
            <path
              d="M35 25 A15 15 0 1 1 35 55 A12 12 0 1 0 35 25"
              fill="white"
              opacity="0.9"
            />
            {/* Twinkling Stars */}
            <path
              d="M75 15 L76 18 L79 19 L76 20 L75 23 L74 20 L71 19 L74 18 Z"
              fill="white"
              className={styles.starTwinkle}
            />
            <path
              d="M85 35 L85.5 37 L87 37.5 L85.5 38 L85 40 L84.5 38 L83 37.5 L84.5 37 Z"
              fill="white"
              className={styles.starTwinkleDelayed}
            />
            <circle cx="15" cy="40" r="1" fill="white" opacity="0.6" />
            <circle cx="20" cy="15" r="0.8" fill="white" opacity="0.4" />
          </g>

          {/* Telescope Image */}
          <foreignObject x="15" y="15" width="70" height="70">
            <img
              src="/telescope.png"
              alt="Telescope"
              className={styles.logoImage}
            />
          </foreignObject>
        </svg>
      </div>
      <div className={styles.logoTextWrapper}>
        <div className={styles.logoNameWrapper}>
          <span className={styles.logoName}>Łukasz Remkowicz</span>
        </div>
        <div className={styles.logoSubtitleWrapper}>
          <div className={styles.logoAccentLine}></div>
          <span className={styles.logoSubtitle}>Astrophotography</span>
        </div>
      </div>
    </Link>
  );
};

export default Logo;
