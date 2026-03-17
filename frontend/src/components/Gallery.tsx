import React, { useState, useMemo, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { APP_ROUTES } from '../api/constants';
import styles from '../styles/components/Gallery.module.css';
import { AstroImage } from '../types';
import GalleryCard from './common/GalleryCard';
import GallerySkeleton from './skeletons/GallerySkeleton';
import { useSettings } from '../hooks/useSettings';
import { useLatestAstroImages } from '../hooks/useLatestAstroImages';

const Gallery: React.FC = () => {
  const { t } = useTranslation();
  const [filter, setFilter] = useState('all');
  const navigate = useNavigate();

  const { data: settings } = useSettings();
  const features = settings;
  const {
    data: images = [],
    isLoading: loading,
    error: queryError,
  } = useLatestAstroImages();
  const error = queryError ? 'Failed to load latest images.' : null;

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
      // Navigate to the full gallery page with the modal pre-opened
      navigate(`${APP_ROUTES.ASTROPHOTOGRAPHY}/${image.slug}`);
    },
    [navigate]
  );

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
          <GallerySkeleton count={6} />
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
    </section>
  );
};

export default Gallery;
