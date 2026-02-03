import React from 'react';
import { useTranslation } from 'react-i18next';
import styles from '../../styles/components/LoadingScreen.module.css';

interface LoadingScreenProps {
  message?: string;
  fullScreen?: boolean;
}

const LoadingScreen: React.FC<LoadingScreenProps> = ({
  message,
  fullScreen = true,
}) => {
  const { t } = useTranslation();
  const displayMessage = message || t('common.syncCosmos');

  return (
    <div
      className={fullScreen ? styles.loadingScreen : ''}
      data-testid='loading-screen'
    >
      <div className={styles.spinner} />
      <span className={styles.text}>{displayMessage}</span>
    </div>
  );
};

export default LoadingScreen;
