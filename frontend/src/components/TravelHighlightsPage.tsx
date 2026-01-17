import React, { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import styles from "../styles/components/TravelHighlightsPage.module.css";
import { ASSETS } from "../api/routes";
import { AstroImage } from "../types";
import { fetchAstroImages, fetchTravelHighlights } from "../api/services";
import ImageModal from "./common/ImageModal";
import LoadingScreen from "./common/LoadingScreen";

const TravelHighlightsPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const countryParam = searchParams.get("country");
  const placeParam = searchParams.get("place");

  const [images, setImages] = useState<AstroImage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalImage, setModalImage] = useState<AstroImage | null>(null);
  const [locationInfo, setLocationInfo] = useState<{
    country: string;
    place: string;
  }>({ country: "", place: "" });

  // Load location info from sliders
  useEffect(() => {
    const loadLocationInfo = async () => {
      if (!countryParam) return;
      try {
        const sliders = await fetchTravelHighlights();
        const slider = sliders.find(
          (s) =>
            s.country === countryParam &&
            (!placeParam || s.place_name === placeParam),
        );
        if (slider) {
          setLocationInfo({
            country: slider.country_name,
            place: slider.place_name || "",
          });
        }
      } catch (err) {
        console.error("Failed to load location info:", err);
      }
    };
    loadLocationInfo();
  }, [countryParam, placeParam]);

  // Load images for the location
  useEffect(() => {
    const loadImages = async () => {
      if (!countryParam) {
        setError("No country specified");
        setLoading(false);
        return;
      }

      setLoading(true);
      setError(null);
      try {
        // Pass country and place as separate parameters
        const params: Record<string, string> = { country: countryParam };
        if (placeParam) {
          params.place = placeParam;
        }
        const data = await fetchAstroImages(params);

        // Filter images to only show those with a location (travel images)
        const travelImages = data.filter((img) => img.location);
        setImages(travelImages);
      } catch (err) {
        console.error("Failed to load images:", err);
        setError("Failed to load images");
      } finally {
        setLoading(false);
      }
    };
    loadImages();
  }, [countryParam, placeParam]);

  const handleImageClick = (image: AstroImage): void => {
    setModalImage(image);
  };

  // Shorten certain country names for display
  const shortenCountryName = (countryName: string): string => {
    const shortNames: Record<string, string> = {
      "United States of America": "USA",
      "United Kingdom": "UK",
      "United Arab Emirates": "UAE",
    };
    return shortNames[countryName] || countryName;
  };

  if (loading) return <LoadingScreen />;
  if (error) return <div className={styles.error}>{error}</div>;

  const shortCountryName = shortenCountryName(locationInfo.country);

  // Display title: "Place, Country" or just "Country"
  const displayTitle =
    locationInfo.place && shortCountryName
      ? `${locationInfo.place}, ${shortCountryName}`
      : shortCountryName || "Travel Highlights";

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
