import React from "react";
import styles from "./styles/components/StarBackground.module.css";

const StarBackground: React.FC = () => {
  return (
    <div className={styles.bgCanvas}>
      <div className={styles.nebulaTexture}></div>
      <div className={styles.starDensity}></div>
      <div className={styles.grainOverlay}></div>
    </div>
  );
};

export default StarBackground;
