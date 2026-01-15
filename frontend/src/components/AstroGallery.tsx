import React, { useState, useEffect } from "react";
import styles from "../styles/components/AstroGallery.module.css";
import { ASSETS } from "../api/routes";
import { AstroImage, FilterType } from "../types";
import { useAppStore } from "../store/useStore";
import ImageModal from "./common/ImageModal";
import LoadingScreen from "./common/LoadingScreen";

const AstroGallery: React.FC = () => {
  const {
    images,
    isImagesLoading,
    isInitialLoading,
    error,
    backgroundUrl: background,
    loadImages,
    loadInitialData,
  } = useAppStore();
  const loading = isInitialLoading || isImagesLoading;
  const [selectedFilter, setSelectedFilter] = useState<string | null>(null);
  const [modalImage, setModalImage] = useState<AstroImage | null>(null);

  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  useEffect(() => {
    loadImages(selectedFilter ? { filter: selectedFilter } : {});
  }, [selectedFilter, loadImages]);

  const handleFilterClick = (filter: FilterType): void => {
    setSelectedFilter(selectedFilter === filter ? null : filter);
  };

  const handleImageClick = (image: AstroImage): void => {
    setModalImage(image);
  };

  if (loading) return <LoadingScreen />;
  if (error) return <div className={styles.error}>{error}</div>;

  const FILTERS: FilterType[] = [
    "Landscape",
    "Deep Sky",
    "Startrails",
    "Solar System",
    "Milky Way",
    "Northern Lights",
  ];

  return (
    <div className={styles.container}>
      <div
        className={styles.hero}
        style={{
          backgroundImage: `url(${background || ASSETS.galleryFallback})`,
        }}
      >
        <h1 className={styles.heroTitle}>Gallery</h1>
      </div>
      <div className={styles.filtersSection}>
        {FILTERS.map((filter: FilterType) => (
          <div
            key={filter}
            className={`${styles.filterBox} ${
              selectedFilter === filter ? styles.activeFilter : ""
            }`}
            onClick={() => handleFilterClick(filter)}
          >
            {filter}
          </div>
        ))}
      </div>
      <div className={styles.grid}>
        {images.map((image: AstroImage) => (
          <div key={image.pk} className={styles.gridItem}>
            <img
              src={image.thumbnail_url || image.url}
              alt={image.name || `Astro Image ${image.pk}`}
              onClick={() => handleImageClick(image)}
              style={{ cursor: "pointer" }}
            />
          </div>
        ))}
      </div>
      <ImageModal image={modalImage} onClose={() => setModalImage(null)} />
    </div>
  );
};

export default AstroGallery;
