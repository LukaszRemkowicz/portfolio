import React from "react";
import { Tag } from "../types";
import styles from "../styles/components/TagSidebar.module.css";
import { Sliders } from "lucide-react";

interface TagSidebarProps {
  tags: Tag[];
  selectedTag: string | null;
  onTagSelect: (tagSlug: string | null) => void;
}

const TagSidebar: React.FC<TagSidebarProps> = ({
  tags,
  selectedTag,
  onTagSelect,
}) => {
  return (
    <aside className={styles.sidebar}>
      <div className={styles.header}>
        <Sliders size={16} className={styles.headerIcon} />
        <h2 className={styles.title}>SPECIFICATIONS</h2>
      </div>
      <div className={styles.tagList}>
        <button
          className={`${styles.tagItem} ${!selectedTag ? styles.active : ""}`}
          onClick={() => onTagSelect(null)}
        >
          All Tags
        </button>
        {tags.map((tag) => (
          <button
            key={tag.slug}
            className={`${styles.tagItem} ${
              selectedTag === tag.slug ? styles.active : ""
            }`}
            onClick={() => onTagSelect(tag.slug)}
          >
            {tag.name}
          </button>
        ))}
      </div>
    </aside>
  );
};

export default TagSidebar;
