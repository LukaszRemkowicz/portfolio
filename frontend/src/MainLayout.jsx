import React from 'react';
import Navbar from './Navbar';
import Footer from './Footer';
import styles from './App.module.css';
import { useLocation } from 'react-router-dom';

const MainLayout = ({ children }) => {
  const location = useLocation();
  const isAstroGallery = location.pathname === '/astrophotography';
  const isProgramming = location.pathname === '/programming';
  return (
    <div className={styles['app-container']} style={{ backgroundColor: isProgramming ? '#000' : '#181c2b' }}>
      <Navbar transparent={isAstroGallery || isProgramming} programmingBg={isProgramming} />
      <main>{children}</main>
      <Footer />
    </div>
  );
};

export default MainLayout; 