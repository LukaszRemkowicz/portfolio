import React from 'react';
import styles from '../styles/components/StarBackground.module.css';
import ShootingStars from './ShootingStars';
import ClientOnly from './common/ClientOnly';

const StarBackground: React.FC = () => {
  return (
    <div className={styles.bgCanvas}>
      <div className={styles.nebulaTexture}></div>
      <div className={styles.starDensity}></div>
      <ClientOnly>
        <ShootingStars />
      </ClientOnly>
      <div className={styles.grainOverlay}></div>
    </div>
  );
};

export default StarBackground;
