import React from 'react';

import styles from './Tooltip.module.css';

type TooltipProps = {
  children: React.ReactNode;
  content: React.ReactNode;
  className?: string;
};

const Tooltip: React.FC<TooltipProps> = ({ children, content, className }) => {
  const wrapperClassName = className
    ? `${styles.wrapper} ${className}`
    : styles.wrapper;

  return (
    <span className={wrapperClassName}>
      {children}
      <span className={styles.content} role='tooltip'>
        {content}
      </span>
    </span>
  );
};

export default Tooltip;
