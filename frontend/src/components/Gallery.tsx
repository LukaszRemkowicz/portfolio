import React, { useState, useEffect } from "react";
import { createPortal } from "react-dom";
import styles from "../styles/components/Gallery.module.css";
import { Camera, Calendar, MapPin } from "lucide-react";
import { fetchAstroImages, fetchAstroImage } from "../api/services";
import { AstroImage } from "../types";

const Gallery: React.FC = () => {
  const [filter, setFilter] = useState("all");
  const [images, setImages] = useState<AstroImage[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [modalImage, setModalImage] = useState<AstroImage | null>(null);
  const [modalDescription, setModalDescription] = useState<string>("");
  const [modalDescriptionLoading, setModalDescriptionLoading] =
    useState<boolean>(false);

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
      .sort((a, b) => {
        const dateA = new Date(a.created_at || 0).getTime();
        const dateB = new Date(b.created_at || 0).getTime();
        return dateB - dateA;
      })
      .slice(0, 9);
  };

  const filteredImages = getFilteredImages();

  const isNew = (dateString?: string) => {
    if (!dateString) return false;
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - date.getTime());
    const diffDays = diffTime / (1000 * 60 * 60 * 24);
    return diffDays < 7;
  };

  const closeModal = (): void => setModalImage(null);

  const handleImageClick = (image: AstroImage): void => {
    console.log("Card clicked!", image.name);
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

  // Only hide the entire section if we have finished loading and there are NO images at all in the backend
  if (!loading && images.length === 0) return null;

  return (
    <section id="gallery" className={styles.section}>
      <div className={styles.header}>
        <h2 className={styles.title}>Latest images</h2>
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
            <div
              key={item.pk}
              className={styles.card}
              onClick={() => handleImageClick(item)}
            >
              {isNew(item.created_at) && (
                <div className={styles.newBadge}>NEW</div>
              )}
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

      {modalImage &&
        createPortal(
          <div
            className={styles.modalOverlay}
            onClick={handleModalOverlayClick}
          >
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
          </div>,
          document.body as HTMLElement,
        )}
    </section>
  );
};

export default Gallery;
