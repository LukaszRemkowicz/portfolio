import React, { useState, useEffect } from "react";
import styles from "./styles/components/Gallery.module.css";
import { Camera } from "lucide-react";
import { fetchEnabledFeatures, fetchAstroImages } from "./api/services";
import { AstroImage } from "./types";

const Gallery: React.FC = () => {
  const [filter, setFilter] = useState("all");
  const [images, setImages] = useState<AstroImage[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        // Fetch a larger batch of images once on mount
        const data = await fetchAstroImages({ limit: 50 });
        setImages(data);
      } catch (error) {
        console.error("Failed to fetch gallery images:", error);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  const getFilteredImages = () => {
    if (filter === "all") return images.slice(0, 9);

    const categoryMap: Record<string, string> = {
      deepsky: "deepsky",
      astrolandscape: "astrolandscape",
      timelapse: "timelapses",
    };

    const targetCategory = categoryMap[filter] || filter;

    return images
      .filter((img) => img.tags && img.tags.includes(targetCategory))
      .slice(0, 9);
  };

  const filteredImages = getFilteredImages();

  // Only hide the entire section if we have finished loading and there are NO images at all in the backend
  if (!loading && images.length === 0) return null;

  return (
    <section id="gallery" className={styles.section}>
      <div className={styles.header}>
        <h2 className={styles.title}>Portfolio</h2>
        <div className={styles.filters}>
          <button
            onClick={() => setFilter("all")}
            className={`${styles.filterBtn} ${filter === "all" ? styles.active : ""}`}
          >
            All Works
          </button>
          <button
            onClick={() => setFilter("deepsky")}
            className={`${styles.filterBtn} ${filter === "deepsky" ? styles.active : ""}`}
          >
            Deep Sky
          </button>
          <button
            onClick={() => setFilter("astrolandscape")}
            className={`${styles.filterBtn} ${filter === "astrolandscape" ? styles.active : ""}`}
          >
            Astrolandscape
          </button>
          <button
            onClick={() => setFilter("timelapse")}
            className={`${styles.filterBtn} ${filter === "timelapse" ? styles.active : ""}`}
          >
            Timelapses
          </button>
        </div>
      </div>

      <div className={styles.grid}>
        {loading ? (
          <div className={styles.loading}>Loading Portfolio...</div>
        ) : filteredImages.length > 0 ? (
          filteredImages.map((item) => (
            <div key={item.pk} className={styles.card}>
              <div
                className={styles.cardBg}
                style={{
                  backgroundImage: `url(${item.thumbnail_url || item.url})`,
                  backgroundSize: "cover",
                  backgroundPosition: "center",
                  opacity: 0.6,
                }}
              ></div>
              <div className={styles.cardIcon}>
                <Camera size={48} />
              </div>
              <div className={styles.cardContent}>
                <span className={styles.category}>{item.celestial_object}</span>
                <h3 className={styles.cardTitle}>{item.name}</h3>
                <div className={styles.divider}></div>
              </div>
            </div>
          ))
        ) : (
          <div className={styles.noResults}>
            No works found in this category.
          </div>
        )}
      </div>
    </section>
  );
};

export default Gallery;
