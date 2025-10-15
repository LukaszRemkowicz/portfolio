import React, { useEffect, useState } from 'react';
import Home from './Home';
import About from './About';
import Navbar from './Navbar';
import Footer from './Footer';
import Gallery from './Gallery';

import styles from './styles/components/App.module.css';
import { fetchProfile, fetchBackground } from './api/services';
const DEFAULT_PORTRAIT = '/portrait_default.png';

const HomePage = () => {
  const [portraitUrl, setPortraitUrl] = useState(DEFAULT_PORTRAIT);
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [backgroundUrl, setBackgroundUrl] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        const profile = await fetchProfile();
        if (profile.avatar) setPortraitUrl(profile.avatar);
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

  const heroViewportStyle = backgroundUrl
    ? {
        backgroundImage: `url(${backgroundUrl})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundAttachment: 'fixed',
      }
    : {};

  if (loading) return <div className={styles['loading-indicator']}>Loading...</div>;
  if (error) return <div className={styles['error-message']}>{error}</div>;

  return (
      <>
        <div className={styles['hero-viewport']} style={heroViewportStyle}>
            <Navbar transparent />
            <main className={styles['main-content']}>
                <Home
                    portraitUrl={portraitUrl}
                    firstName={firstName}
                    lastName={lastName}
                />
            </main>
            <Gallery />
        </div>
        <About />
        <Footer />
      </>
  );
};

export default HomePage; 