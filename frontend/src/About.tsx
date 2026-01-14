import React from "react";
import styles from "./styles/components/About.module.css";
import { AboutProps } from "./types";

const About: React.FC<AboutProps> = ({ profile }) => {
  if (!profile) {
    return null; // Or a loading spinner
  }

  return (
    <section className={styles.aboutContainer}>
      <div className={styles.aboutContent}>
        <div className={styles.imageWrapper}>
          {profile.about_me_image && (
            <img
              src={profile.about_me_image}
              alt="About me"
              className={styles.aboutImage}
            />
          )}
        </div>
        <div className={styles.textWrapper}>
          <h2 className={styles.title}>About me</h2>
          {profile.bio?.split("\n").map((paragraph: string, index: number) => (
            <p
              key={index}
              className={index === 0 ? styles.subtitle : styles.bioParagraph}
            >
              {paragraph}
            </p>
          ))}
        </div>
      </div>
    </section>
  );
};

export default About;
