import React from 'react';
import { Link } from 'react-router-dom';
import styles from '../styles/components/App.module.css';
import { HomeProps } from '../types';
import ShootingStars from './ShootingStars';

const Home: React.FC<HomeProps> = ({
  portraitUrl,
  shortDescription = 'I am a professional astrophotographer capturing the silent majesty of deep-space phenomena. My work bridges the gap between scientific observation and cinematic fine art.',
  backgroundUrl,
}) => {
  return (
    <section
      id='home'
      className={styles.heroSection}
      style={
        backgroundUrl
          ? {
              backgroundImage: `linear-gradient(rgba(2, 4, 10, 0.8), rgba(2, 4, 10, 0.8)), url(${backgroundUrl})`,
              backgroundSize: 'cover',
              backgroundPosition: 'center',
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
        <p className={styles.heroDescription}>{shortDescription}</p>

        {portraitUrl && (
          <div className={styles.portraitWrapper}>
            <img
              src={portraitUrl}
              alt='Portrait'
              className={styles.heroPortrait}
              loading='eager'
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              {...({ fetchpriority: 'high' } as any)}
            />
          </div>
        )}

        <div className={styles.heroActions}>
          <Link to='/astrophotography' className={styles.primaryBtn}>
            View Portfolio
          </Link>
          <a href='#about' className={styles.secondaryBtn}>
            About Me
          </a>
        </div>
      </div>
    </section>
  );
};

export default Home;
