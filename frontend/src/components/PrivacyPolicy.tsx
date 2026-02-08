// frontend/src/components/PrivacyPolicy.tsx
import React from 'react';
import SEO from './common/SEO';
import styles from '../styles/components/PrivacyPolicy.module.css';

const PrivacyPolicy: React.FC = () => {
  return (
    <div className={styles.container}>
      <SEO
        title='Privacy Policy'
        description='Privacy Policy and Cookie Notice'
      />
      <div className={styles.content}>
        <h1 className={styles.title}>Privacy Policy & Cookie Notice</h1>
        <p className={styles.lastUpdated}>Last updated: January 29, 2026</p>

        <section className={styles.section}>
          <h2>Introduction</h2>
          <p>
            This website is a personal portfolio showcasing my astrophotography,
            travel photography, and software development work. I respect your
            privacy and am committed to being transparent about how this site
            collects and uses data.
          </p>
        </section>

        <section className={styles.section}>
          <h2>What Data We Collect</h2>
          <p>
            This website uses Google Analytics to understand how visitors
            interact with the site. The following data is collected:
          </p>
          <ul>
            <li>
              <strong>Anonymous usage data:</strong> Pages viewed, time spent on
              pages, browser type, device type
            </li>
            <li>
              <strong>Geographic location:</strong> Country and city
              (approximate, based on IP address)
            </li>
            <li>
              <strong>Referral source:</strong> How you arrived at this website
            </li>
          </ul>
          <p className={styles.note}>
            <strong>Important:</strong> No personally identifiable information
            (PII) is collected. I cannot identify individual visitors.
          </p>
        </section>

        <section className={styles.section}>
          <h2>Cookies Used</h2>
          <p>Google Analytics sets the following cookies on your browser:</p>
          <div className={styles.cookieTable}>
            <div className={styles.cookieRow}>
              <div className={styles.cookieName}>_ga</div>
              <div className={styles.cookieDesc}>
                <strong>Purpose:</strong> Distinguishes unique visitors
                <br />
                <strong>Expiration:</strong> 2 years
              </div>
            </div>
            <div className={styles.cookieRow}>
              <div className={styles.cookieName}>_gid</div>
              <div className={styles.cookieDesc}>
                <strong>Purpose:</strong> Distinguishes unique visitors
                <br />
                <strong>Expiration:</strong> 24 hours
              </div>
            </div>
            <div className={styles.cookieRow}>
              <div className={styles.cookieName}>_gat</div>
              <div className={styles.cookieDesc}>
                <strong>Purpose:</strong> Throttles request rate
                <br />
                <strong>Expiration:</strong> 1 minute
              </div>
            </div>
          </div>
        </section>

        <section className={styles.section}>
          <h2>Why We Use Cookies</h2>
          <p>Analytics cookies help me understand:</p>
          <ul>
            <li>
              Which content is most popular (astrophotography vs. travel vs.
              programming)
            </li>
            <li>How visitors navigate the site</li>
            <li>What devices and browsers are being used</li>
            <li>Whether the site is performing well</li>
          </ul>
          <p>
            This information helps me improve the website and create better
            content for visitors.
          </p>
        </section>

        <section className={styles.section}>
          <h2>Your Choices & Rights</h2>
          <h3>Opt-Out Options:</h3>
          <ol>
            <li>
              <strong>Cookie Settings:</strong> Click &quot;Cookie
              Settings&quot; in the footer to change your consent at any time
            </li>
            <li>
              <strong>Browser Settings:</strong> Configure your browser to block
              cookies (note: this may affect site functionality)
            </li>
            <li>
              <strong>Google Analytics Opt-Out:</strong> Install the{' '}
              <a
                href='https://tools.google.com/dlpage/gaoptout'
                target='_blank'
                rel='noopener noreferrer'
                className={styles.link}
              >
                Google Analytics Opt-out Browser Add-on
              </a>
            </li>
          </ol>
        </section>

        <section className={styles.section}>
          <h2>Data Retention</h2>
          <p>
            Google Analytics data is retained for <strong>26 months</strong> by
            default. After this period, aggregated data is automatically
            deleted.
          </p>
        </section>

        <section className={styles.section}>
          <h2>Third-Party Services</h2>
          <p>
            For more detailed information, please refer to the privacy policies
            of these services, paying attention to specific sections, such as
            &quot;How we use your information&quot; or &quot;Third-party
            services&quot;.
          </p>
          <p>This website uses:</p>
          <ul>
            <li>
              <strong>Google Analytics:</strong> Web analytics service by Google
              LLC.{' '}
              <a
                href='https://policies.google.com/privacy'
                target='_blank'
                rel='noopener noreferrer'
                className={styles.link}
              >
                Google Privacy Policy
              </a>
            </li>
          </ul>
        </section>

        <section className={styles.section}>
          <h2>Contact</h2>
          <p>
            If you have questions about this privacy policy or how your data is
            handled, please contact me via the contact form on this website.
          </p>
        </section>

        <div className={styles.footer}>
          <p>
            This privacy policy is effective as of the date stated above and
            will remain in effect except with respect to any changes in its
            provisions in the future.
          </p>
        </div>
      </div>
    </div>
  );
};

export default PrivacyPolicy;
