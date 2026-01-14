import React, { useState } from "react";
import styles from "./styles/components/Gallery.module.css";

const GALLERY_DATA = [
  {
    id: 1,
    title: "Andromeda Galaxy",
    category: "deepsky",
    color: "linear-gradient(135deg, #1e3a8a, #172554)",
  },
  {
    id: 2,
    title: "Milky Way over Alps",
    category: "landscape",
    color: "linear-gradient(135deg, #0f172a, #1e3a8a)",
  },
  {
    id: 3,
    title: "Star Trails",
    category: "timelapse",
    color: "linear-gradient(135deg, #581c87, #000000)",
  },
  {
    id: 4,
    title: "Orion Nebula",
    category: "deepsky",
    color: "linear-gradient(135deg, #831843, #312e81)",
  },
  {
    id: 5,
    title: "Moonrise Canyon",
    category: "landscape",
    color: "linear-gradient(135deg, #1f2937, #020617)",
  },
  {
    id: 6,
    title: "Solar Eclipse",
    category: "deepsky",
    color: "linear-gradient(135deg, #7c2d12, #000000)",
  },
];

const Gallery: React.FC = () => {
  const [filter, setFilter] = useState("all");

  const filteredItems =
    filter === "all"
      ? GALLERY_DATA
      : GALLERY_DATA.filter((item) => item.category === filter);

  return (
    <section id="gallery" className={styles.section}>
      <h2 className={styles.title}>Portfolio Gallery</h2>

      <div className={styles.filters}>
        {["all", "deepsky", "landscape", "timelapse"].map((cat) => (
          <button
            key={cat}
            onClick={() => setFilter(cat)}
            className={`${styles.filterBtn} ${filter === cat ? styles.active : ""}`}
          >
            {cat === "all"
              ? "All Works"
              : cat === "deepsky"
                ? "Deep Sky"
                : cat.charAt(0).toUpperCase() + cat.slice(1)}
          </button>
        ))}
      </div>

      <div className={styles.grid}>
        {filteredItems.map((item) => (
          <div key={item.id} className={styles.card}>
            <div
              className={styles.cardImage}
              style={{ background: item.color }}
            >
              <div className={styles.imagePlaceholder}>✦</div>
            </div>
            <div className={styles.cardOverlay}>
              <span className={styles.category}>{item.category}</span>
              <h3 className={styles.cardTitle}>{item.title}</h3>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
};

export default Gallery;
