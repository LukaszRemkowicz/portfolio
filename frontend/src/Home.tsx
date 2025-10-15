import React from 'react';
import styles from './styles/components/App.module.css';
import { HomeProps } from './types';

const Home: React.FC<HomeProps> = ({ portraitUrl, firstName, lastName }) => {
  return (
    <>
      <section className={styles.hero}>
        <div className={styles.hero__headline}>
          Landscape and Astrophotography
          {(firstName || lastName) && (
            <div className={styles.hero__signature}>
              <div className={styles.hero__name}>{`${firstName} ${lastName}`.trim()}</div>
            </div>
          )}
        </div>
      </section>
      <img
        className={styles['astro-image']}
        src={portraitUrl}
        alt="Portrait"
        loading="lazy"
      />
    </>
  );
};

export default Home;
