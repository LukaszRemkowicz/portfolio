import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import styles from "./styles/components/Navbar.module.css";
import { Sparkles, Menu, X } from "lucide-react";
import { fetchEnabledFeatures } from "./api/services";
import { NavbarProps } from "./types";

const Navbar: React.FC<NavbarProps> = ({ transparent: _transparent }) => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isProgrammingEnabled, setIsProgrammingEnabled] =
    useState<boolean>(false);

  useEffect(() => {
    const checkEnablement = async () => {
      try {
        const features = await fetchEnabledFeatures();
        setIsProgrammingEnabled(features.programming === true);
      } catch (error) {
        console.error("Failed to check programming enablement:", error);
        setIsProgrammingEnabled(false);
      }
    };
    checkEnablement();
  }, []);

  const toggleMenu = () => setIsMenuOpen(!isMenuOpen);

  return (
    <>
      <nav className={styles.navbar}>
        <Link to="/" className={styles.logo}>
          <Sparkles size={20} className={styles.logoIcon} />
          <span className={styles.logoText}>Celestial</span>
        </Link>

        <div className={styles.links}>
          <Link to="/astrophotography" className={styles.link}>
            Astrophotography
          </Link>
          {isProgrammingEnabled && (
            <Link to="/programming" className={styles.link}>
              Programming
            </Link>
          )}
          <a href="#about" className={styles.link}>
            About
          </a>
          <a href="#contact" className={styles.link}>
            Contact
          </a>
        </div>

        <button className={styles.menuTrigger} onClick={toggleMenu}>
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
              <Link to="/astrophotography" onClick={toggleMenu}>
                Astrophotography
              </Link>
              {isProgrammingEnabled && (
                <Link to="/programming" onClick={toggleMenu}>
                  Programming
                </Link>
              )}
              <a href="#about" onClick={toggleMenu}>
                About
              </a>
              <a href="#contact" onClick={toggleMenu}>
                Contact
              </a>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default Navbar;
