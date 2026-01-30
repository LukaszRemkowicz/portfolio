// frontend/src/components/common/ImageModal.tsx
import { type FC, useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { useNavigate } from 'react-router-dom';
import { X, Calendar, MapPin } from 'lucide-react';
import styles from '../../styles/components/ImageModal.module.css';
import { AstroImage, EquipmentItem } from '../../types';
import { sanitizeHtml, slugify } from '../../utils/html';
import { APP_ROUTES } from '../../api/constants';

interface ImageModalProps {
  image: AstroImage | null;
  onClose: () => void;
}

const ImageModal: FC<ImageModalProps> = ({ image, onClose }) => {
  const navigate = useNavigate();

  useEffect(() => {
    if (!image) return;
    const handleKeyDown = (e: KeyboardEvent): void => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [image, onClose]);

  const handleTagClick = useCallback(
    (tag: string) => {
      // We don't call onClose() here because navigate() will change the URL,
      // and the parent component's useEffect will close the modal since the 'img' param will be gone.
      // This allows the browser's back button to return to the modal!
      const tagSlug = slugify(tag);
      navigate(
        `${APP_ROUTES.ASTROPHOTOGRAPHY}?tag=${encodeURIComponent(tagSlug)}`
      );
    },
    [navigate]
  );

  const renderEquipment = () => {
    const source = image;
    if (!source) return null;

    const getEquipmentValue = (
      items: (EquipmentItem | string)[] | undefined,
      key: 'model' | 'name'
    ) => {
      if (!Array.isArray(items) || items.length === 0) return null;
      return items.map(t => (typeof t === 'string' ? t : t[key])).join(', ');
    };

    const telescopeValue = getEquipmentValue(
      source.telescope as (EquipmentItem | string)[],
      'model'
    );
    const lensValue = !telescopeValue
      ? getEquipmentValue(source.lens as (EquipmentItem | string)[], 'model')
      : null;
    const cameraValue = getEquipmentValue(
      source.camera as (EquipmentItem | string)[],
      'model'
    );
    const trackerValue = getEquipmentValue(
      source.tracker as (EquipmentItem | string)[],
      'name'
    );
    const tripodValue = getEquipmentValue(
      source.tripod as (EquipmentItem | string)[],
      'name'
    );

    const items = [
      {
        label:
          Array.isArray(source.telescope) && source.telescope.length > 1
            ? 'Telescopes'
            : 'Telescope',
        value: telescopeValue,
      },
      {
        label:
          Array.isArray(source.lens) && source.lens.length > 1
            ? 'Lenses'
            : 'Lens',
        value: lensValue,
      },
      {
        label:
          Array.isArray(source.camera) && source.camera.length > 1
            ? 'Cameras'
            : 'Camera',
        value: cameraValue,
      },
      {
        label:
          Array.isArray(source.tracker) && source.tracker.length > 1
            ? 'Trackers'
            : 'Tracker',
        value: trackerValue,
      },
      {
        label:
          Array.isArray(source.tripod) && source.tripod.length > 1
            ? 'Tripods'
            : 'Tripod',
        value: tripodValue,
      },
      {
        label: 'Exposure',
        value: source.exposure_details ? (
          <div
            dangerouslySetInnerHTML={{
              __html: sanitizeHtml(source.exposure_details),
            }}
          />
        ) : null,
      },
      {
        label: 'Processing',
        value: source.processing_details ? (
          <div
            dangerouslySetInnerHTML={{
              __html: sanitizeHtml(source.processing_details),
            }}
          />
        ) : null,
      },
    ].filter(item => item.value);

    if (items.length === 0) return null;

    return (
      <div className={styles.specsBar}>
        {items.map(item => (
          <div
            key={item.label}
            className={`${styles.specItem} ${
              item.label === 'Exposure' ? styles.fullWidth : ''
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
    <div
      className={styles.modalOverlay}
      onClick={onClose}
      data-testid='image-modal'
    >
      <div className={styles.modalContent} onClick={e => e.stopPropagation()}>
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
                  <Calendar size={14} className={styles.metaIcon} />
                  {new Date(image.capture_date).toLocaleDateString('en-GB', {
                    day: 'numeric',
                    month: 'short',
                    year: 'numeric',
                  })}
                </span>
              )}
              {image.location && (
                <span className={styles.metaItem}>
                  <MapPin size={14} className={styles.metaIcon} />
                  {image.location}
                </span>
              )}
            </div>
          </div>
          <div className={styles.tagsContainer}>
            {image.tags?.map(tag => (
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
            <div
              className={styles.modalDescription}
              dangerouslySetInnerHTML={{
                __html: sanitizeHtml(
                  image.description || 'No description available.'
                ),
              }}
            />
          </div>
        </div>
      </div>
    </div>,
    document.body
  );
};

export default ImageModal;
