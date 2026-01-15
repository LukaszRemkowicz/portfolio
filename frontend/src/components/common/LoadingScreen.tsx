import React from "react";
import styles from "../../styles/components/LoadingScreen.module.css";

interface LoadingScreenProps {
  message?: string;
  fullScreen?: boolean;
}

const LoadingScreen: React.FC<LoadingScreenProps> = ({
  message = "Synchronizing with the Cosmos",
  fullScreen = true,
}) => {
  return (
    <div className={fullScreen ? styles.loadingScreen : ""}>
      <div className={styles.spinner} />
      <span className={styles.text}>{message}</span>
    </div>
  );
};

export default LoadingScreen;
