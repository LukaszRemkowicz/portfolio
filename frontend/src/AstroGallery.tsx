import React, { useState, useEffect } from 'react';
import styles from './styles/components/AstroGallery.module.css';
import {
  fetchAstroImages,
  fetchBackground,
  fetchAstroImage,
} from './api/services';
// import { API_BASE_URL } from './api/routes';
import { AstroImage, FilterParams, FilterType } from './types';

const GALLERY_BG = '/startrails.jpeg'; // fallback static image

const FILTERS: FilterType[] = [
  'Landscape',
  'Deep Sky',
  'Startrails',
  'Solar System',
  'Milky Way',
  'Northern Lights',
];

const AstroGallery: React.FC = () => {
  const [images, setImages] = useState<AstroImage[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>('');
  const [background, setBackground] = useState<string>(GALLERY_BG);
  const [selectedFilter, setSelectedFilter] = useState<string | null>(null);
  const [modalImage, setModalImage] = useState<AstroImage | null>(null);
  const [modalDescription, setModalDescription] = useState<string>('');
  const [modalDescriptionLoading, setModalDescriptionLoading] =
    useState<boolean>(false);

  const loadImages = async (filter: string | null = null): Promise<void> => {
    try {
      setError('');
      setLoading(true);
      let params: FilterParams = {};
      if (filter) {
        params.filter = filter; // send as-is
      }
      const data: AstroImage[] = await fetchAstroImages(params);
      setImages(Array.isArray(data) ? data : []);
    } catch (err: unknown) {
      setError('Failed to load images. Please try again later.');
      setImages([]); // Ensure images is always an array on error
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadImages(selectedFilter);
  }, [selectedFilter]);

  useEffect(() => {
    // Try to fetch a background from the backend, fallback to static
    const loadBackground = async (): Promise<void> => {
      try {
        const bg: string | null = await fetchBackground();
        if (bg) setBackground(bg);
      } catch {
        setBackground(GALLERY_BG);
      }
    };
    loadBackground();
  }, []);

  // Fetch description when modalImage changes
  useEffect(() => {
    if (!modalImage) return;
    setModalDescription('');
    setModalDescriptionLoading(true);
    fetchAstroImage(modalImage.pk)
      .then((data: AstroImage) => {
        setModalDescription(data.description || 'No description available.');
        // Optionally update modalImage with full data if needed
        // setModalImage(img => ({ ...img, ...data }));
      })
      .catch(() => {
        setModalDescription('No description available.');
      });

    // Always stop loading
    setModalDescriptionLoading(false);
  }, [modalImage]);

  // Close modal on Escape key
  useEffect(() => {
    if (!modalImage) return;
    const handleKeyDown = (e: KeyboardEvent): void => {
      if (e.key === 'Escape') {
        closeModal();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [modalImage]);

  const closeModal = (): void => setModalImage(null);

  const handleFilterClick = (filter: FilterType): void => {
    setSelectedFilter(selectedFilter === filter ? null : filter);
  };

  const handleImageClick = (image: AstroImage): void => {
    setModalImage(image);
  };

  const handleModalOverlayClick = (): void => {
    closeModal();
  };

  const handleModalContentClick = (
    e: React.MouseEvent<HTMLDivElement>
  ): void => {
    e.stopPropagation();
  };

  if (loading) return <div className={styles.loading}>Loading...</div>;
  if (error) return <div className={styles.error}>{error}</div>;

  return (
    <div className={styles.container}>
      <div
        className={styles.hero}
        style={{ backgroundImage: `url(${background})` }}
      >
        <h1 className={styles.heroTitle}>Gallery</h1>
      </div>
      <div className={styles.filtersSection}>
        {FILTERS.map((filter: FilterType) => (
          <div
            key={filter}
            className={`${styles.filterBox} ${
              selectedFilter === filter ? styles.activeFilter : ''
            }`}
            onClick={() => handleFilterClick(filter)}
          >
            {filter}
          </div>
        ))}
      </div>
      <div className={styles.grid}>
        {images.map((image: AstroImage) => (
          <div key={image.pk} className={styles.gridItem}>
            <img
              src={image.url}
              alt={`Astro Image ${image.pk}`}
              onClick={() => handleImageClick(image)}
              style={{ cursor: 'pointer' }}
            />
          </div>
        ))}
      </div>
      {modalImage && (
        <div className={styles.modalOverlay} onClick={handleModalOverlayClick}>
          <div
            className={styles.modalContent}
            onClick={handleModalContentClick}
          >
            <button className={styles.modalClose} onClick={closeModal}>
              &times;
            </button>
            <img
              src={modalImage.url}
              alt='Astro Large'
              className={styles.modalImage}
            />
            <div className={styles.modalDescription}>
              {modalDescriptionLoading
                ? 'Loading description...'
                : modalDescription}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AstroGallery;
