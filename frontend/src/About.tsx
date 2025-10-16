import React, { useEffect, useState } from 'react';
import { fetchProfile } from './api/services';
import styles from './styles/components/About.module.css';
import { UserProfile } from './types';

const About: React.FC = () => {
  const [profile, setProfile] = useState<UserProfile | null>(null);

  useEffect(() => {
    const loadProfile = async (): Promise<void> => {
      try {
        const profileData: UserProfile = await fetchProfile();
        setProfile(profileData);
      } catch (e: unknown) {
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
          {profile.about_me_image && (
            <img
              src={profile.about_me_image}
              alt='About me'
              className={styles.aboutImage}
            />
          )}
        </div>
        <div className={styles.textWrapper}>
          <h2 className={styles.title}>About me</h2>
          {profile.bio?.split('\n').map((paragraph: string, index: number) => (
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
