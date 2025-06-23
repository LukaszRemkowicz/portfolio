import React, { useState, useEffect } from 'react';
import styles from './AstroGallery.module.css';
import { fetchAstroImages, fetchBackground } from './api/services';
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

  const loadImages = async (filter = null) => {
    try {
      setError('');
      setLoading(true);
      let params = {};
      if (filter) {
        params.filter = filter; // send as-is
      }
      const data = await fetchAstroImages(params);
      setImages(data);
    } catch (err) {
      setError('Failed to load images. Please try again later.');
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
            <img src={image.url} alt={`Astro Image ${image.pk}`} />
          </div>
        ))}
      </div>
    </div>
  );
};

export default AstroGallery; 