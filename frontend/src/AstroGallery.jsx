import React, { useState, useEffect } from 'react';
import styles from './styles/components/AstroGallery.module.css';
import { fetchAstroImages, fetchBackground, fetchAstroImage } from './api/services';
import { API_BASE_URL } from './api/routes';
// import Navbar from './Navbar';

const GALLERY_BG = '/startrails.jpeg'; // fallback static image

const FILTERS = [
  'Landscape',
  'Deep Sky',
  'Startrails',
  'Solar System',
  'Milky Way',
  'Northern Lights',
];

const AstroGallery = () => {
  const [images, setImages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [background, setBackground] = useState(GALLERY_BG);
  const [selectedFilter, setSelectedFilter] = useState(null);
  const [modalImage, setModalImage] = useState(null);
  const [modalDescription, setModalDescription] = useState('');
  const [modalDescriptionLoading, setModalDescriptionLoading] = useState(false);

  const loadImages = async (filter = null) => {
    try {
      setError('');
      setLoading(true);
      let params = {};
      if (filter) {
        params.filter = filter; // send as-is
      }
      const data = await fetchAstroImages(params);
      setImages(Array.isArray(data) ? data : []);
    } catch (err) {
      setError('Failed to load images. Please try again later.');
      setImages([]); // Ensure images is always an array on error
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadImages(selectedFilter);
    // eslint-disable-next-line
  }, [selectedFilter]);

  useEffect(() => {
    // Try to fetch a background from the backend, fallback to static
    const loadBackground = async () => {
      try {
        const bg = await fetchBackground();
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
      .then(data => {
        setModalDescription(data.description || 'No description available.');
        // Optionally update modalImage with full data if needed
        // setModalImage(img => ({ ...img, ...data }));
      })
      .catch(() => {
        setModalDescription('No description available.');
      })
      .finally(() => setModalDescriptionLoading(false));
  }, [modalImage]);

  // Close modal on Escape key
  useEffect(() => {
    if (!modalImage) return;
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        closeModal();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [modalImage]);

  const closeModal = () => setModalImage(null);

  if (loading) return <div className={styles.loading}>Loading...</div>;
  if (error) return <div className={styles.error}>{error}</div>;

  return (
    <div className={styles.container}>
      {/* <Navbar transparent /> */}
      <div
        className={styles.hero}
        style={{ backgroundImage: `url(${background})` }}
      >
        <h1 className={styles.heroTitle}>Gallery</h1>
      </div>
      <div className={styles.filtersSection}>
        {FILTERS.map((filter) => (
          <div
            key={filter}
            className={`${styles.filterBox} ${selectedFilter === filter ? styles.activeFilter : ''}`}
            onClick={() => setSelectedFilter(selectedFilter === filter ? null : filter)}
          >
            {filter}
          </div>
        ))}
      </div>
      <div className={styles.grid}>
        {images.map(image => (
          <div key={image.pk} className={styles.gridItem}>
            <img
              src={image.url}
              alt={`Astro Image ${image.pk}`}
              onClick={() => setModalImage(image)}
              style={{ cursor: 'pointer' }}
            />
          </div>
        ))}
      </div>
      {modalImage && (
        <div className={styles.modalOverlay} onClick={closeModal}>
          <div className={styles.modalContent} onClick={e => e.stopPropagation()}>
            <button className={styles.modalClose} onClick={closeModal}>&times;</button>
            <img src={modalImage.url} alt="Astro Large" className={styles.modalImage} />
            <div className={styles.modalDescription}>
              {modalDescriptionLoading ? 'Loading description...' : modalDescription}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AstroGallery; 