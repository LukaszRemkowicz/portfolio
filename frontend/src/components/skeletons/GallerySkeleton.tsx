import { FC } from 'react';
import Skeleton from '../common/Skeleton';
import styles from '../../styles/components/GalleryCard.module.css';

interface GallerySkeletonProps {
  count?: number;
}

const GallerySkeleton: FC<GallerySkeletonProps> = ({ count = 6 }) => {
  return (
    <>
      {Array.from({ length: count }).map((_, index) => (
        <Skeleton
          key={index}
          className={styles.card}
          style={{ cursor: 'default' }}
        />
      ))}
    </>
  );
};

export default GallerySkeleton;
