import React from 'react';
import { Link, NavLink, useLocation } from 'react-router-dom';
import styles from './styles/components/Navbar.module.css';
import { NavbarProps, NavLinkClassProps } from './types';

const DEFAULT_LOGO = '/logo.png';

const Navbar: React.FC<NavbarProps> = ({ transparent, programmingBg }) => {
  const location = useLocation();

  const getLinkClass = ({ isActive }: NavLinkClassProps): string => {
    return isActive ? `${styles.navbar__link} ${styles.navbar__link_active}` : styles.navbar__link;
  };

  const navbarStyle: React.CSSProperties = transparent && programmingBg
    ? {
        backgroundImage: `url('/underconstruction.jpg')`,
        backgroundSize: 'contain',
        backgroundRepeat: 'no-repeat',
        backgroundPosition: 'center',
      }
    : {};

  const handleContactClick = (e: React.MouseEvent<HTMLAnchorElement>) => {
    e.preventDefault();
    const contactSection = document.getElementById('contact');
    if (contactSection) {
      contactSection.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <nav className={`${styles.navbar} ${transparent ? styles.transparent : ''}`}
         style={navbarStyle}>
      <Link to="/" className={styles.navbar__logo_link}>
        <img src={DEFAULT_LOGO} alt="Logo" className={styles.navbar__logo} />
      </Link>
      <ul className={styles.navbar__links}>
        <li>
          <NavLink 
            to="/astrophotography" 
            className={location.pathname === '/astrophotography' ? styles.active : getLinkClass}
          >
            Astrophotography
          </NavLink>
        </li>
        <li>
          <NavLink 
            to="/programming" 
            className={location.pathname === '/programming' ? styles.active : getLinkClass}
          >
            Programming
          </NavLink>
        </li>
        <li>
          <a 
            href="#contact" 
            className={getLinkClass}
            onClick={handleContactClick}
          >
            Contact
          </a>
        </li>
      </ul>
    </nav>
  );
};

export default Navbar;
