// src/components/skeletons/ProjectSkeleton.tsx
import React from 'react';
import Skeleton from '../common/Skeleton';
import styles from '../../styles/components/Programming.module.css';

const ProjectSkeleton: React.FC = () => {
  return (
    <div className={styles.projectCard}>
      <div className={styles.imageWrapper}>
        <Skeleton height='100%' width='100%' />
      </div>
      <div className={styles.cardContent}>
        <Skeleton variant='title' width='70%' />
        <Skeleton variant='text' />
        <Skeleton variant='text' />
        <div style={{ display: 'flex', gap: '8px', marginTop: '1rem' }}>
          <Skeleton width='60px' height='24px' />
          <Skeleton width='80px' height='24px' />
          <Skeleton width='70px' height='24px' />
        </div>
        <div style={{ display: 'flex', gap: '16px', marginTop: '1.5rem' }}>
          <Skeleton width='100px' height='36px' />
          <Skeleton width='100px' height='36px' />
        </div>
      </div>
    </div>
  );
};

export default ProjectSkeleton;
