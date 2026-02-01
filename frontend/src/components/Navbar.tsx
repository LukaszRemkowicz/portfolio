// frontend/src/components/Navbar.tsx
import { type FC, useState } from 'react';
import { Link, NavLink, useLocation } from 'react-router-dom';
import Logo from './common/Logo';
import styles from '../styles/components/Navbar.module.css';
import { Menu, X } from 'lucide-react';
import { NavbarProps } from '../types';
import { useAppStore } from '../store/useStore';
import { APP_ROUTES } from '../api/constants';

import LanguageSwitcher from './common/LanguageSwitcher';

import { useTranslation } from 'react-i18next';

const Navbar: FC<NavbarProps> = ({ transparent: _transparent }) => {
  const { t } = useTranslation();
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
              `${styles.link} ${isActive && !location.hash ? styles.active : ''}`
            }
            onClick={() => {
              requestAnimationFrame(() => {
                const root = document.getElementById('root');
                if (root) root.scrollTo({ top: 0, behavior: 'smooth' });
                window.scrollTo({ top: 0, behavior: 'smooth' });
                document.documentElement.scrollTo({
                  top: 0,
                  behavior: 'smooth',
                });
                document.body.scrollTo({ top: 0, behavior: 'smooth' });
              });
            }}
          >
            {t('nav.home')}
          </NavLink>
          <NavLink
            to={APP_ROUTES.ASTROPHOTOGRAPHY}
            className={({ isActive }) =>
              `${styles.link} ${isActive ? styles.active : ''}`
            }
          >
            {t('nav.astrophotography')}
          </NavLink>
          {isProgrammingEnabled && (
            <NavLink
              to={APP_ROUTES.PROGRAMMING}
              className={({ isActive }) =>
                `${styles.link} ${isActive ? styles.active : ''}`
              }
            >
              {t('nav.programming')}
            </NavLink>
          )}
          <Link
            to={`${APP_ROUTES.HOME}#about`}
            className={`${styles.link} ${location.hash === '#about' ? styles.active : ''}`}
          >
            {t('nav.about')}
          </Link>
          <Link
            to={`${APP_ROUTES.HOME}#contact`}
            className={`${styles.link} ${location.hash === '#contact' ? styles.active : ''}`}
          >
            {t('nav.contact')}
          </Link>
        </div>

        <div className={styles.controls}>
          <LanguageSwitcher />
          <button
            className={styles.menuTrigger}
            onClick={toggleMenu}
            aria-label={isMenuOpen ? 'Close menu' : 'Open menu'}
            aria-expanded={isMenuOpen}
          >
            {isMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
      </nav>

      {isMenuOpen && (
        <div className={styles.mobileDrawer}>
          <div className={styles.mobileDrawerContent}>
            <div className={styles.drawerLinks}>
              <NavLink
                to={APP_ROUTES.HOME}
                onClick={() => {
                  toggleMenu();
                  requestAnimationFrame(() => {
                    const root = document.getElementById('root');
                    if (root) root.scrollTo({ top: 0, behavior: 'smooth' });
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                    document.documentElement.scrollTo({
                      top: 0,
                      behavior: 'smooth',
                    });
                    document.body.scrollTo({ top: 0, behavior: 'smooth' });
                  });
                }}
                end
                className={({ isActive }) =>
                  isActive && !location.hash ? styles.active : ''
                }
              >
                {t('nav.home')}
              </NavLink>
              <NavLink
                to={APP_ROUTES.ASTROPHOTOGRAPHY}
                onClick={toggleMenu}
                className={({ isActive }) => (isActive ? styles.active : '')}
              >
                {t('nav.astrophotography')}
              </NavLink>
              {isProgrammingEnabled && (
                <NavLink
                  to={APP_ROUTES.PROGRAMMING}
                  onClick={toggleMenu}
                  className={({ isActive }) => (isActive ? styles.active : '')}
                >
                  {t('nav.programming')}
                </NavLink>
              )}
              <Link
                to={`${APP_ROUTES.HOME}#about`}
                onClick={toggleMenu}
                className={location.hash === '#about' ? styles.active : ''}
              >
                {t('nav.about')}
              </Link>
              <Link
                to={`${APP_ROUTES.HOME}#contact`}
                onClick={toggleMenu}
                className={location.hash === '#contact' ? styles.active : ''}
              >
                {t('nav.contact')}
              </Link>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default Navbar;
