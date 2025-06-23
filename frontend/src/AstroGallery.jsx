import React, { useState, useEffect } from 'react';
import styles from './AstroGallery.module.css';
import { fetchAstroImages } from './api/services';

const AstroGallery = () => {
  const [images, setImages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const loadImages = async () => {
      try {
        setError('');
        setLoading(true);
        const data = await fetchAstroImages();
        setImages(data);
      } catch (err) {
        setError('Failed to load images. Please try again later.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    loadImages();
  }, []);

  if (loading) return <div className={styles.loading}>Loading...</div>;
  if (error) return <div className={styles.error}>{error}</div>;

  return (
    <div className={styles.container}>
      <h1 className={styles.title}>Astrokrajobraz</h1>
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