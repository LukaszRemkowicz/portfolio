import React from "react";
import styles from "./styles/components/About.module.css";
import { AboutProps } from "./types";

const About: React.FC<AboutProps> = ({ profile }) => {
  return (
    <section id="about" className={styles.section}>
      <div className={styles.container}>
        <div className={styles.visual}>
          <div className={styles.imageBox}>
            <div className={styles.placeholderIcon}>✦</div>
            <div className={styles.overlay}>
              <p className={styles.role}>Founder & Photographer</p>
              <h3 className={styles.name}>
                {profile?.name || "Kamil Gwiezdny"}
              </h3>
            </div>
          </div>
        </div>

        <div className={styles.content}>
          <h2 className={styles.title}>
            Beneath the <span className={styles.accent}>Atmosphere</span>
          </h2>
          <p className={styles.text}>
            My journey started with a small telescope and a massive curiosity.
            For over a decade, I've chased clear skies across the globe, from
            the high deserts of Chile to the frozen landscapes of the Arctic
            Circle.
          </p>
          <p className={styles.text}>
            Astrophotography is more than just clicking a shutter; it's a
            technical dance with physics, light, and patience. I specialize in
            narrow-band imaging and composite night landscapes that bring the
            invisible majesty of our galaxy to life.
          </p>

          <div className={styles.stats}>
            <div className={styles.statCard}>
              <p className={styles.statValue}>100+</p>
              <p className={styles.statLabel}>Clear Nights Per Year</p>
            </div>
            <div className={styles.statCard}>
              <p className={styles.statValue}>12k+</p>
              <p className={styles.statLabel}>Light Frames Captured</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default About;
