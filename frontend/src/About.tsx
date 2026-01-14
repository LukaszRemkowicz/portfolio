import React from "react";
import styles from "./styles/components/About.module.css";
import { Camera } from "lucide-react";
import { AboutProps } from "./types";

const About: React.FC<AboutProps> = ({ profile }) => {
  if (!profile) return null;

  return (
    <section id="about" className={styles.section}>
      <div className={styles.container}>
        <div className={styles.info}>
          <h2 className={styles.title}>
            Beyond the <br />
            <span className={styles.titleAccent}>Atmosphere.</span>
          </h2>
          <div className={styles.line}></div>
          <p className={styles.description}>
            {profile.bio ||
              "Astrophotography is a technical dance with physics. My journey involves thousands of light frames, hours of integration, and a dedication to revealing what remains invisible to the naked eye."}
          </p>
          <div className={styles.stats}>
            <div className={styles.statItem}>
              <p className={styles.statValue}>Bortle 1</p>
              <p className={styles.statLabel}>Site Quality</p>
            </div>
            <div className={styles.statItem}>
              <p className={styles.statValue}>130mm</p>
              <p className={styles.statLabel}>Primary Optics</p>
            </div>
          </div>
        </div>
        <div className={styles.visual}>
          <div className={styles.glassCard}>
            <div className={styles.cardGradient}></div>
            {profile.about_me_image ? (
              <img
                src={profile.about_me_image}
                alt="About me"
                className={styles.aboutImage}
              />
            ) : (
              <Camera size={100} className={styles.cardIcon} />
            )}
          </div>
        </div>
      </div>
    </section>
  );
};

export default About;
