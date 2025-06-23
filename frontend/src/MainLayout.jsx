import React from 'react';
import Navbar from './Navbar';
import Footer from './Footer';
import styles from './App.module.css';

const MainLayout = ({ children }) => {
  return (
    <div className={styles['app-container']} style={{ backgroundColor: '#181c2b' }}>
      <Navbar />
      <main>{children}</main>
      <Footer />
    </div>
  );
};

export default MainLayout; 