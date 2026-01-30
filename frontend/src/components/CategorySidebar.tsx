import React from 'react';
import { FilterType } from '../types';
import styles from '../styles/components/CategorySidebar.module.css';
import { LayoutGrid } from 'lucide-react';

interface CategorySidebarProps {
  categories: FilterType[];
  selectedCategory: FilterType | null;
  onCategorySelect: (category: FilterType) => void;
  isOpen: boolean;
  onToggle: () => void;
}

const CategorySidebar: React.FC<CategorySidebarProps> = ({
  categories,
  selectedCategory,
  onCategorySelect,
  isOpen,
  onToggle,
}) => {
  return (
    <aside className={`${styles.sidebar} ${isOpen ? styles.open : ''}`}>
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <LayoutGrid size={16} className={styles.headerIcon} />
          <h2 className={styles.title}>Categories</h2>
        </div>
        <button
          className={styles.closeButton}
          onClick={onToggle}
          aria-label='Close categories'
        >
          ✕
        </button>
      </div>
      <div className={styles.list}>
        {categories.map(category => (
          <button
            key={category}
            className={`${styles.item} ${
              selectedCategory === category ? styles.active : ''
            }`}
            onClick={() => onCategorySelect(category)}
          >
            {category}
          </button>
        ))}
      </div>
    </aside>
  );
};

export default CategorySidebar;
