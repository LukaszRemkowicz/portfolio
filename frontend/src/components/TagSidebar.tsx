import React from 'react';
import { Tag } from '../types';
import styles from '../styles/components/TagSidebar.module.css';
import { Sliders } from 'lucide-react';

interface TagSidebarProps {
  tags: Tag[];
  selectedTag: string | null;
  onTagSelect: (tagSlug: string | null) => void;
  isOpen?: boolean;
  onToggle?: () => void;
}

const TagSidebar: React.FC<TagSidebarProps> = ({
  tags,
  selectedTag,
  onTagSelect,
  isOpen = false,
  onToggle,
}) => {
  return (
    <aside className={`${styles.sidebar} ${isOpen ? styles.open : ''}`}>
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <Sliders size={16} className={styles.headerIcon} />
          <h2 className={styles.title}>Tags</h2>
        </div>
        {onToggle && (
          <button
            className={styles.closeButton}
            onClick={onToggle}
            aria-label='Close tags'
          >
            ✕
          </button>
        )}
      </div>
      <div className={styles.tagList}>
        <button
          className={`${styles.tagItem} ${!selectedTag ? styles.active : ''}`}
          onClick={() => onTagSelect(null)}
        >
          All Tags
        </button>
        {tags.map(tag => (
          <button
            key={tag.slug}
            className={`${styles.tagItem} ${
              selectedTag === tag.slug ? styles.active : ''
            }`}
            onClick={() => onTagSelect(tag.slug)}
          >
            {tag.name} <span className={styles.count}>({tag.count})</span>
          </button>
        ))}
      </div>
    </aside>
  );
};

export default TagSidebar;
