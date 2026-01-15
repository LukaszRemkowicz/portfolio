import React from "react";
import styles from "../styles/components/Programming.module.css";
import { ASSETS } from "../api/routes";

const Programming: React.FC = () => (
  <div className={styles.wrapper}>
    <div
      className={styles.container}
      style={
        {
          "--bg-image": `url(${ASSETS.underConstruction})`,
        } as React.CSSProperties
      }
    >
      <div className={styles.overlay}></div>
      <div className={styles.text}>
        Oops, page is under construction
        <br />
        Sorry, this page is still being built.
        <br />
        Please check back later!
      </div>
    </div>
  </div>
);

export default Programming;
