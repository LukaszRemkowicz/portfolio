import React from 'react';
import { Link, NavLink, useLocation } from 'react-router-dom';
import styles from './Navbar.module.css';

const DEFAULT_LOGO = '/logo.png';

const Navbar = ({ transparent }) => {
    const location = useLocation();

    const getLinkClass = ({ isActive }) => {
      return isActive ? `${styles.navbar__link} ${styles.navbar__link_active}` : styles.navbar__link;
    };

    return (
        <nav className={`${styles.navbar} ${transparent ? styles.transparent : ''}`}>
            <Link to="/" className={styles.navbar__logo_link}>
                <img src={DEFAULT_LOGO} alt="Logo" className={styles.navbar__logo} />
            </Link>
            <ul className={styles.navbar__links}>
                <li>
                  <NavLink to="/astrophotography" className={location.pathname === '/astrophotography' ? styles.active : getLinkClass}>
                    Astrophotography
                  </NavLink>
                </li>
                <li>
                  <NavLink to="/programming" className={location.pathname === '/programming' ? styles.active : getLinkClass}>
                    Programming
                  </NavLink>
                </li>
                <li>
                  <NavLink to="/contact" className={getLinkClass}>
                    Contact
                  </NavLink>
                </li>
            </ul>
        </nav>
    );
};

export default Navbar; 