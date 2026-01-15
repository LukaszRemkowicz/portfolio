import React, { useState } from "react";
import { Link } from "react-router-dom";
import Logo from "./common/Logo";
import styles from "../styles/components/Navbar.module.css";
import { Menu, X } from "lucide-react";
import { NavbarProps } from "../types";
import { useAppStore } from "../store/useStore";

const Navbar: React.FC<NavbarProps> = ({ transparent: _transparent }) => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const { features } = useAppStore();
  const isProgrammingEnabled = features?.programming === true;

  const toggleMenu = () => setIsMenuOpen(!isMenuOpen);

  return (
    <>
      <nav className={styles.navbar}>
        <Logo />

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

        <button
          className={styles.menuTrigger}
          onClick={toggleMenu}
          aria-label={isMenuOpen ? "Close menu" : "Open menu"}
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
