import React, { useEffect, useState, useCallback } from "react";
import { createPortal } from "react-dom";
import { useNavigate } from "react-router-dom";
import { X } from "lucide-react";
import styles from "../../styles/components/ImageModal.module.css";
import { AstroImage, EquipmentItem } from "../../types";
import { fetchAstroImage } from "../../api/services";
import { sanitizeHtml, slugify } from "../../utils/html";

interface ImageModalProps {
  image: AstroImage | null;
  onClose: () => void;
}

const ImageModal: React.FC<ImageModalProps> = ({ image, onClose }) => {
  const navigate = useNavigate();
  const [detailedImage, setDetailedImage] = useState<AstroImage | null>(null);
  const [description, setDescription] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    if (!image) return;

    // Reset state
    setDescription("");
    setDetailedImage(null);

    // Optimization: if image already has a substantial description, use it
    if (image.description && image.description.length > 100) {
      setDescription(image.description);
    }

    setLoading(true);
    fetchAstroImage(image.pk)
      .then((data: AstroImage) => {
        setDetailedImage(data);
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

  const handleTagClick = useCallback(
    (tag: string) => {
      // We don't call onClose() here because navigate() will change the URL,
      // and the parent component's useEffect will close the modal since the 'img' param will be gone.
      // This allows the browser's back button to return to the modal!
      const tagSlug = slugify(tag);
      navigate(`/astrophotography?tag=${encodeURIComponent(tagSlug)}`);
    },
    [navigate],
  );

  const renderEquipment = () => {
    // Prefer detailedImage data, fallback to image prop (which is guaranteed non-null here)
    const source = detailedImage || image;
    if (!source) return null;

    const getEquipmentValue = (
      items: (EquipmentItem | string)[] | undefined,
      key: "model" | "name",
    ) => {
      if (!Array.isArray(items) || items.length === 0) return null;
      return items.map((t) => (typeof t === "string" ? t : t[key])).join(", ");
    };

    const telescopeValue = getEquipmentValue(source.telescope, "model");
    const lensValue = !telescopeValue
      ? getEquipmentValue(source.lens, "model")
      : null;
    const cameraValue = getEquipmentValue(source.camera, "model");
    const trackerValue = getEquipmentValue(source.tracker, "name");
    const tripodValue = getEquipmentValue(source.tripod, "name");

    const items = [
      {
        label:
          Array.isArray(source.telescope) && source.telescope.length > 1
            ? "Telescopes"
            : "Telescope",
        value: telescopeValue,
      },
      {
        label:
          Array.isArray(source.lens) && source.lens.length > 1
            ? "Lenses"
            : "Lens",
        value: lensValue,
      },
      {
        label:
          Array.isArray(source.camera) && source.camera.length > 1
            ? "Cameras"
            : "Camera",
        value: cameraValue,
      },
      {
        label:
          Array.isArray(source.tracker) && source.tracker.length > 1
            ? "Trackers"
            : "Tracker",
        value: trackerValue,
      },
      {
        label:
          Array.isArray(source.tripod) && source.tripod.length > 1
            ? "Tripods"
            : "Tripod",
        value: tripodValue,
      },
      {
        label: "Exposure",
        value: source.exposure_details ? (
          <>
            {source.exposure_details
              .replace(" Foreground:", "\nForeground:")
              .split("\n")
              .map((line, idx) => {
                const parts = line.split(":");
                if (parts.length > 1) {
                  return (
                    <div key={idx}>
                      {parts[0]}:
                      <span className={styles.lightWeight}>
                        {parts.slice(1).join(":")}
                      </span>
                    </div>
                  );
                }
                return <div key={idx}>{line}</div>;
              })}
          </>
        ) : null,
      },
    ].filter((item) => item.value);

    if (items.length === 0) return null;

    return (
      <div className={styles.specsBar}>
        {items.map((item) => (
          <div
            key={item.label}
            className={`${styles.specItem} ${
              item.label === "Exposure" ? styles.fullWidth : ""
            }`}
          >
            <span className={styles.specLabel}>{item.label}</span>
            <span className={styles.specValue}>{item.value}</span>
          </div>
        ))}
      </div>
    );
  };

  if (!image) return null;

  return createPortal(
    <div className={styles.modalOverlay} onClick={onClose}>
      <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
        <button className={styles.modalClose} onClick={onClose}>
          <X size={24} />
        </button>

        <div className={styles.imageWrapper}>
          <img src={image.url} alt={image.name} className={styles.modalImage} />
        </div>

        <div className={styles.modalMetadata}>
          <div className={styles.metadataLeft}>
            <h2 className={styles.modalTitle}>{image.name}</h2>
            <div className={styles.metaRow}>
              {image.capture_date && (
                <span className={styles.metaItem}>
                  {new Date(image.capture_date).toLocaleDateString()}
                </span>
              )}
              {image.location && (
                <span className={styles.metaItem}>{image.location}</span>
              )}
            </div>
          </div>
          <div className={styles.tagsContainer}>
            {image.tags?.map((tag) => (
              <button
                key={tag}
                className={styles.tagBadge}
                onClick={() => handleTagClick(tag)}
              >
                #{tag}
              </button>
            ))}
          </div>
        </div>
        <div className={styles.descriptionWrapper}>
          {renderEquipment()}
          <div className={styles.descriptionContent}>
            {(loading
              ? "Loading cosmic details..."
              : description || "No description available."
            )
              .split(/\r?\n/)
              .filter((para) => para.trim().length > 0)
              .map((para, index) => (
                <div
                  key={index}
                  className={
                    index === 0
                      ? styles.modalDescription
                      : styles.descriptionParagraph
                  }
                  dangerouslySetInnerHTML={{
                    __html: sanitizeHtml(para),
                  }}
                />
              ))}
          </div>
        </div>
      </div>
    </div>,
    document.body,
  );
};

export default ImageModal;
