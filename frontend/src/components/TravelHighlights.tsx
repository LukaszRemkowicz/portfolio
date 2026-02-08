// frontend/src/components/TravelHighlights.tsx
import { type FC, useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import styles from '../styles/components/TravelHighlights.module.css';
import { MapPin } from 'lucide-react';
import { fetchTravelHighlights } from '../api/services';
import { MainPageLocation } from '../types';
import { useAppStore } from '../store/useStore';
import { stripHtml } from '../utils/html';
import { APP_ROUTES, DEFAULT_TRAVEL_IMAGE } from '../api/constants';
import { useTranslation } from 'react-i18next';

const TravelCard: FC<{ location: MainPageLocation }> = ({ location }) => {
  const navigate = useNavigate();
  const [currentIndex, setCurrentIndex] = useState(0);
  const images = location.images.map(img => img.thumbnail_url || img.url);

  useEffect(() => {
    if (images.length <= 1) return;

    const interval = setInterval(() => {
      setCurrentIndex(prev => (prev + 1) % images.length);
    }, 7000);
    return () => clearInterval(interval);
  }, [images.length]);

  // Fallback logic
  const displayImages = images.length > 0 ? images : [DEFAULT_TRAVEL_IMAGE];

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

  const handleCardClick = () => {
    const url = location.place_slug
      ? `${APP_ROUTES.TRAVEL_HIGHLIGHTS}/${location.country_slug}/${location.place_slug}`
      : `${APP_ROUTES.TRAVEL_HIGHLIGHTS}/${location.country_slug}`;

    navigate(url);
  };

  return (
    <article
      className={styles.card}
      onClick={handleCardClick}
      style={{ cursor: 'pointer' }}
    >
      <div className={styles.imageWrapper}>
        {displayImages.map((img, index) => (
          <img
            key={index}
            src={img}
            alt={`Travel highlight from ${location.place?.country}`}
            className={`${styles.cardImage} ${
              index === currentIndex ? styles.active : ''
            }`}
            loading='lazy'
          />
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
  const [locations, setLocations] = useState<MainPageLocation[]>([]);
  const [loading, setLoading] = useState(true);
  const { features } = useAppStore();
  const { t } = useTranslation();

  useEffect(() => {
    const loadSliders = async () => {
      if (features?.travelHighlights === false) {
        setLoading(false);
        return;
      }
      try {
        const data = await fetchTravelHighlights();
        if (data) setLocations(data);
      } catch (error) {
        console.error('Failed to fetch travel highlights:', error);
      } finally {
        setLoading(false);
      }
    };
    loadSliders();
  }, [features?.travelHighlights]);

  if (loading) {
    return null; // Or a loading spinner
  }

  if (features?.travelHighlights === false) {
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
        {locations.map(location => (
          <TravelCard key={location.pk} location={location} />
        ))}
      </div>
    </section>
  );
};

export default TravelHighlights;
