// frontend/src/components/TravelHighlights.tsx
import { type FC, useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import styles from '../styles/components/TravelHighlights.module.css';
import { MapPin } from 'lucide-react';
import { MainPageLocation } from '../types';
import { useSettings } from '../hooks/useSettings';
import { useTravelHighlights } from '../hooks/useTravelHighlights';
import { stripHtml } from '../utils/html';
import { getDateSlug } from '../utils/date';
import { APP_ROUTES, DEFAULT_TRAVEL_IMAGE } from '../api/constants';
import { useTranslation } from 'react-i18next';
import ImageWithFallback from './common/ImageWithFallback';

const getNextAvailableIndex = (
  imagesLength: number,
  startIndex: number,
  failed: Set<number>
) => {
  if (imagesLength === 0) {
    return 0;
  }

  for (let offset = 1; offset <= imagesLength; offset += 1) {
    const candidate = (startIndex + offset) % imagesLength;
    if (!failed.has(candidate)) {
      return candidate;
    }
  }

  return startIndex;
};

const PRIORITY_CARD_COUNT = 6;

const TravelCard: FC<{
  location: MainPageLocation;
  prioritizeImage?: boolean;
}> = ({ location, prioritizeImage = false }) => {
  const navigate = useNavigate();
  const [currentIndex, setCurrentIndex] = useState(0);
  const [failedIndices, setFailedIndices] = useState<Set<number>>(new Set());
  const images = location.images
    .map(img => img.thumbnail_url || '')
    .filter(Boolean);
  const activeIndex =
    images.length > 1 && failedIndices.has(currentIndex)
      ? getNextAvailableIndex(images.length, currentIndex, failedIndices)
      : currentIndex;

  useEffect(() => {
    if (images.length <= 1) return;

    const interval = setInterval(() => {
      setCurrentIndex(prev =>
        getNextAvailableIndex(images.length, prev, failedIndices)
      );
    }, 7000);
    return () => clearInterval(interval);
  }, [failedIndices, images.length]);

  const handleImageError = (index: number) => {
    setFailedIndices(prev => new Set(prev).add(index));
  };

  // Fallback logic
  const hasNoImages = images.length === 0;
  const displayImages = !hasNoImages ? images : [DEFAULT_TRAVEL_IMAGE];
  const allImagesFailed =
    !hasNoImages && failedIndices.size >= displayImages.length;

  // Construct display location: "Place, Country" or just "Country"
  const displayLocation = location.place?.name
    ? `${location.place.name}, ${location.place.country}`
    : location.place?.country;

  // Prioritize story from location model, fall back to first image description
  const description = useMemo(() => {
    if (location.story && location.story.trim()) {
      return stripHtml(location.story);
    }
    return location.images.length > 0
      ? stripHtml(location.images[0].description)
      : `Explore the cosmic wonders of ${location.place?.country}.`;
  }, [location.story, location.images, location.place?.country]);

  // Check if the location is "new" (created within last 14 days)
  const isNew = useMemo(() => {
    if (!location.created_at) return false;
    try {
      const createdAtDate = new Date(location.created_at);
      const fourteenDaysAgo = new Date();
      fourteenDaysAgo.setDate(fourteenDaysAgo.getDate() - 14);
      return createdAtDate > fourteenDaysAgo;
    } catch {
      return false;
    }
  }, [location.created_at]);

  const handleCardClick = () => {
    // Generate the required date slug using the actual raw date range.
    const resolvedDateSlug =
      location.date_slug || getDateSlug(location.adventure_date_raw);

    let url = `${APP_ROUTES.TRAVEL_HIGHLIGHTS}/${location.country_slug}`;
    if (location.place_slug && resolvedDateSlug) {
      url += `/${location.place_slug}/${resolvedDateSlug}`;
    }
    navigate(url);
  };

  return (
    <article
      className={styles.card}
      onClick={handleCardClick}
      style={{ cursor: 'pointer' }}
    >
      {isNew && <div className={styles.newBadge}>New!</div>}
      <div className={styles.imageWrapper}>
        {displayImages.map((img, index) => (
          <div key={index} className={styles.carouselSlide}>
            <ImageWithFallback
              src={img}
              alt={`Travel highlight from ${location.place?.country}`}
              className={`${styles.cardImage} ${
                index === activeIndex && !failedIndices.has(index)
                  ? styles.active
                  : ''
              }`}
              onError={() => handleImageError(index)}
              loading={
                prioritizeImage && index === activeIndex ? 'eager' : 'lazy'
              }
              decoding='async'
              {...(prioritizeImage && index === activeIndex
                ? ({ fetchpriority: 'high' } as const)
                : {})}
            />
            {(hasNoImages || allImagesFailed) && (
              <div
                className={`${styles.placeholderOverlay} ${index === activeIndex ? styles.active : ''}`}
              >
                <span className={styles.placeholderText}>[Placeholder]</span>
              </div>
            )}
          </div>
        ))}
      </div>
      <div className={styles.cardContent}>
        <span className={styles.category}>Adventure</span>
        <h3 className={styles.cardTitle}>
          {location.highlight_name ||
            location.place?.name ||
            location.place?.country}
        </h3>
        <p className={styles.cardLocation}>
          <MapPin size={12} className={styles.metaIcon} />
          {displayLocation}
        </p>
        <p className={styles.cardDescription}>{description}</p>
        <div className={styles.divider} aria-hidden='true' />
      </div>
    </article>
  );
};

const TravelHighlights: FC = () => {
  const { data: settings } = useSettings();
  const isEnabled = settings?.travelHighlights !== false;

  const { data: locations = [], isLoading: loading } =
    useTravelHighlights(isEnabled);
  const { t } = useTranslation();

  if (loading && isEnabled) {
    return null; // Or a loading spinner
  }

  if (!isEnabled) {
    return null;
  }

  if (!locations || locations.length === 0) {
    return null; // Hide section if no content
  }

  return (
    <section id='travel' className={styles.section}>
      <header className={styles.header}>
        <h2 className={styles.title}>{t('travel.title')}</h2>
        <p className={styles.subtitle}>{t('travel.subtitle')}</p>
      </header>

      <div className={styles.grid}>
        {locations.map((location: MainPageLocation, index: number) => (
          <TravelCard
            key={location.pk}
            location={location}
            prioritizeImage={index < PRIORITY_CARD_COUNT}
          />
        ))}
      </div>
    </section>
  );
};

export default TravelHighlights;
