import React, { useState } from 'react';
import { Link, NavLink, useLocation } from 'react-router-dom';
import Logo from './common/Logo';
import styles from '../styles/components/Navbar.module.css';
import { Menu, X } from 'lucide-react';
import { NavbarProps } from '../types';
import { useAppStore } from '../store/useStore';

const Navbar: React.FC<NavbarProps> = ({ transparent: _transparent }) => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const location = useLocation();
  const { features } = useAppStore();
  const isProgrammingEnabled = features?.programming === true;

  const toggleMenu = () => setIsMenuOpen(!isMenuOpen);

  return (
    <>
      <nav className={styles.navbar}>
        <Logo />

        <div className={styles.links}>
          <NavLink
            to='/'
            end
            className={({ isActive }) =>
              `${styles.link} ${isActive ? styles.active : ''}`
            }
          >
            Home
          </NavLink>
          <NavLink
            to='/astrophotography'
            className={({ isActive }) =>
              `${styles.link} ${isActive ? styles.active : ''}`
            }
          >
            Astrophotography
          </NavLink>
          {isProgrammingEnabled && (
            <NavLink
              to='/programming'
              className={({ isActive }) =>
                `${styles.link} ${isActive ? styles.active : ''}`
              }
            >
              Programming
            </NavLink>
          )}
          <Link to='/#about' className={styles.link}>
            About
          </Link>
          <Link to='/#contact' className={styles.link}>
            Contact
          </Link>
        </div>

        <button
          className={styles.menuTrigger}
          onClick={toggleMenu}
          aria-label={isMenuOpen ? 'Close menu' : 'Open menu'}
          aria-expanded={isMenuOpen}
        >
          {isMenuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </nav>

      {isMenuOpen && (
        <div className={styles.mobileDrawer}>
          <div className={styles.mobileDrawerContent}>
            <button className={styles.closeDrawer} onClick={toggleMenu}>
              <X size={24} />
            </button>
            <div className={styles.drawerLinks}>
              <NavLink
                to='/'
                onClick={toggleMenu}
                end
                className={({ isActive }) => (isActive ? styles.active : '')}
              >
                Home
              </NavLink>
              <NavLink
                to='/astrophotography'
                onClick={toggleMenu}
                className={({ isActive }) => (isActive ? styles.active : '')}
              >
                Astrophotography
              </NavLink>
              {isProgrammingEnabled && (
                <NavLink
                  to='/programming'
                  onClick={toggleMenu}
                  className={({ isActive }) => (isActive ? styles.active : '')}
                >
                  Programming
                </NavLink>
              )}
              <Link
                to='/#about'
                onClick={toggleMenu}
                className={location.hash === '#about' ? styles.active : ''}
              >
                About
              </Link>
              <Link
                to='/#contact'
                onClick={toggleMenu}
                className={location.hash === '#contact' ? styles.active : ''}
              >
                Contact
              </Link>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default Navbar;
