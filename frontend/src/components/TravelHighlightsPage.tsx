import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useParams } from 'react-router-dom';
import styles from '../styles/components/TravelHighlightsPage.module.css';
import { getMediaUrl, ASSETS } from '../api/routes';
import { AstroImage } from '../types';
import ImageModal from './common/ImageModal';
import LoadingScreen from './common/LoadingScreen';
import StarBackground from './StarBackground';
import { useBackground } from '../hooks/useBackground';
import { useTravelHighlightDetail } from '../hooks/useTravelHighlightDetail';
import { sanitizeHtml } from '../utils/html';

const TravelHighlightsPage: React.FC = () => {
  const { t, i18n } = useTranslation();
  const { countrySlug, placeSlug } = useParams<{
    countrySlug: string;
    placeSlug?: string;
  }>();

  const [modalImage, setModalImage] = useState<AstroImage | null>(null);

  const { data: backgroundUrl } = useBackground();
  const {
    data: locationData,
    isLoading: loading,
    error: queryError,
  } = useTravelHighlightDetail(countrySlug, placeSlug);

  const error = queryError ? (queryError as Error).message : null;

  // Metadata from locationData
  const images = locationData?.images || [];
  const country = locationData?.place?.country || '';
  const place = locationData?.place?.name || null;
  const story = locationData?.story || null;
  const adventureDate = locationData?.adventure_date || null;
  const createdAt = locationData?.created_at || null;
  const highlightName = locationData?.highlight_name || null;
  const locationBackgroundImage = locationData?.background_image || null;

  const handleImageClick = (image: AstroImage): void => {
    setModalImage(image);
  };

  if (loading) return <LoadingScreen />;
  if (error) return <div className={styles.error}>{t('travel.error')}</div>;

  // Display title: "Place, Country" or just "Country"
  const displayTitle =
    place && country ? `${place}, ${country}` : country || 'Travel Highlights';

  const localizeAdventureDate = (dateStr: string | null, lang: string) => {
    if (!dateStr) return null;
    const months: Record<string, number> = {
      Jan: 0,
      Feb: 1,
      Mar: 2,
      Apr: 3,
      May: 4,
      Jun: 5,
      Jul: 6,
      Aug: 7,
      Sep: 8,
      Oct: 9,
      Nov: 10,
      Dec: 11,
    };

    return dateStr.replace(
      /\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b/g,
      match => {
        const dummyDate = new Date(2000, months[match], 1);
        return dummyDate.toLocaleDateString(lang, { month: 'short' });
      }
    );
  };

  return (
    <div className={styles.container}>
      <StarBackground />
      <div
        className={styles.hero}
        style={
          locationBackgroundImage || backgroundUrl
            ? {
                backgroundImage: `linear-gradient(rgba(2, 4, 10, 0.8), rgba(2, 4, 10, 0.8)), url(${getMediaUrl(
                  locationBackgroundImage || backgroundUrl
                )})`,
                backgroundSize: 'cover',
                backgroundPosition: 'center',
              }
            : {
                backgroundImage: `url(${ASSETS.galleryFallback})`,
              }
        }
      >
        <h1 className={styles.heroTitle}>{displayTitle}</h1>
        <p className={styles.heroSubtitle}>
          {t('travel.exploringCosmic')} {displayTitle}
        </p>
      </div>

      {/* Dynamic Story Section */}
      {story && story.trim().length > 0 && (
        <section className={styles.expeditionContainer}>
          <div className={styles.glassCard}>
            <header className={styles.metaInfo}>
              <span className={styles.badge}>
                {t('travel.adventureDate')} |{' '}
                {adventureDate
                  ? localizeAdventureDate(
                      adventureDate,
                      i18n.language
                    )?.toUpperCase()
                  : createdAt
                    ? new Date(createdAt)
                        .toLocaleDateString(i18n.language, {
                          month: 'long',
                          year: 'numeric',
                        })
                        .toUpperCase()
                    : 'RECENT EXPEDITION'}
              </span>
            </header>

            <h2 className={styles.storyTitle}>
              {highlightName || 'About this place'}
            </h2>

            <div
              className={styles.storyContent}
              dangerouslySetInnerHTML={{ __html: sanitizeHtml(story) }}
            />
          </div>
        </section>
      )}

      {/* Gallery Section */}
      <div className={styles.gallerySection}>
        <h3 className={styles.galleryTitle}>CAPTURED HIGHLIGHTS</h3>

        {images.length > 0 ? (
          <div className={styles.stackedCards}>
            {images.map(image => (
              <div key={image.pk} className={styles.viewerContainer}>
                <div className={styles.viewerFrame}>
                  <div className={styles.imageWrapper}>
                    <img
                      src={image.url}
                      alt={image.name}
                      className={styles.viewerImage}
                      loading='lazy'
                      onClick={() => handleImageClick(image)}
                      draggable='false'
                      onContextMenu={e => e.preventDefault()}
                    />
                  </div>

                  <div className={styles.viewerDetails}>
                    <h4 className={styles.imageTitle}>{image.name}</h4>
                    <div
                      className={styles.imageDescription}
                      dangerouslySetInnerHTML={{
                        __html: sanitizeHtml(
                          image.description || t('common.noDescription')
                        ),
                      }}
                    />

                    <div className={styles.imageMeta}></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className={styles.noResults}>
            <p>No images found for this destination.</p>
          </div>
        )}
      </div>
      <ImageModal image={modalImage} onClose={() => setModalImage(null)} />
    </div>
  );
};

export default TravelHighlightsPage;
