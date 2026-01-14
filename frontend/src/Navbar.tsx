import React, { useState, useEffect } from "react";
import { Link, NavLink, useLocation } from "react-router-dom";
import styles from "./styles/components/Navbar.module.css";
import { NavbarProps, NavLinkClassProps } from "./types";
import { ASSETS } from "./api/routes";
import { fetchEnabledFeatures } from "./api/services";

const Navbar: React.FC<NavbarProps> = ({ transparent, programmingBg }) => {
  const location = useLocation();
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

  const getLinkClass = ({ isActive }: NavLinkClassProps): string => {
    return isActive
      ? `${styles.navbar__link} ${styles.navbar__link_active}`
      : styles.navbar__link;
  };

  const handleContactClick = (e: React.MouseEvent<HTMLAnchorElement>) => {
    e.preventDefault();
    const contactSection = document.getElementById("contact");
    if (contactSection) {
      contactSection.scrollIntoView({ behavior: "smooth" });
    }
  };

  const navbarStyle: React.CSSProperties =
    transparent && programmingBg
      ? {
          backgroundImage: `url(${ASSETS.underConstruction})`,
          backgroundSize: "contain",
          backgroundRepeat: "no-repeat",
          backgroundPosition: "center",
        }
      : {};

  return (
    <nav
      className={`${styles.navbar} ${transparent ? styles.transparent : ""} ${
        programmingBg ? styles.programmingBg : ""
      }`}
      style={navbarStyle}
    >
      <Link to="/" className={styles.navbar__logo_link}>
        <img src={ASSETS.logo} alt="Logo" className={styles.navbar__logo} />
      </Link>
      <ul className={styles.navbar__links}>
        <li>
          <NavLink
            to="/astrophotography"
            className={
              location.pathname === "/astrophotography"
                ? styles.active
                : getLinkClass({
                    isActive: location.pathname === "/astrophotography",
                  })
            }
          >
            Astrophotography
          </NavLink>
        </li>
        {isProgrammingEnabled && (
          <li>
            <NavLink
              to="/programming"
              className={
                location.pathname === "/programming"
                  ? styles.active
                  : getLinkClass({
                      isActive: location.pathname === "/programming",
                    })
              }
            >
              Programming
            </NavLink>
          </li>
        )}
        <li>
          <a
            href="#contact"
            className={getLinkClass({ isActive: false })}
            onClick={handleContactClick}
          >
            Contact
          </a>
        </li>
      </ul>
    </nav>
  );
};

export default Navbar;
