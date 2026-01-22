import React from 'react';
import Navbar from './Navbar';
import Footer from './Footer';
import styles from '../styles/components/App.module.css';
import { useLocation } from 'react-router-dom';
import { MainLayoutProps } from '../types';

const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const location = useLocation();
  const isAstroGallery = location.pathname === '/astrophotography';
  const isProgramming = location.pathname === '/programming';

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
