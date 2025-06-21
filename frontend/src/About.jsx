import React, { useEffect, useState } from 'react';
import { fetchProfile } from './api/services';
import styles from './About.module.css';

const About = () => {
  const [profile, setProfile] = useState(null);

  useEffect(() => {
    const loadProfile = async () => {
      try {
        const profileData = await fetchProfile();
        setProfile(profileData);
      } catch (e) {
        console.error('Failed to load profile for About section:', e);
      }
    };
    loadProfile();
  }, []);

  if (!profile) {
    return null; // Or a loading spinner
  }

  return (
    <section className={styles.aboutContainer}>
      <div className={styles.aboutContent}>
        <div className={styles.imageWrapper}>
          {profile.about_me_image && <img src={profile.about_me_image} alt="About me" className={styles.aboutImage} />}
        </div>
        <div className={styles.textWrapper}>
          <h2 className={styles.title}>About me</h2>
          {profile.bio.split('\n').map((paragraph, index) => (
            <p key={index} className={index === 0 ? styles.subtitle : ''}>
              {paragraph}
            </p>
          ))}
        </div>
      </div>
    </section>
  );
};

export default About; 