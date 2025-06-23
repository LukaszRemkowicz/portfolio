import React from 'react';
import { Link, NavLink } from 'react-router-dom';
import styles from './Navbar.module.css';

const DEFAULT_LOGO = '/logo.png';

const Navbar = () => {
    const getLinkClass = ({ isActive }) => {
      return isActive ? `${styles.navbar__link} ${styles.navbar__link_active}` : styles.navbar__link;
    };

    return (
        <nav className={styles.navbar}>
            <Link to="/" className={styles.navbar__logo_link}>
                <img src={DEFAULT_LOGO} alt="Logo" className={styles.navbar__logo} />
            </Link>
            <ul className={styles.navbar__links}>
                <li>
                  <NavLink to="/astrophotography" className={getLinkClass}>
                    Astrophotography
                  </NavLink>
                </li>
                <li>
                  <NavLink to="/programming" className={getLinkClass}>
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