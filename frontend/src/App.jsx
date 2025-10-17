import React, { useEffect, useState } from 'react';
import Navbar from './Navbar';
import Footer from './Footer';
import Gallery from './Gallery';
import About from './About';
import styles from './App.module.css';
import { fetchBackground, fetchProfile } from './api/services';

const DEFAULT_PORTRAIT = '/portrait.jpeg';

const App = () => {
  const [portraitUrl, setPortraitUrl] = useState(DEFAULT_PORTRAIT);
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [backgroundUrl, setBackgroundUrl] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        const profile = await fetchProfile();
        if (profile.avatar) {
          setPortraitUrl(profile.avatar);
        }
        setFirstName(profile.first_name || '');
        setLastName(profile.last_name || '');

        const background = await fetchBackground();
        setBackgroundUrl(background);

      } catch (e) {
        console.error('Failed to load initial data:', e);
        setError('Failed to load page content. Please try again later.');
        setPortraitUrl(DEFAULT_PORTRAIT);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  const appContainerStyle = backgroundUrl ? {
    backgroundImage: `url(${backgroundUrl})`,
    backgroundSize: 'cover',
    backgroundPosition: 'center',
    backgroundAttachment: 'fixed',
  } : {};

  if (loading) {
    return <div className={styles['loading-indicator']}>Loading...</div>;
  }

  if (error) {
    return <div className={styles['error-message']}>{error}</div>;
  }

  return (
    <div className={styles['app-container']}>
      <div className={styles['hero-viewport']} style={appContainerStyle}>
        <header className={styles['header-container']}>
          <Navbar />
        </header>
        <main className={styles['main-content']}>
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
        </main>
        <Gallery />
      </div>

      <About />
      <Footer />
    </div>
  );
};

export default App;