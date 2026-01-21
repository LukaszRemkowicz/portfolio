import React, { useEffect, useState, useCallback } from "react";
import { createPortal } from "react-dom";
import { useNavigate } from "react-router-dom";
import { Calendar, MapPin, X } from "lucide-react";
import styles from "../../styles/components/ImageModal.module.css";
import { AstroImage } from "../../types";
import { fetchAstroImage } from "../../api/services";
import { sanitizeHtml, slugify } from "../../utils/html";

interface ImageModalProps {
  image: AstroImage | null;
  onClose: () => void;
}

const ImageModal: React.FC<ImageModalProps> = ({ image, onClose }) => {
  const navigate = useNavigate();
  const [description, setDescription] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    if (!image) return;

    // Reset state
    setDescription("");

    // Optimization: if image already has a substantial description, use it
    if (image.description && image.description.length > 100) {
      setDescription(image.description);
      return;
    }

    setLoading(true);
    fetchAstroImage(image.pk)
      .then((data: AstroImage) => {
        setDescription(data.description || "No description available.");
      })
      .catch(() => {
        setDescription(image.description || "No description available.");
      })
      .finally(() => {
        setLoading(false);
      });
  }, [image]);

  useEffect(() => {
    if (!image) return;
    const handleKeyDown = (e: KeyboardEvent): void => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [image, onClose]);

  const handleOverlayClick = useCallback(() => onClose(), [onClose]);
  const handleContentClick = useCallback(
    (e: React.MouseEvent) => e.stopPropagation(),
    [],
  );

  const handleTagClick = useCallback((tag: string) => {
    onClose();
    const tagSlug = slugify(tag);
    navigate(`/astrophotography?tag=${encodeURIComponent(tagSlug)}`);
  }, [navigate, onClose]);

  if (!image) return null;

  return createPortal(
    <div className={styles.modalOverlay} onClick={handleOverlayClick}>
      <div className={styles.modalContent} onClick={handleContentClick}>
        <button
          className={styles.modalClose}
          onClick={onClose}
          aria-label="Close modal"
        >
          <X size={24} />
        </button>
        <img
          src={image.url}
          alt={image.name || "Astro Large"}
          className={styles.modalImage}
        />
        <div className={styles.modalMetadata}>
          <div className={styles.metaItem}>
            <Calendar size={16} className={styles.metaIcon} />
            <span>{image.capture_date}</span>
          </div>
          <div className={styles.metaItem}>
            <MapPin size={16} className={styles.metaIcon} />
            <span>{image.location}</span>
          </div>
          {image.tags && image.tags.length > 0 && (
            <div className={styles.tagsContainer}>
              {image.tags.map((tag, index) => (
                <button
                  key={index}
                  className={styles.tagBadge}
                  onClick={() => handleTagClick(tag)}
                  title={`View more ${tag} items`}
                >
                  #{tag.replace(/^#/, "")}
                </button>
              ))}
            </div>
          )}
          <div
            className={styles.modalDescription}
            dangerouslySetInnerHTML={{
              __html: sanitizeHtml(
                loading
                  ? "Loading cosmic details..."
                  : description || "No description available.",
              ),
            }}
          />
        </div>
      </div>
    </div>,
    document.body,
  );
};

export default ImageModal;
