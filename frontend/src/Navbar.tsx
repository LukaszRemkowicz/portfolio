import React, { useState, useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import styles from "./styles/components/Navbar.module.css";
import { NavbarProps } from "./types";

const Navbar: React.FC<NavbarProps> = ({ transparent }) => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);
  const location = useLocation();

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const toggleMenu = () => setIsMenuOpen(!isMenuOpen);

  return (
    <>
      <nav
        className={`${styles.navbar} ${isScrolled ? styles.scrolled : ""} ${transparent ? styles.transparent : ""}`}
      >
        <div className={styles.container}>
          <Link to="/" className={styles.logo}>
            <svg
              className={styles.logoIcon}
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z" />
              <path d="M5 3v4" />
              <path d="M19 17v4" />
              <path d="M3 5h4" />
              <path d="M17 19h4" />
            </svg>
            <span className={styles.logoText}>CELESTIAL</span>
          </Link>

          <div className={styles.links}>
            <a href="#gallery" className={styles.link}>
              Gallery
            </a>
            <a href="#about" className={styles.link}>
              About
            </a>
            <a href="#contact" className={styles.link}>
              Contact
            </a>
          </div>

          <button className={styles.menuTrigger} onClick={toggleMenu}>
            <div
              className={`${styles.hamburger} ${isMenuOpen ? styles.active : ""}`}
            ></div>
          </button>
        </div>
      </nav>

      <div
        className={`${styles.mobileDrawer} ${isMenuOpen ? styles.open : ""}`}
      >
        <button className={styles.closeBtn} onClick={toggleMenu}>
          ×
        </button>
        <div className={styles.drawerLinks}>
          <a href="#gallery" onClick={toggleMenu}>
            Gallery
          </a>
          <a href="#about" onClick={toggleMenu}>
            About
          </a>
          <a href="#contact" onClick={toggleMenu}>
            Contact
          </a>
        </div>
      </div>
    </>
  );
};

export default Navbar;
