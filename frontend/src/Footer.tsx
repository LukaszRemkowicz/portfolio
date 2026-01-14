import React from "react";
import styles from "./styles/components/Footer.module.css";

const Footer: React.FC = () => {
  return (
    <footer className={styles.footer}>
      <div className={styles.container}>
        <div className={styles.branding}>
          <span className={styles.logoIcon}>✦</span>
          <span className={styles.logoText}>CELESTIAL CAPTURES</span>
        </div>

        <p className={styles.copyright}>
          © 2024 Alex Stargazer Portfolio. All Rights Reserved.
        </p>

        <div className={styles.socials}>
          <a href="#" className={styles.socialLink}>
            Instagram
          </a>
          <a href="#" className={styles.socialLink}>
            Twitter
          </a>
          <a href="#" className={styles.socialLink}>
            Email
          </a>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
