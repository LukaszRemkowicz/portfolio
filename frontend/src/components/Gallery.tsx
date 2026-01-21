import React, { useState, useEffect, useMemo, useCallback, memo } from "react";
import { useSearchParams } from "react-router-dom";
import styles from "../styles/components/Gallery.module.css";
import { MapPin } from "lucide-react";
import { AstroImage } from "../types";
import { useAppStore } from "../store/useStore";
import ImageModal from "./common/ImageModal";
import { stripHtml } from "../utils/html";

interface GalleryCardProps {
  item: AstroImage;
  onClick: (image: AstroImage) => void;
  isNew: (dateString?: string) => boolean;
}

const GalleryCard = memo(({ item, onClick, isNew }: GalleryCardProps) => {
  const [isLoaded, setIsLoaded] = useState(false);

  return (
    <button
      className={styles.card}
      onClick={() => onClick(item)}
      aria-label={`View details for ${item.name}`}
      type="button"
    >
      {isNew(item.created_at) && <div className={styles.newBadge}>NEW</div>}
      <div className={styles.imageWrapper} aria-hidden="true">
        <div
          className={`${styles.placeholder} ${isLoaded ? styles.hide : ""}`}
        />
        <img
          src={item.thumbnail_url || item.url}
          alt=""
          loading="lazy"
          onLoad={() => setIsLoaded(true)}
          className={`${styles.cardImage} ${isLoaded ? styles.show : ""}`}
        />
      </div>
      <div className={styles.cardContent}>
        <span className={styles.category}>{item.celestial_object}</span>
        <h3 className={styles.cardTitle}>{item.name}</h3>
        <p className={styles.cardLocation}>
          <MapPin size={12} className={styles.metaIcon} />
          {item.location}
        </p>
        <p className={styles.cardDescription}>
          {item.description
            ? (() => {
              const plainDescription = stripHtml(item.description);
              return plainDescription.length > 80
                ? `${plainDescription.substring(0, 80)}...`
                : plainDescription;
            })()
            : ""}
        </p>
        <div className={styles.divider} aria-hidden="true"></div>
      </div>
    </button>
  );
});

GalleryCard.displayName = "GalleryCard";

const Gallery: React.FC = () => {
  const [filter, setFilter] = useState("all");
  const {
    images,
    isImagesLoading: loading,
    error,
    loadImages,
    features,
  } = useAppStore();
  const [modalImage, setModalImage] = useState<AstroImage | null>(null);
  const [searchParams, setSearchParams] = useSearchParams();

  // Sync modalImage with 'img' query parameter
  useEffect(() => {
    const imgId = searchParams.get("img");
    if (imgId) {
      const img = images.find((i) => i.pk.toString() === imgId);
      if (img) {
        setModalImage(img);
      } else {
        setModalImage(null);
      }
    } else {
      setModalImage(null);
    }
  }, [searchParams, images]);

  useEffect(() => {
    if (features?.lastimages !== false) {
      loadImages({ limit: 50 });
    }
  }, [loadImages, features]);

  const filteredImages = useMemo(() => {
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
  }, [images, filter]);

  const isNew = useCallback((dateString?: string) => {
    if (!dateString) return false;
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - date.getTime());
    const diffDays = diffTime / (1000 * 60 * 60 * 24);
    return diffDays < 7;
  }, []);

  const handleImageClick = useCallback((image: AstroImage): void => {
    console.log("Card clicked!", image.name);
    // Use URL params for modal state to support browser back button
    searchParams.set("img", image.pk.toString());
    setSearchParams(searchParams);
  }, [searchParams, setSearchParams]);

  const closeModal = useCallback(() => {
    searchParams.delete("img");
    setSearchParams(searchParams);
  }, [searchParams, setSearchParams]);

  // Hide the entire section if disabled via admin toggle or if no images
  if (features?.lastimages === false || (!loading && images.length === 0)) {
    return null;
  }

  return (
    <section id="gallery" className={styles.section}>
      <div className={styles.header}>
        <h2 className={styles.title}>Latest images</h2>
        <div className={styles.filters}>
          <button
            type="button"
            onClick={() => setFilter("all")}
            className={`${styles.filterBtn} ${filter === "all" ? styles.active : ""}`}
          >
            All Works
          </button>
          <button
            type="button"
            onClick={() => setFilter("deepsky")}
            className={`${styles.filterBtn} ${filter === "deepsky" ? styles.active : ""}`}
          >
            Deep Sky
          </button>
          <button
            type="button"
            onClick={() => setFilter("astrolandscape")}
            className={`${styles.filterBtn} ${filter === "astrolandscape" ? styles.active : ""}`}
          >
            Astrolandscape
          </button>
          <button
            type="button"
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
        ) : error ? (
          <div className={styles.error}>{error}</div>
        ) : filteredImages.length > 0 ? (
          filteredImages.map((item) => (
            <GalleryCard
              key={item.pk}
              item={item}
              onClick={handleImageClick}
              isNew={isNew}
            />
          ))
        ) : (
          <div className={styles.noResults}>
            No works found in this category.
          </div>
        )}
      </div>

      <ImageModal image={modalImage} onClose={closeModal} />
    </section>
  );
};

export default Gallery;
