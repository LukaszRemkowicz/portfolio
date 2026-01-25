// frontend/src/components/MainLayout.tsx
import { type FC } from 'react';
import Navbar from './Navbar';
import Footer from './Footer';
import styles from '../styles/components/App.module.css';
import { useLocation } from 'react-router-dom';
import { MainLayoutProps } from '../types';
import { APP_ROUTES } from '../api/constants';

const MainLayout: FC<MainLayoutProps> = ({ children }) => {
  const location = useLocation();
  const isAstroGallery = location.pathname === APP_ROUTES.ASTROPHOTOGRAPHY;
  const isProgramming = location.pathname === APP_ROUTES.PROGRAMMING;

  return (
    <div
      className={`${styles['app-container']} ${
        isProgramming ? styles['programming-bg'] : styles['astro-bg']
      }`}
      style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}
    >
      <Navbar
        transparent={isAstroGallery || isProgramming}
        programmingBg={isProgramming}
      />
      <main style={{ flex: 1 }}>{children}</main>
      <Footer />
    </div>
  );
};

export default MainLayout;
