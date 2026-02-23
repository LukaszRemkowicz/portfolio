import { FC, CSSProperties } from 'react';
import styles from '../../styles/components/Skeleton.module.css';

interface SkeletonProps {
  className?: string;
  width?: string | number;
  height?: string | number;
  borderRadius?: string | number;
  style?: CSSProperties;
}

const Skeleton: FC<SkeletonProps> = ({
  className = '',
  width,
  height,
  borderRadius,
  style = {},
}) => {
  return (
    <div
      className={`${styles.skeleton} ${className}`}
      style={{
        width,
        height,
        borderRadius,
        ...style,
      }}
      aria-hidden='true'
    />
  );
};

export default Skeleton;
