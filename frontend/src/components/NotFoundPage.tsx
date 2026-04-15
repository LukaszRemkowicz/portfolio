import { type FC } from 'react';
import { Link } from 'react-router-dom';
import { APP_ROUTES } from '../api/constants';
import SEO from './common/SEO';
import StarBackground from './StarBackground';
import styles from '../styles/components/Programming.module.css';

const NotFoundPage: FC = () => {
  return (
    <>
      <SEO
        title='Page Not Found'
        description='The requested page could not be found on this site.'
        robots='noindex, nofollow'
        includeCanonical={false}
      />
      <StarBackground />
      <section className={styles.section}>
        <header className={styles.header}>
          <h1 className={styles.title}>Page not found</h1>
          <p className={styles.subtitle}>
            The page you requested does not exist or is no longer available.
          </p>
        </header>

        <div className={styles.noResults}>
          <p>
            Return to the <Link to={APP_ROUTES.HOME}>homepage</Link> or explore{' '}
            <Link to={APP_ROUTES.ASTROPHOTOGRAPHY}>astrophotography</Link>.
          </p>
        </div>
      </section>
    </>
  );
};

export default NotFoundPage;
