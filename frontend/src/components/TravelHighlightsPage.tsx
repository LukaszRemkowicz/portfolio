import React, { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { useParams, useSearchParams } from 'react-router-dom';
import styles from '../styles/components/TravelHighlightsPage.module.css';
import { ASSETS } from '../api/routes';
import { getMediaUrl } from '../api/media';
import ImageModal from './common/ImageModal';
import ImageWithFallback from './common/ImageWithFallback';
import LoadingScreen from './common/LoadingScreen';
import StarBackground from './StarBackground';
import { sanitizeHtml } from '../utils/html';
import { useBackground } from '../hooks/useBackground';
import { useImageUrls } from '../hooks/useImageUrls';
import SEO from './common/SEO';
import {
  useTravelHighlightDetail,
  ExtendedAstroImage,
} from '../hooks/useTravelHighlightDetail';

const TravelHighlightsPage: React.FC = () => {
  const { t, i18n } = useTranslation();
  const { countrySlug, placeSlug, dateSlug } = useParams<{
    countrySlug: string;
    placeSlug?: string;
    dateSlug?: string;
  }>();

  const [searchParams, setSearchParams] = useSearchParams();
  const imgParam = searchParams.get('img');

  const { data: backgroundUrl } = useBackground();

  // Redirect or show error if URL params are incomplete
  const hasIncompleteParams = !countrySlug || !placeSlug || !dateSlug;

  const {
    data: detailData,
    isLoading: queryLoading,
    error: queryError,
  } = useTravelHighlightDetail(countrySlug, placeSlug, dateSlug);

  const error = hasIncompleteParams
    ? 'Incomplete location specified. URL must contain country, place, and date.'
    : queryError
      ? 'Failed to load travel highlights. Please check the URL and try again.'
      : null;

  const loading = queryLoading && !hasIncompleteParams;

  const fullLocation = detailData?.full_location || 'Travel Highlights';
  const story = detailData?.story || null;
  const adventureDate = detailData?.adventure_date || null;
  const highlightName = detailData?.highlight_name || null;
  const highlightTitle = detailData?.highlight_title || null;
  const locationBackgroundImage = detailData?.background_image || null;
  const images = useMemo(() => detailData?.images || [], [detailData?.images]);

  // Fetch full resolution URLs for all images
  const imageIdsToFetch = useMemo(
    () => images.map(img => img.pk.toString()),
    [images]
  );
  const { data: imageUrls = {} } = useImageUrls(
    imageIdsToFetch,
    imageIdsToFetch.length > 0
  );

  // Derive modal image from URL parameter
  const modalImage = useMemo(() => {
    if (!imgParam) return null;
    const found = images.find(
      i => i.slug === imgParam || i.pk.toString() === imgParam
    );
    if (!found) return null;

    // Enhance with full-res URL if available
    const fullResUrl = imageUrls[found.pk.toString()] || imageUrls[found.slug];
    return {
      ...found,
      url: fullResUrl || found.url || found.thumbnail_url,
    };
  }, [imgParam, images, imageUrls]);

  const handleImageClick = (image: ExtendedAstroImage): void => {
    const nextParams = new URLSearchParams(searchParams);
    nextParams.set('img', image.slug);
    setSearchParams(nextParams);
  };

  const closeModal = (): void => {
    const nextParams = new URLSearchParams(searchParams);
    nextParams.delete('img');
    setSearchParams(nextParams);
  };

  if (loading) return <LoadingScreen />;
  if (error) return <div className={styles.error}>{error}</div>;

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

  // Derive SEO description safely
  const seoDescription = String(
    highlightTitle ||
      (story ? story.substring(0, 160) : undefined) ||
      `Travel highlights from ${fullLocation}`
  );

  return (
    <div className={styles.container}>
      <SEO
        title={fullLocation}
        description={seoDescription}
        ogImage={
          locationBackgroundImage
            ? getMediaUrl(locationBackgroundImage)
            : undefined
        }
      />
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
        <h1 className={styles.heroTitle}>{fullLocation}</h1>
        <p className={styles.heroSubtitle}>
          {highlightTitle || `${t('travel.exploringCosmic')} ${fullLocation}`}
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
                    <ViewerImage
                      image={image}
                      handleImageClick={handleImageClick}
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
      <ImageModal image={modalImage} onClose={closeModal} />
    </div>
  );
};

const ViewerImage: React.FC<{
  image: ExtendedAstroImage;
  handleImageClick: (image: ExtendedAstroImage) => void;
}> = ({ image, handleImageClick }) => {
  const [hasError, setHasError] = React.useState(!image.thumbnail_url);

  return (
    <>
      <ImageWithFallback
        src={image.thumbnail_url}
        alt={image.name}
        data-testid={`gallery-card-${image.slug}`}
        className={styles.viewerImage}
        onClick={() => handleImageClick(image)}
        draggable='false'
        onContextMenu={e => e.preventDefault()}
        onError={() => setHasError(true)}
      />
      {hasError && (
        <div className={styles.placeholderOverlay}>
          <span className={styles.placeholderText}>[Placeholder]</span>
        </div>
      )}
    </>
  );
};

export default TravelHighlightsPage;
