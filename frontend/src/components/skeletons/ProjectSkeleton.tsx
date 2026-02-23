import { FC } from 'react';
import Skeleton from '../common/Skeleton';
import styles from '../../styles/components/Programming.module.css';

interface ProjectSkeletonProps {
  count?: number;
}

const ProjectSkeleton: FC<ProjectSkeletonProps> = ({ count = 3 }) => {
  return (
    <>
      {Array.from({ length: count }).map((_, index) => (
        <div
          key={index}
          className={styles.projectCard}
          data-testid='project-skeleton'
        >
          <Skeleton className={styles.imageWrapper} borderRadius={0} />

          <div className={styles.cardContent}>
            <Skeleton
              width='60%'
              height='24px'
              style={{ marginBottom: '1rem' }}
            />
            <Skeleton
              width='100%'
              height='16px'
              style={{ marginBottom: '0.5rem' }}
            />
            <Skeleton
              width='90%'
              height='16px'
              style={{ marginBottom: '0.5rem' }}
            />
            <Skeleton
              width='40%'
              height='16px'
              style={{ marginBottom: '1.5rem', flex: 1 }}
            />

            <div className={styles.techStack}>
              <Skeleton width='60px' height='24px' borderRadius='9999px' />
              <Skeleton width='80px' height='24px' borderRadius='9999px' />
              <Skeleton width='70px' height='24px' borderRadius='9999px' />
            </div>

            <div className={styles.cardActions}>
              <Skeleton width='80px' height='20px' />
              <Skeleton width='80px' height='20px' />
            </div>
          </div>
        </div>
      ))}
    </>
  );
};

export default ProjectSkeleton;
