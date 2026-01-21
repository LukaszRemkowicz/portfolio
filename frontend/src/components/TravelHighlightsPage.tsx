import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import styles from "../styles/components/TravelHighlightsPage.module.css";
import { API_ROUTES, getMediaUrl, ASSETS } from "../api/routes";
import { AstroImage } from "../types";
import { api } from "../api/api";
import ImageModal from "./common/ImageModal";
import LoadingScreen from "./common/LoadingScreen";
import StarBackground from "./StarBackground";
import { useAppStore } from "../store/useStore";
import { sanitizeHtml } from "../utils/html";

const TravelHighlightsPage: React.FC = () => {
  const { countrySlug, placeSlug } = useParams<{
    countrySlug: string;
    placeSlug?: string;
  }>();

  const [images, setImages] = useState<AstroImage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalImage, setModalImage] = useState<AstroImage | null>(null);
  const [country, setCountry] = useState<string>("");
  const [place, setPlace] = useState<string | null>(null);
  const [story, setStory] = useState<string | null>(null);
  const [adventureDate, setAdventureDate] = useState<string | null>(null);
  const [createdAt, setCreatedAt] = useState<string | null>(null);
  const [highlightName, setHighlightName] = useState<string | null>(null);
  const [locationBackgroundImage, setLocationBackgroundImage] = useState<
    string | null
  >(null);

  const { backgroundUrl, loadInitialData } = useAppStore();

  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  useEffect(() => {
    const loadData = async () => {
      if (!countrySlug) {
        setError("No location specified");
        setLoading(false);
        return;
      }

      setLoading(true);
      setError(null);
      try {
        // Build slug-based URL
        const slugPath = placeSlug
          ? `${countrySlug}/${placeSlug}`
          : `${countrySlug}`;

        // Fetch from new slug-based endpoint
        const response = await api.get(
          `${API_ROUTES.travelBySlug}${slugPath}/`,
        );

        const data = response.data;

        // Validate response structure
        if (!data || typeof data !== "object") {
          throw new Error("Invalid API response structure");
        }

        // Set metadata with fallbacks
        setCountry(data.country || "");
        setPlace(data.place || null);
        setStory(data.story || null);
        setAdventureDate(data.adventure_date || null);
        setCreatedAt(data.created_at || null);
        setHighlightName(data.highlight_name || null);
        setLocationBackgroundImage(data.background_image || null);

        // Process images with defensive checks
        const imagesArray = Array.isArray(data.images) ? data.images : [];
        const processedImages = imagesArray.map((image: AstroImage) => ({
          ...image,
          url: getMediaUrl(image.url) || "",
          thumbnail_url: getMediaUrl(image.thumbnail_url) || undefined,
        }));

        setImages(processedImages);
      } catch (err) {
        console.error("Failed to load travel highlights:", err);
        setError(
          "Failed to load travel highlights. Please check the URL and try again.",
        );
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [countrySlug, placeSlug]);

  const handleImageClick = (image: AstroImage): void => {
    setModalImage(image);
  };

  if (loading) return <LoadingScreen />;
  if (error) return <div className={styles.error}>{error}</div>;

  // Display title: "Place, Country" or just "Country"
  const displayTitle =
    place && country ? `${place}, ${country}` : country || "Travel Highlights";

  return (
    <div className={styles.container}>
      <StarBackground />
      <div
        className={styles.hero}
        style={
          locationBackgroundImage || backgroundUrl
            ? {
                backgroundImage: `linear-gradient(rgba(2, 4, 10, 0.8), rgba(2, 4, 10, 0.8)), url(${getMediaUrl(locationBackgroundImage || backgroundUrl)})`,
                backgroundSize: "cover",
                backgroundPosition: "center",
              }
            : {
                backgroundImage: `url(${ASSETS.galleryFallback})`,
              }
        }
      >
        <h1 className={styles.heroTitle}>{displayTitle}</h1>
        <p className={styles.heroSubtitle}>
          Exploring the cosmic wonders of {displayTitle}
        </p>
      </div>

      {/* Dynamic Story Section */}
      {story && story.trim().length > 0 && (
        <section className={styles.expeditionContainer}>
          <div className={styles.glassCard}>
            <header className={styles.metaInfo}>
              <span className={styles.badge}>
                ADVENTURE DATE |{" "}
                {adventureDate
                  ? adventureDate.toUpperCase()
                  : createdAt
                    ? new Date(createdAt)
                        .toLocaleDateString("en-US", {
                          month: "long",
                          year: "numeric",
                        })
                        .toUpperCase()
                    : "RECENT EXPEDITION"}
              </span>
            </header>

            <h2 className={styles.storyTitle}>
              {highlightName || "About this place"}
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
            {images.map((image) => (
              <div key={image.pk} className={styles.viewerContainer}>
                <div className={styles.viewerFrame}>
                  <div className={styles.imageWrapper}>
                    <img
                      src={image.url}
                      alt={image.name}
                      className={styles.viewerImage}
                      onClick={() => handleImageClick(image)}
                    />
                  </div>

                  <div className={styles.viewerDetails}>
                    <h4 className={styles.imageTitle}>{image.name}</h4>
                    <div
                      className={styles.imageDescription}
                      dangerouslySetInnerHTML={{
                        __html: sanitizeHtml(
                          image.description || "No description available.",
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
