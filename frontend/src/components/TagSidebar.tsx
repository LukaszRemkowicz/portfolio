import React from 'react';
import { useTranslation } from 'react-i18next';
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
  const { t } = useTranslation();
  return (
    <aside className={`${styles.sidebar} ${isOpen ? styles.open : ''}`}>
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <Sliders size={16} className={styles.headerIcon} />
          <h2 className={styles.title}>{t('common.tags')}</h2>
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
          {t('common.allTags')}
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
