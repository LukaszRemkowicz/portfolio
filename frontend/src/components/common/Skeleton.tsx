// src/components/common/Skeleton.tsx
import React from 'react';
import styles from '../../styles/components/Skeleton.module.css';

interface SkeletonProps {
  className?: string;
  width?: string | number;
  height?: string | number;
  variant?: 'text' | 'title' | 'rectangular' | 'circle';
  style?: React.CSSProperties;
}

const Skeleton: React.FC<SkeletonProps> = ({
  className = '',
  width,
  height,
  variant = 'rectangular',
  style,
}) => {
  const customStyles: React.CSSProperties = {
    ...style,
    width: width,
    height: height,
  };

  const variantClass = styles[variant] || '';

  return (
    <div
      className={`${styles.skeleton} ${variantClass} ${className}`}
      style={customStyles}
      data-testid='skeleton'
    >
      <div className={styles.shimmer} />
    </div>
  );
};

export default Skeleton;
