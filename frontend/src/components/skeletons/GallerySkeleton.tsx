// src/components/skeletons/GallerySkeleton.tsx
import React from 'react';
import Skeleton from '../common/Skeleton';
import styles from '../../styles/components/GalleryCard.module.css';

const GallerySkeleton: React.FC = () => {
  return (
    <div className={styles.card}>
      <div className={styles.imageWrapper}>
        <Skeleton height='100%' width='100%' />
      </div>
      <div className={styles.cardContent}>
        <Skeleton width='30%' height='16px' style={{ marginBottom: '8px' }} />
        <Skeleton variant='title' width='80%' />
        <Skeleton width='40%' height='14px' style={{ marginBottom: '12px' }} />
        <Skeleton variant='text' />
        <Skeleton variant='text' width='60%' />
      </div>
    </div>
  );
};

export default GallerySkeleton;
