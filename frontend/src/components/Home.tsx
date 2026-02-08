// frontend/src/components/Home.tsx
import { type FC } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import styles from '../styles/components/App.module.css';
import { HomeProps } from '../types';
import ShootingStars from './ShootingStars';
import { APP_ROUTES } from '../api/constants';

const Home: FC<HomeProps> = ({
  portraitUrl,
  shortDescription,
  backgroundUrl,
}) => {
  const { t } = useTranslation();
  const displayDescription = shortDescription || t('hero.defaultDescription');
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
        <span className={styles.heroSubtitle}>{t('hero.subtitle')}</span>
        <h1 className={styles.heroTitle}>
          {t('hero.titlePart1')} <br />
          <span className={styles.heroTitleAccent}>{t('hero.titlePart2')}</span>
        </h1>
        <p className={styles.heroDescription}>{displayDescription}</p>

        {portraitUrl && (
          <div className={styles.portraitWrapper}>
            <img
              src={portraitUrl}
              alt='Portrait'
              className={styles.heroPortrait}
              loading='eager'
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              {...({ fetchpriority: 'high' } as any)}
              draggable='false'
              onContextMenu={e => e.preventDefault()}
            />
          </div>
        )}

        <div className={styles.heroActions}>
          <Link to={APP_ROUTES.ASTROPHOTOGRAPHY} className={styles.primaryBtn}>
            {t('hero.viewPortfolio')}
          </Link>
          <a href='#about' className={styles.secondaryBtn}>
            {t('hero.aboutMe')}
          </a>
        </div>
      </div>
    </section>
  );
};

export default Home;
