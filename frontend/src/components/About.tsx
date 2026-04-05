import React from 'react';
import styles from '../styles/components/About.module.css';
import { Camera } from 'lucide-react';
import { AboutProps } from '../types';
import { sanitizeHtml } from '../utils/html';
import ImageWithFallback from './common/ImageWithFallback';
import Tooltip from './common/Tooltip';
import { useSettings } from '../hooks/useSettings';

import { useTranslation } from 'react-i18next';

const About: React.FC<AboutProps> = ({ profile }) => {
  const { t } = useTranslation();
  const { data: settings } = useSettings();
  const totalTimeSpent = settings?.total_time_spent;
  // Gracefull degradation: If profile is missing, render with defaults instead of returning null
  // if (!profile) return null;

  return (
    <section id='about' className={styles.section}>
      <div className={styles.container}>
        <div className={styles.info}>
          <h2 className={styles.title}>
            {t('about.title').split(' ').slice(0, 2).join(' ')} <br />
            <span className={styles.titleAccent}>
              {t('about.title').split(' ').slice(2).join(' ')}
            </span>
          </h2>
          <div className={styles.line}></div>
          <div
            className={styles.description}
            dangerouslySetInnerHTML={{
              __html: sanitizeHtml(profile?.bio || t('about.defaultBio')),
            }}
          />
          <div className={styles.stats}>
            <div className={styles.statItem}>
              <p className={styles.statValue}>Bortle 4</p>
              <p className={styles.statLabel}>{t('about.siteQuality')}</p>
            </div>
            <div className={styles.statItem}>
              <p className={styles.statValue}>430mm</p>
              <p className={styles.statLabel}>{t('about.primaryOptics')}</p>
            </div>
            {typeof totalTimeSpent === 'number' && totalTimeSpent > 0 ? (
              <div className={styles.statItem}>
                <Tooltip
                  content={t('about.totalTimeSpentTooltip')}
                  className={styles.tooltipTrigger}
                >
                  <p className={styles.statValue} tabIndex={0}>
                    {`${totalTimeSpent}h +`}
                  </p>
                </Tooltip>
                <p className={styles.statLabel}>{t('about.totalTimeSpent')}</p>
              </div>
            ) : null}
          </div>
        </div>
        <div className={styles.visual}>
          <div className={styles.glassCard}>
            <div className={styles.cardGradient}></div>
            {profile?.about_me_image ? (
              <ImageWithFallback
                src={profile.about_me_image}
                alt='About me'
                className={styles.aboutImage}
                width={400}
                height={400}
                draggable='false'
                onContextMenu={e => e.preventDefault()}
              />
            ) : (
              <Camera size={100} className={styles.cardIcon} />
            )}
          </div>
        </div>
      </div>
    </section>
  );
};

export default About;
