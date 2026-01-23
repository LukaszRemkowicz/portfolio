import React from 'react';
import styles from '../styles/components/StarBackground.module.css';
import ShootingStars from './ShootingStars';

const StarBackground: React.FC = () => {
  return (
    <div className={styles.bgCanvas}>
      <div className={styles.nebulaTexture}></div>
      <div className={styles.starDensity}></div>
      <ShootingStars />
      <div className={styles.grainOverlay}></div>
    </div>
  );
};

export default StarBackground;
