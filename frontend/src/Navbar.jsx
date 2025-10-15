<<<<<<< Updated upstream
import React, { useEffect, useState } from 'react';
import styles from './Navbar.module.css';
import { API_BASE_URL, API_ROUTES } from './api/routes';
=======
import React from 'react';
import { Link, NavLink, useLocation } from 'react-router-dom';
import styles from './styles/components/Navbar.module.css';
>>>>>>> Stashed changes

const DEFAULT_LOGO = '/logo.png';

const Navbar = () => {
  const [logoUrl, setLogoUrl] = useState(DEFAULT_LOGO);

  useEffect(() => {
    const fetchLogo = async () => {
      if (!API_ROUTES.logo) return;
      try {
        const res = await fetch(API_BASE_URL + API_ROUTES.logo);
        if (!res.ok) throw new Error('API error');
        const data = await res.json();
        if (data?.url) setLogoUrl(data.url);
      } catch (e) {
        setLogoUrl(DEFAULT_LOGO);
      }
    };
    fetchLogo();
  }, []);

  return (
    <nav className={styles.navbar}>
      <img
        src={logoUrl}
        alt="Logo"
        className={styles.navbar__logo}
        height={150}
        style={{
          background: 'none',
          filter: 'drop-shadow(0 2px 8px rgba(0,0,0,0.25))',
          border: 'none',
          display: 'block',
        }}
      />
      <ul className={styles.navbar__links}>
        <li><a className={styles.navbar__link} href="#">Astrophotography</a></li>
        <li><a className={styles.navbar__link} href="#">Programming</a></li>
        <li><a className={styles.navbar__link} href="#">Contact</a></li>
      </ul>
    </nav>
  );
};

export default Navbar; 