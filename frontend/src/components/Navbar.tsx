// frontend/src/components/Navbar.tsx
import { type FC, useState } from 'react';
import { Link, NavLink, useLocation } from 'react-router-dom';
import Logo from './common/Logo';
import styles from '../styles/components/Navbar.module.css';
import { Menu, X } from 'lucide-react';
import { NavbarProps } from '../types';
import { useAppStore } from '../store/useStore';
import { APP_ROUTES } from '../api/constants';

const Navbar: FC<NavbarProps> = ({ transparent: _transparent }) => {
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
            to={APP_ROUTES.HOME}
            end
            className={({ isActive }) =>
              `${styles.link} ${isActive ? styles.active : ''}`
            }
          >
            Home
          </NavLink>
          <NavLink
            to={APP_ROUTES.ASTROPHOTOGRAPHY}
            className={({ isActive }) =>
              `${styles.link} ${isActive ? styles.active : ''}`
            }
          >
            Astrophotography
          </NavLink>
          {isProgrammingEnabled && (
            <NavLink
              to={APP_ROUTES.PROGRAMMING}
              className={({ isActive }) =>
                `${styles.link} ${isActive ? styles.active : ''}`
              }
            >
              Programming
            </NavLink>
          )}
          <Link to={`${APP_ROUTES.HOME}#about`} className={styles.link}>
            About
          </Link>
          <Link to={`${APP_ROUTES.HOME}#contact`} className={styles.link}>
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
            <div className={styles.drawerLinks}>
              <NavLink
                to={APP_ROUTES.HOME}
                onClick={toggleMenu}
                end
                className={({ isActive }) => (isActive ? styles.active : '')}
              >
                Home
              </NavLink>
              <NavLink
                to={APP_ROUTES.ASTROPHOTOGRAPHY}
                onClick={toggleMenu}
                className={({ isActive }) => (isActive ? styles.active : '')}
              >
                Astrophotography
              </NavLink>
              {isProgrammingEnabled && (
                <NavLink
                  to={APP_ROUTES.PROGRAMMING}
                  onClick={toggleMenu}
                  className={({ isActive }) => (isActive ? styles.active : '')}
                >
                  Programming
                </NavLink>
              )}
              <Link
                to={`${APP_ROUTES.HOME}#about`}
                onClick={toggleMenu}
                className={location.hash === '#about' ? styles.active : ''}
              >
                About
              </Link>
              <Link
                to={`${APP_ROUTES.HOME}#contact`}
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
