import React, { useState, useMemo, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { useSearchParams } from 'react-router-dom';
import styles from '../styles/components/Gallery.module.css';
import { AstroImage } from '../types';
import { useAstroImages } from '../hooks/useAstroImages';
import { useSettings } from '../hooks/useSettings';
import ImageModal from './common/ImageModal';
import GalleryCard from './common/GalleryCard';

const Gallery: React.FC = () => {
  const { t } = useTranslation();
  const [filter, setFilter] = useState('all');
  const {
    data: images = [],
    isLoading: loading,
    error: queryError,
  } = useAstroImages({ limit: 50 });
  const { data: settings } = useSettings();
  const error = queryError ? (queryError as Error).message : null;
  const features = settings;
  const [searchParams, setSearchParams] = useSearchParams();
  const imgId = searchParams.get('img');

  const modalImage = useMemo(() => {
    if (!imgId) return null;
    return (
      images.find(i => i.slug === imgId || i.pk.toString() === imgId) || null
    );
  }, [imgId, images]);

  // No longer need manual image loading effect

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
      searchParams.set('img', image.slug);
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
        <h2 className={styles.title}>{t('gallery.title')}</h2>
        <div className={styles.filters}>
          <button
            type='button'
            onClick={() => setFilter('all')}
            className={`${styles.filterBtn} ${
              filter === 'all' ? styles.active : ''
            }`}
          >
            {t('gallery.all')}
          </button>
          <button
            type='button'
            onClick={() => setFilter('deepsky')}
            className={`${styles.filterBtn} ${
              filter === 'deepsky' ? styles.active : ''
            }`}
          >
            {t('categories.Deep Sky')}
          </button>
          <button
            type='button'
            onClick={() => setFilter('astrolandscape')}
            className={`${styles.filterBtn} ${
              filter === 'astrolandscape' ? styles.active : ''
            }`}
          >
            {t('gallery.astrolandscape')}
          </button>
          <button
            type='button'
            onClick={() => setFilter('timelapse')}
            className={`${styles.filterBtn} ${
              filter === 'timelapse' ? styles.active : ''
            }`}
          >
            {t('gallery.timelapses')}
          </button>
        </div>
      </div>

      <div className={styles.grid}>
        {loading ? (
          <div className={styles.loading}>{t('gallery.loading')}</div>
        ) : error ? (
          <div className={styles.error}>{error}</div>
        ) : filteredImages.length > 0 ? (
          filteredImages.map(item => (
            <GalleryCard key={item.pk} item={item} onClick={handleImageClick} />
          ))
        ) : (
          <div className={styles.noResults}>{t('gallery.empty')}</div>
        )}
      </div>

      <ImageModal image={modalImage} onClose={closeModal} />
    </section>
  );
};

export default Gallery;
