import React, { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import styles from "../styles/components/AstroGallery.module.css";
import { ASSETS } from "../api/routes";
import { AstroImage, FilterType } from "../types";
import { useAppStore } from "../store/useStore";
import ImageModal from "./common/ImageModal";
import LoadingScreen from "./common/LoadingScreen";
import GalleryCard from "./common/GalleryCard";
import TagSidebar from "./TagSidebar";

const AstroGallery: React.FC = () => {
  const images = useAppStore((state) => state.images);
  const isInitialLoading = useAppStore((state) => state.isInitialLoading);
  const isImagesLoading = useAppStore((state) => state.isImagesLoading);
  const tags = useAppStore((state) => state.tags);
  const background = useAppStore((state) => state.backgroundUrl);
  const error = useAppStore((state) => state.error);
  const loadInitialData = useAppStore((state) => state.loadInitialData);
  const loadImages = useAppStore((state) => state.loadImages);
  const [searchParams, setSearchParams] = useSearchParams();
  const [modalImage, setModalImage] = useState<AstroImage | null>(null);

  const selectedFilter = searchParams.get("filter") as FilterType | null;
  const selectedTag = searchParams.get("tag");

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
    const nextParams = new URLSearchParams(searchParams);
    if (selectedFilter === filter) {
      nextParams.delete("filter");
    } else {
      nextParams.set("filter", filter);
      nextParams.delete("tag"); // Clicking a category clears the tag filter
    }
    setSearchParams(nextParams);
  };

  const handleTagSelect = (tagSlug: string | null): void => {
    const nextParams = new URLSearchParams(searchParams);
    if (tagSlug) {
      nextParams.set("tag", tagSlug);
    } else {
      nextParams.delete("tag");
    }
    setSearchParams(nextParams);
  };

  const handleImageClick = (image: AstroImage): void => {
    const nextParams = new URLSearchParams(searchParams);
    nextParams.set("img", image.pk.toString());
    setSearchParams(nextParams);
  };

  const closeModal = (): void => {
    const nextParams = new URLSearchParams(searchParams);
    nextParams.delete("img");
    setSearchParams(nextParams);
  };

  if (isInitialLoading) return <LoadingScreen />;
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
      <div className={styles.mainContent}>
        <h3 className={styles.sidebarLabel}>
          Filter by category or explore images using the tags below.
        </h3>

        <div className={styles.sidebarContainer}>
          <TagSidebar
            tags={tags}
            selectedTag={selectedTag}
            onTagSelect={handleTagSelect}
          />
        </div>

        <div className={styles.filtersSection}>
          {FILTERS.map((filter: FilterType) => {
            const isActive = selectedFilter === filter;
            return (
              <button
                key={filter}
                type="button"
                className={`${styles.filterBox} ${
                  isActive ? styles.activeFilter : ""
                }`}
                onClick={() => handleFilterClick(filter)}
                aria-pressed={isActive}
              >
                {filter}
              </button>
            );
          })}
        </div>

        <div className={styles.grid}>
          {isImagesLoading ? (
            <div className={styles.noResults}>
              <p>Scanning deep space sectors...</p>
            </div>
          ) : images.length > 0 ? (
            images.map((image: AstroImage) => (
              <GalleryCard
                key={image.pk}
                item={image}
                onClick={handleImageClick}
              />
            ))
          ) : (
            <div className={styles.noResults}>
              <p>No images found for this filter.</p>
              <p className={styles.noResultsHint}>
                Try selecting a different category or tag to see more images.
              </p>
            </div>
          )}
        </div>
      </div>
      <ImageModal image={modalImage} onClose={closeModal} />
    </div>
  );
};

export default AstroGallery;
