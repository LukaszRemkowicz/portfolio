// frontend/src/components/common/ImageModal.tsx
import { type FC, useEffect, useCallback, useState } from 'react';
import { useTranslation } from 'react-i18next';
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
  const { t, i18n } = useTranslation();

  const [isFullRes, setIsFullRes] = useState(false);
  const [scale, setScale] = useState(1);
  const [panPosition, setPanPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [dragStartTime, setDragStartTime] = useState(0);
  const [hasMoved, setHasMoved] = useState(false);
  const [lastTouchDistance, setLastTouchDistance] = useState<number | null>(
    null
  );

  const closeFullRes = () => {
    setIsFullRes(false);
    setScale(1);
    setPanPosition({ x: 0, y: 0 });
    setLastTouchDistance(null);
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    if (!image || scale <= 1 || image.process === false) return;
    e.preventDefault();
    e.stopPropagation(); // Stop from hitting overlay
    setIsDragging(true);
    setHasMoved(false);
    setDragStartTime(Date.now());
    setDragStart({ x: e.clientX, y: e.clientY });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging || scale <= 1) return;

    const dx = Math.abs(e.clientX - dragStart.x);
    const dy = Math.abs(e.clientY - dragStart.y);

    if (dx > 5 || dy > 5) {
      setHasMoved(true);
    }

    const moveX = e.clientX - dragStart.x;
    const moveY = e.clientY - dragStart.y;

    setPanPosition((prev: { x: number; y: number }) => ({
      x: prev.x + moveX / (scale * 250), // Increased speed (was 500)
      y: prev.y + moveY / (scale * 250),
    }));

    setDragStart({ x: e.clientX, y: e.clientY });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleWheel = (e: React.WheelEvent<HTMLDivElement>) => {
    if (!image || !isFullRes || image.process === false) return;

    // Always prevent default to stop the background from scrolling while in lightbox
    e.preventDefault();

    // Standard scroll or Trackpad Pinch (ctrlKey)
    const factor = e.ctrlKey ? 0.05 : 0.005;
    const delta = -e.deltaY * factor;
    setScale(prev => Math.min(Math.max(1, prev + delta), 4));
  };

  const handleTouchStart = (e: React.TouchEvent<HTMLDivElement>) => {
    if (!image || image.process === false) return;
    if (e.touches.length === 2) {
      const distance = Math.hypot(
        e.touches[0].pageX - e.touches[1].pageX,
        e.touches[0].pageY - e.touches[1].pageY
      );
      setLastTouchDistance(distance);
    }
  };

  const handleTouchMove = (e: React.TouchEvent<HTMLDivElement>) => {
    if (!image || image.process === false) return;
    if (e.touches.length === 2 && lastTouchDistance !== null) {
      const distance = Math.hypot(
        e.touches[0].pageX - e.touches[1].pageX,
        e.touches[0].pageY - e.touches[1].pageY
      );
      const delta = (distance - lastTouchDistance) * 0.01;
      setScale(prev => Math.min(Math.max(1, prev + delta), 4));
      setLastTouchDistance(distance);
    } else if (e.touches.length === 1 && scale > 1) {
      const touch = e.touches[0];
      const dx = touch.clientX - dragStart.x;
      const dy = touch.clientY - dragStart.y;

      setPanPosition((prev: { x: number; y: number }) => ({
        x: prev.x + dx / (scale * 250), // Increased speed (was 500)
        y: prev.y + dy / (scale * 250),
      }));

      setDragStart({ x: touch.clientX, y: touch.clientY });
    }
  };

  const toggleZoom = (e: React.MouseEvent) => {
    if (!image || image.process === false) return;
    e.stopPropagation();
    const duration = Date.now() - dragStartTime;
    if (hasMoved || duration > 200) return; // Ignore if moved or held for long

    if (scale > 1) {
      setScale(1.0);
      setPanPosition({ x: 0, y: 0 });
    } else {
      setScale(2.0);
      setPanPosition({ x: 0, y: 0 });
    }
  };

  useEffect(() => {
    if (!image) return;
    const handleKeyDown = (e: KeyboardEvent): void => {
      if (e.key === 'Escape') {
        if (isFullRes) {
          if (scale > 1) {
            setScale(1);
            setPanPosition({ x: 0, y: 0 });
          } else {
            closeFullRes();
          }
        } else {
          onClose();
        }
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [image, onClose, isFullRes, scale]);

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
          <img
            src={image.url}
            alt={image.name}
            className={styles.modalImage}
            onClick={() => {
              if (image.process !== false) {
                setIsFullRes(true);
                setPanPosition({ x: 0, y: 0 });
              }
            }}
            style={{ cursor: image.process !== false ? 'zoom-in' : 'default' }}
            title={
              image.process !== false
                ? 'Click to view full resolution'
                : undefined
            }
            draggable='false'
            onContextMenu={e => e.preventDefault()}
          />
        </div>

        {isFullRes &&
          createPortal(
            <div
              className={styles.fullResOverlay}
              onMouseDown={() => {
                setHasMoved(false);
                setDragStartTime(Date.now());
              }}
              onClick={() => {
                const duration = Date.now() - dragStartTime;
                if (!hasMoved && duration < 200) closeFullRes();
              }}
              onMouseMove={handleMouseMove}
              onMouseUp={handleMouseUp}
              onMouseLeave={handleMouseUp}
              onWheel={handleWheel}
              onTouchStart={e => {
                if (e.touches.length === 1) {
                  setDragStart({
                    x: e.touches[0].clientX,
                    y: e.touches[0].clientY,
                  });
                }
                handleTouchStart(e);
              }}
              onTouchMove={handleTouchMove}
              onTouchEnd={() => {
                setIsDragging(false);
                setLastTouchDistance(null);
              }}
            >
              <button
                className={styles.fullResClose}
                onClick={e => {
                  e.stopPropagation();
                  closeFullRes();
                }}
              >
                <X size={32} />
              </button>
              <img
                src={image.url}
                alt={image.name}
                className={`${styles.fullResImage} ${
                  scale > 1.01 ? styles.isZoomed : ''
                }`}
                onMouseDown={handleMouseDown}
                onClick={toggleZoom}
                style={{
                  transform: `translate(${panPosition.x * 100}%, ${panPosition.y * 100}%) scale(${scale})`,
                  transition: isDragging
                    ? 'none'
                    : 'transform 0.3s cubic-bezier(0.165, 0.84, 0.44, 1)',
                  cursor:
                    image.process === false
                      ? 'default'
                      : scale > 1.01
                        ? isDragging
                          ? 'grabbing'
                          : 'grab'
                        : 'zoom-in',
                }}
                draggable='false'
                onContextMenu={e => e.preventDefault()}
              />
            </div>,
            document.body
          )}

        <div className={styles.modalMetadata}>
          <div className={styles.metadataLeft}>
            <h2 className={styles.modalTitle}>{image.name}</h2>
            <div className={styles.metaRow}>
              {image.capture_date && (
                <span className={styles.metaItem}>
                  <Calendar size={14} className={styles.metaIcon} />
                  {new Date(image.capture_date).toLocaleDateString(
                    i18n.language,
                    {
                      day: 'numeric',
                      month: 'short',
                      year: 'numeric',
                    }
                  )}
                </span>
              )}
              {image.place?.name && (
                <span className={styles.metaItem}>
                  <MapPin size={14} className={styles.metaIcon} />
                  {image.place.name}
                  {image.place.country ? `, ${image.place.country}` : ''}
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
                  image.description || t('common.noDescription')
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
