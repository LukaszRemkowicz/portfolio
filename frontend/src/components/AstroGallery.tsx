import React, { useState, useEffect } from "react";
import styles from "../styles/components/AstroGallery.module.css";
import { Calendar, MapPin } from "lucide-react";
import {
  fetchAstroImage,
} from "../api/services";
import { ASSETS } from "../api/routes";
import { AstroImage, FilterType } from "../types";
import { useAppStore } from "../store/useStore";

const AstroGallery: React.FC = () => {
  const {
    images,
    isImagesLoading: loading,
    error,
    backgroundUrl: background,
    loadImages,
    loadInitialData
  } = useAppStore();
  const [selectedFilter, setSelectedFilter] = useState<string | null>(null);
  const [modalImage, setModalImage] = useState<AstroImage | null>(null);
  const [modalDescription, setModalDescription] = useState<string>("");
  const [modalDescriptionLoading, setModalDescriptionLoading] =
    useState<boolean>(false);

  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  useEffect(() => {
    loadImages(selectedFilter ? { filter: selectedFilter } : {});
  }, [selectedFilter, loadImages]);

  useEffect(() => {
    if (!modalImage) return;
    setModalDescription("");
    setModalDescriptionLoading(true);
    fetchAstroImage(modalImage.pk)
      .then((data: AstroImage) => {
        setModalDescription(data.description || "No description available.");
      })
      .catch(() => {
        setModalDescription("No description available.");
      })
      .finally(() => {
        setModalDescriptionLoading(false);
      });
  }, [modalImage]);

  useEffect(() => {
    if (!modalImage) return;
    const handleKeyDown = (e: KeyboardEvent): void => {
      if (e.key === "Escape") {
        closeModal();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [modalImage]);

  const closeModal = (): void => setModalImage(null);

  const handleFilterClick = (filter: FilterType): void => {
    setSelectedFilter(selectedFilter === filter ? null : filter);
  };

  const handleImageClick = (image: AstroImage): void => {
    setModalImage(image);
  };

  const handleModalOverlayClick = (): void => {
    closeModal();
  };

  const handleModalContentClick = (
    e: React.MouseEvent<HTMLDivElement>,
  ): void => {
    e.stopPropagation();
  };

  if (loading) return <div className={styles.loading}>Loading...</div>;
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
        style={{ backgroundImage: `url(${background || ASSETS.galleryFallback})` }}
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
      {modalImage && (
        <div className={styles.modalOverlay} onClick={handleModalOverlayClick}>
          <div
            className={styles.modalContent}
            onClick={handleModalContentClick}
          >
            <button className={styles.modalClose} onClick={closeModal}>
              &times;
            </button>
            <img
              src={modalImage.url}
              alt="Astro Large"
              className={styles.modalImage}
            />
            <div className={styles.modalMetadata}>
              <div className={styles.metaItem}>
                <Calendar size={16} className={styles.metaIcon} />
                <span>{modalImage.capture_date}</span>
              </div>
              <div className={styles.metaItem}>
                <MapPin size={16} className={styles.metaIcon} />
                <span>{modalImage.location}</span>
              </div>
              {modalImage.tags && modalImage.tags.length > 0 && (
                <div className={styles.tagsContainer}>
                  {modalImage.tags.map((tag, index) => (
                    <span key={index} className={styles.tagBadge}>
                      #{tag}
                    </span>
                  ))}
                </div>
              )}
            </div>
            <div className={styles.modalDescription}>
              {modalDescriptionLoading
                ? "Loading description..."
                : modalDescription}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AstroGallery;
