import React, { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
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
  const [searchParams, setSearchParams] = useSearchParams();
  const selectedFilter = searchParams.get("filter");
  const selectedTag = searchParams.get("tag");
  const [modalImage, setModalImage] = useState<AstroImage | null>(null);

  // Sync modalImage with 'img' query parameter
  useEffect(() => {
    const imgId = searchParams.get("img");
    if (imgId) {
      const img = images.find((i) => i.pk.toString() === imgId);
      if (img) {
        setModalImage(img);
      } else {
        // If image not in current list (e.g. direct link), we might need to fetch it
        // but for now we'll just close it if not found in current view
        setModalImage(null);
      }
    } else {
      setModalImage(null);
    }
  }, [searchParams, images]);

  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  useEffect(() => {
    loadImages({
      ...(selectedFilter ? { filter: selectedFilter } : {}),
      ...(selectedTag ? { tag: selectedTag } : {}),
    });
  }, [selectedFilter, selectedTag, loadImages]);

  const handleFilterClick = (filter: FilterType): void => {
    if (selectedFilter === filter) {
      searchParams.delete("filter");
    } else {
      searchParams.set("filter", filter);
      searchParams.delete("tag"); // Clicking a category clears the tag filter
    }
    setSearchParams(searchParams);
  };

  const handleImageClick = (image: AstroImage): void => {
    searchParams.set("img", image.pk.toString());
    setSearchParams(searchParams);
  };

  const closeModal = (): void => {
    searchParams.delete("img");
    setSearchParams(searchParams);
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
            className={`${styles.filterBox} ${selectedFilter === filter ? styles.activeFilter : ""
              }`}
            onClick={() => handleFilterClick(filter)}
          >
            {filter}
          </div>
        ))}
      </div>
      <div className={styles.grid}>
        {images.length > 0 ? (
          images.map((image: AstroImage) => (
            <div key={image.pk} className={styles.gridItem}>
              <img
                src={image.thumbnail_url || image.url}
                alt={image.name || `Astro Image ${image.pk}`}
                onClick={() => handleImageClick(image)}
                style={{ cursor: "pointer" }}
              />
            </div>
          ))
        ) : (
          <div className={styles.noResults}>
            <p>No images found for this filter.</p>
            <p className={styles.noResultsHint}>
              Try selecting a different category or clear the filter to see all
              images.
            </p>
          </div>
        )}
      </div>
      <ImageModal image={modalImage} onClose={closeModal} />
    </div>
  );
};

export default AstroGallery;
