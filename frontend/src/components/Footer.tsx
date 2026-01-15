import React from "react";
import styles from "../styles/components/Footer.module.css";
import { Sparkles } from "lucide-react";

const Footer: React.FC = () => {
  return (
    <footer className={styles.footer}>
      <div className={styles.container}>
        <div className={styles.branding}>
          <Sparkles size={16} className={styles.logoIcon} />
          <span className={styles.logoText}>Celestial © 2024</span>
        </div>
        <div className={styles.links}>
          <a href="#" className={styles.link}>
            Instagram
          </a>
          <a href="#" className={styles.link}>
            Astrobin
          </a>
          <a href="#" className={styles.link}>
            Email
          </a>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
