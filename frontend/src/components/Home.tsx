// frontend/src/components/Home.tsx
import { type FC, useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import styles from '../styles/components/App.module.css';
import { HomeProps } from '../types';
// - [x] Remove redundant `frontend_upstream` from `TEMPLATE.conf`
// - [x] Finalize commit message and implementation plan alignment
// - [x] Final Polish & Documentation
import ShootingStars from './ShootingStars';
import { APP_ROUTES } from '../api/constants';
import ImageWithFallback from './common/ImageWithFallback';
import ClientOnly from './common/ClientOnly';

const Home: FC<HomeProps> = ({
  portraitUrl,
  shortDescription,
  backgroundUrl,
}) => {
  const { t } = useTranslation();
  const [isLoaded, setIsLoaded] = useState(false);

  const displayDescription = shortDescription || t('hero.defaultDescription');

  // SSR-safe check for already loaded images (e.g. from cache)
  useEffect(() => {
    const img = document.querySelector(
      '[data-testid="hero-background-image"]'
    ) as HTMLImageElement;
    if (img?.complete) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setIsLoaded(true);
    }
  }, []);

  return (
    <section id='home' className={styles.heroSection}>
      {backgroundUrl && (
        <>
          <img
            src={backgroundUrl}
            alt=''
            aria-hidden='true'
            data-testid='hero-background-image'
            className={styles.heroBackgroundImage}
            onLoad={() => setIsLoaded(true)}
            loading='eager'
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            {...({ fetchpriority: 'high' } as any)}
            style={{ opacity: isLoaded ? 1 : 0 }}
          />
          <div className={styles.heroBackgroundOverlay} />
        </>
      )}
      <ClientOnly>
        <ShootingStars />
      </ClientOnly>
      <div className={styles.heroContent}>
        <span className={styles.heroSubtitle}>{t('hero.subtitle')}</span>
        <h1 className={styles.heroTitle}>
          {t('hero.titlePart1')} <br />
          <span className={styles.heroTitleAccent}>{t('hero.titlePart2')}</span>
        </h1>
        <p className={styles.heroDescription}>{displayDescription}</p>

        {portraitUrl && (
          <div className={styles.portraitWrapper}>
            <ImageWithFallback
              src={portraitUrl}
              alt='Portrait'
              className={styles.heroPortrait}
              width={140}
              height={140}
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
