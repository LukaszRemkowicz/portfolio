import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import styles from "../styles/components/TravelHighlightsPage.module.css";
import { API_ROUTES, getMediaUrl, ASSETS } from "../api/routes";
import { AstroImage } from "../types";
import { api } from "../api/api";
import ImageModal from "./common/ImageModal";
import LoadingScreen from "./common/LoadingScreen";

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
      <div
        className={styles.hero}
        style={{
          backgroundImage: `url(${ASSETS.galleryFallback})`,
        }}
      >
        <h1 className={styles.heroTitle}>{displayTitle}</h1>
        <p className={styles.heroSubtitle}>
          Exploring the cosmic wonders of {displayTitle}
        </p>
      </div>

      <div className={styles.grid}>
        {images.length > 0 ? (
          images.map((image: AstroImage) => (
            <div key={image.pk} className={styles.gridItem}>
              <img
                src={image.thumbnail_url || image.url}
                alt={image.name || `Travel Image ${image.pk}`}
                onClick={() => handleImageClick(image)}
                style={{ cursor: "pointer" }}
              />
            </div>
          ))
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
