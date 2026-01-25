import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import styles from '../styles/components/Gallery.module.css';
import { AstroImage } from '../types';
import { useAppStore } from '../store/useStore';
import ImageModal from './common/ImageModal';
import GalleryCard from './common/GalleryCard';

const Gallery: React.FC = () => {
  const [filter, setFilter] = useState('all');
  const images = useAppStore(state => state.images);
  const loading = useAppStore(state => state.isImagesLoading);
  const error = useAppStore(state => state.error);
  const loadImages = useAppStore(state => state.loadImages);
  const features = useAppStore(state => state.features);
  const [modalImage, setModalImage] = useState<AstroImage | null>(null);
  const [searchParams, setSearchParams] = useSearchParams();

  // Sync modalImage with 'img' query parameter
  useEffect(() => {
    const imgId = searchParams.get('img');
    if (imgId) {
      const img = images.find(i => i.pk.toString() === imgId);
      if (img) {
        setModalImage(img);
      } else {
        setModalImage(null);
      }
    } else {
      setModalImage(null);
    }
  }, [searchParams, images]);

  useEffect(() => {
    if (features?.lastimages !== false) {
      loadImages({ limit: 50 });
    }
  }, [loadImages, features]);

  const filteredImages = useMemo(() => {
    if (filter === 'all') return images.slice(0, 9);

    const categoryMap: Record<string, string> = {
      deepsky: 'deepsky',
      astrolandscape: 'astrolandscape',
      timelapse: 'timelapses',
    };

    const targetCategory = categoryMap[filter] || filter;

    return images
      .filter(img => img.tags && img.tags.includes(targetCategory))
      .sort((a, b) => {
        const dateA = new Date(a.created_at || 0).getTime();
        const dateB = new Date(b.created_at || 0).getTime();
        return dateB - dateA;
      })
      .slice(0, 9);
  }, [images, filter]);

  const handleImageClick = useCallback(
    (image: AstroImage): void => {
      console.log('Card clicked!', image.name);
      // Use URL params for modal state to support browser back button
      searchParams.set('img', image.pk.toString());
      setSearchParams(searchParams);
    },
    [searchParams, setSearchParams]
  );

  const closeModal = useCallback(() => {
    searchParams.delete('img');
    setSearchParams(searchParams);
  }, [searchParams, setSearchParams]);

  // Hide the entire section if disabled via admin toggle or if no images
  if (features?.lastimages === false || (!loading && images.length === 0)) {
    return null;
  }

  return (
    <section id='gallery' className={styles.section}>
      <div className={styles.header}>
        <h2 className={styles.title}>Latest images</h2>
        <div className={styles.filters}>
          <button
            type='button'
            onClick={() => setFilter('all')}
            className={`${styles.filterBtn} ${
              filter === 'all' ? styles.active : ''
            }`}
          >
            All Works
          </button>
          <button
            type='button'
            onClick={() => setFilter('deepsky')}
            className={`${styles.filterBtn} ${
              filter === 'deepsky' ? styles.active : ''
            }`}
          >
            Deep Sky
          </button>
          <button
            type='button'
            onClick={() => setFilter('astrolandscape')}
            className={`${styles.filterBtn} ${
              filter === 'astrolandscape' ? styles.active : ''
            }`}
          >
            Astrolandscape
          </button>
          <button
            type='button'
            onClick={() => setFilter('timelapse')}
            className={`${styles.filterBtn} ${
              filter === 'timelapse' ? styles.active : ''
            }`}
          >
            Timelapses
          </button>
        </div>
      </div>

      <div className={styles.grid}>
        {loading ? (
          <div className={styles.loading}>Loading Portfolio...</div>
        ) : error ? (
          <div className={styles.error}>{error}</div>
        ) : filteredImages.length > 0 ? (
          filteredImages.map(item => (
            <GalleryCard key={item.pk} item={item} onClick={handleImageClick} />
          ))
        ) : (
          <div className={styles.noResults}>
            No works found in this category.
          </div>
        )}
      </div>

      <ImageModal image={modalImage} onClose={closeModal} />
    </section>
  );
};

export default Gallery;
