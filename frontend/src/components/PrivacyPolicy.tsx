// frontend/src/components/PrivacyPolicy.tsx
import React from 'react';
import { useTranslation } from 'react-i18next';
import styles from '../styles/components/PrivacyPolicy.module.css';

const PrivacyPolicy: React.FC = () => {
  const { t } = useTranslation();

  return (
    <div className={styles.container}>
      <div className={styles.content}>
        <h1 className={styles.title}>{t('privacy.title')}</h1>
        <p className={styles.lastUpdated}>{t('privacy.lastUpdated')}</p>

        <section className={styles.section}>
          <h2>{t('privacy.introduction.title')}</h2>
          <p>{t('privacy.introduction.body')}</p>
        </section>

        <section className={styles.section}>
          <h2>{t('privacy.dataCollected.title')}</h2>
          <p>{t('privacy.dataCollected.intro')}</p>
          <ul>
            <li>
              <strong>
                {t('privacy.dataCollected.items.anonymous.label')}
              </strong>{' '}
              {t('privacy.dataCollected.items.anonymous.value')}
            </li>
            <li>
              <strong>{t('privacy.dataCollected.items.geo.label')}</strong>{' '}
              {t('privacy.dataCollected.items.geo.value')}
            </li>
            <li>
              <strong>{t('privacy.dataCollected.items.referral.label')}</strong>{' '}
              {t('privacy.dataCollected.items.referral.value')}
            </li>
          </ul>
          <p className={styles.note}>
            <strong>{t('privacy.dataCollected.note.label')}</strong>{' '}
            {t('privacy.dataCollected.note.value')}
          </p>
        </section>

        <section className={styles.section}>
          <h2>{t('privacy.cookiesUsed.title')}</h2>
          <p>{t('privacy.cookiesUsed.intro')}</p>
          <div className={styles.cookieTable}>
            <div className={styles.cookieRow}>
              <div className={styles.cookieName}>_ga</div>
              <div className={styles.cookieDesc}>
                <strong>{t('privacy.cookiesUsed.purpose')}</strong>{' '}
                {t('privacy.cookiesUsed.cookies.ga.purpose')}
                <br />
                <strong>{t('privacy.cookiesUsed.expiration')}</strong>{' '}
                {t('privacy.cookiesUsed.cookies.ga.expiration')}
              </div>
            </div>
            <div className={styles.cookieRow}>
              <div className={styles.cookieName}>_gid</div>
              <div className={styles.cookieDesc}>
                <strong>{t('privacy.cookiesUsed.purpose')}</strong>{' '}
                {t('privacy.cookiesUsed.cookies.gid.purpose')}
                <br />
                <strong>{t('privacy.cookiesUsed.expiration')}</strong>{' '}
                {t('privacy.cookiesUsed.cookies.gid.expiration')}
              </div>
            </div>
            <div className={styles.cookieRow}>
              <div className={styles.cookieName}>_gat</div>
              <div className={styles.cookieDesc}>
                <strong>{t('privacy.cookiesUsed.purpose')}</strong>{' '}
                {t('privacy.cookiesUsed.cookies.gat.purpose')}
                <br />
                <strong>{t('privacy.cookiesUsed.expiration')}</strong>{' '}
                {t('privacy.cookiesUsed.cookies.gat.expiration')}
              </div>
            </div>
          </div>
        </section>

        <section className={styles.section}>
          <h2>{t('privacy.whyCookies.title')}</h2>
          <p>{t('privacy.whyCookies.intro')}</p>
          <ul>
            <li>{t('privacy.whyCookies.items.popularContent')}</li>
            <li>{t('privacy.whyCookies.items.navigation')}</li>
            <li>{t('privacy.whyCookies.items.devices')}</li>
            <li>{t('privacy.whyCookies.items.performance')}</li>
          </ul>
          <p>{t('privacy.whyCookies.outro')}</p>
        </section>

        <section className={styles.section}>
          <h2>{t('privacy.rights.title')}</h2>
          <h3>{t('privacy.rights.optOutTitle')}</h3>
          <ol>
            <li>
              <strong>{t('privacy.rights.items.cookieSettings.label')}</strong>{' '}
              {t('privacy.rights.items.cookieSettings.value')}
            </li>
            <li>
              <strong>{t('privacy.rights.items.browserSettings.label')}</strong>{' '}
              {t('privacy.rights.items.browserSettings.value')}
            </li>
            <li>
              <strong>{t('privacy.rights.items.googleOptOut.label')}</strong>{' '}
              {t('privacy.rights.items.googleOptOut.prefix')}{' '}
              <a
                href='https://tools.google.com/dlpage/gaoptout'
                target='_blank'
                rel='noopener noreferrer'
                className={styles.link}
              >
                {t('privacy.rights.items.googleOptOut.link')}
              </a>
            </li>
          </ol>
        </section>

        <section className={styles.section}>
          <h2>{t('privacy.retention.title')}</h2>
          <p>{t('privacy.retention.body')}</p>
        </section>

        <section className={styles.section}>
          <h2>{t('privacy.thirdParty.title')}</h2>
          <p>{t('privacy.thirdParty.intro')}</p>
          <p>{t('privacy.thirdParty.uses')}</p>
          <ul>
            <li>
              <strong>{t('privacy.thirdParty.googleAnalytics.label')}</strong>{' '}
              {t('privacy.thirdParty.googleAnalytics.value')}{' '}
              <a
                href='https://policies.google.com/privacy'
                target='_blank'
                rel='noopener noreferrer'
                className={styles.link}
              >
                {t('privacy.thirdParty.googleAnalytics.link')}
              </a>
            </li>
          </ul>
        </section>

        <section className={styles.section}>
          <h2>{t('privacy.contact.title')}</h2>
          <p>{t('privacy.contact.body')}</p>
        </section>

        <div className={styles.footer}>
          <p>{t('privacy.footer')}</p>
        </div>
      </div>
    </div>
  );
};

export default PrivacyPolicy;
