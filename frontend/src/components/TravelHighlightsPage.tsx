import React, { useState, useEffect, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { useParams, useSearchParams } from 'react-router-dom';
import styles from '../styles/components/TravelHighlightsPage.module.css';
import { API_ROUTES, getMediaUrl, ASSETS } from '../api/routes';
import { AstroImage } from '../types';
import { api } from '../api/api';
import ImageModal from './common/ImageModal';
import LoadingScreen from './common/LoadingScreen';
import StarBackground from './StarBackground';
import { useAppStore } from '../store/useStore';
import { sanitizeHtml } from '../utils/html';

interface ExtendedAstroImage extends AstroImage {
  url?: string;
}

const TravelHighlightsPage: React.FC = () => {
  const { t, i18n } = useTranslation();
  const { countrySlug, placeSlug, dateSlug } = useParams<{
    countrySlug: string;
    placeSlug?: string;
    dateSlug?: string;
  }>();

  const [images, setImages] = useState<ExtendedAstroImage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchParams, setSearchParams] = useSearchParams();
  const imgParam = searchParams.get('img');
  const [fullLocation, setFullLocation] = useState<string>('Travel Highlights');
  const [story, setStory] = useState<string | null>(null);
  const [adventureDate, setAdventureDate] = useState<string | null>(null);
  const [highlightName, setHighlightName] = useState<string | null>(null);
  const [highlightTitle, setHighlightTitle] = useState<string | null>(null);
  const [locationBackgroundImage, setLocationBackgroundImage] = useState<
    string | null
  >(null);

  const { backgroundUrl, loadInitialData, loadImageUrls, imageUrls } =
    useAppStore();

  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  useEffect(() => {
    const loadData = async () => {
      if (!countrySlug || !placeSlug || !dateSlug) {
        setError(
          'Incomplete location specified. URL must contain country, place, and date.'
        );
        setLoading(false);
        return;
      }

      setLoading(true);
      setError(null);
      try {
        // Fetch from new strict 3-segment endpoint
        const response = await api.get(
          `${API_ROUTES.travelBySlug}${countrySlug}/${placeSlug}/${dateSlug}/`
        );

        const data = response.data;

        // Validate response structure
        if (!data || typeof data !== 'object') {
          throw new Error('Invalid API response structure');
        }

        // Set metadata using new pre-formatted fields
        setFullLocation(data.full_location || 'Travel Highlights');
        setStory(data.story || null);
        setAdventureDate(data.adventure_date || null);
        setHighlightName(data.highlight_name || null);
        setHighlightTitle(data.highlight_title || null);
        setLocationBackgroundImage(data.background_image || null);

        // Process images with defensive checks
        // ... (rest of logic unchanged)
        const imagesArray = Array.isArray(data.images) ? data.images : [];
        const processedImages: ExtendedAstroImage[] = imagesArray.map(
          (image: AstroImage) => ({
            ...image,
            thumbnail_url: getMediaUrl(image.thumbnail_url) || undefined,
            url: undefined, // Initialize url clearly
          })
        );

        setImages(processedImages);

        // Fetch full resolution URLs for all images
        if (imagesArray.length > 0) {
          const imageIds = imagesArray.map((img: AstroImage) => img.pk);
          // Trigger store action to fetch URLs
          await loadImageUrls(imageIds);
        }
      } catch {
        setError(
          'Failed to load travel highlights. Please check the URL and try again.'
        );
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [countrySlug, placeSlug, dateSlug, i18n.language, loadImageUrls]);

  // Derive modal image from URL parameter
  const modalImage = useMemo(() => {
    if (!imgParam) return null;
    const found = images.find(
      i => i.slug === imgParam || i.pk.toString() === imgParam
    );
    if (!found) return null;

    // Enhance with full-res URL if available
    const fullResUrl = imageUrls[found.slug];
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
                    <img
                      src={image.thumbnail_url}
                      alt={image.name}
                      className={styles.viewerImage}
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
      <ImageModal image={modalImage} onClose={closeModal} />
    </div>
  );
};

export default TravelHighlightsPage;
