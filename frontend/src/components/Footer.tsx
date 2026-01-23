import React from 'react';
import styles from '../styles/components/Footer.module.css';
import { Sparkles } from 'lucide-react';
import { useAppStore } from '../store/useStore';

const Footer: React.FC = () => {
  const { profile } = useAppStore();

  // Extract links from the ASTRO profile (or fallback to any found)
  const astroProfile = profile?.profiles?.find(p => p.type === 'ASTRO');
  const igUrl = astroProfile?.ig_url;
  const astrobinUrl = astroProfile?.astrobin_url;
  return (
    <footer className={styles.footer}>
      <div className={styles.container}>
        <div className={styles.branding}>
          <Sparkles size={16} className={styles.logoIcon} />
          <span className={styles.logoText}>Łukasz Remkowicz © 2026</span>
        </div>
        <div className={styles.links}>
          {igUrl && (
            <a
              href={igUrl}
              className={styles.link}
              target='_blank'
              rel='noopener noreferrer'
            >
              Instagram
            </a>
          )}
          {astrobinUrl && (
            <a
              href={astrobinUrl}
              className={styles.link}
              target='_blank'
              rel='noopener noreferrer'
            >
              Astrobin
            </a>
          )}
          {profile?.contact_email && (
            <a href={`mailto:${profile.contact_email}`} className={styles.link}>
              Email
            </a>
          )}
        </div>
      </div>
    </footer>
  );
};

export default Footer;
