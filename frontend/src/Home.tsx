import React from "react";
import styles from "./styles/components/App.module.css";
import { HomeProps } from "./types";
import ExperienceStats from "./ExperienceStats";

const Home: React.FC<HomeProps> = ({ portraitUrl, shortDescription }) => {
  const displayDescription =
    shortDescription || "Landscape and Astrophotography";
  const dotIndex = displayDescription.indexOf(".");

  const renderHeadline = () => {
    if (dotIndex === -1) {
      return (
        <span className={styles.hero__headline_main}>{displayDescription}</span>
      );
    }
    const boldPart = displayDescription.substring(0, dotIndex + 1);
    const normalPart = displayDescription.substring(dotIndex + 1);
    return (
      <>
        <span className={styles.hero__headline_main}>{boldPart}</span>
        <span className={styles.hero__headline_sub}>{normalPart}</span>
      </>
    );
  };

  return (
    <>
      <section className={styles.hero}>
        <div className={styles.hero__headline}>{renderHeadline()}</div>
        {/* TODO: Enable ExperienceStats once backend integration is ready */}
        {/* <ExperienceStats /> */}
      </section>
      <div className={styles["side-title"]}>
        EST. 2024 — REDEFINING THE NIGHT SKY
      </div>
      <img
        className={styles["astro-image"]}
        src={portraitUrl}
        alt="Portrait"
        loading="lazy"
      />
    </>
  );
};

export default Home;
