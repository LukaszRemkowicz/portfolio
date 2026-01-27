import React, { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import styles from '../styles/components/AstroGallery.module.css';
import { ASSETS } from '../api/routes';
import { AstroImage, FilterType } from '../types';
import { useAppStore } from '../store/useStore';
import ImageModal from './common/ImageModal';
import LoadingScreen from './common/LoadingScreen';
import GalleryCard from './common/GalleryCard';
import TagSidebar from './TagSidebar';
import { Sliders } from 'lucide-react';

const AstroGallery: React.FC = () => {
  const images = useAppStore(state => state.images);
  const isInitialLoading = useAppStore(state => state.isInitialLoading);
  const isImagesLoading = useAppStore(state => state.isImagesLoading);
  const categories = useAppStore(state => state.categories);
  const tags = useAppStore(state => state.tags);
  const background = useAppStore(state => state.backgroundUrl);
  const error = useAppStore(state => state.error);
  const loadInitialData = useAppStore(state => state.loadInitialData);
  const loadImages = useAppStore(state => state.loadImages);
  const loadCategories = useAppStore(state => state.loadCategories);
  const loadTags = useAppStore(state => state.loadTags);
  const [searchParams, setSearchParams] = useSearchParams();
  const [modalImage, setModalImage] = useState<AstroImage | null>(null);
  const [isTagsDrawerOpen, setIsTagsDrawerOpen] = useState(false);
  const resultsRef = useRef<HTMLDivElement>(null);

  const selectedFilter = searchParams.get('filter') as FilterType | null;
  const selectedTag = searchParams.get('tag');

  useEffect(() => {
    const imgParam = searchParams.get('img');
    if (imgParam) {
      // Lookup by slug (primary) or pk (fallback)
      const img = images.find(
        i => i.slug === imgParam || i.pk.toString() === imgParam
      );
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
    loadInitialData();
    loadCategories();
  }, [loadInitialData, loadCategories]);

  useEffect(() => {
    loadImages({
      ...(selectedFilter ? { filter: selectedFilter } : {}),
      ...(selectedTag ? { tag: selectedTag } : {}),
    });
  }, [selectedFilter, selectedTag, loadImages]);

  // Refresh tags when category changes
  useEffect(() => {
    loadTags(selectedFilter || undefined);
  }, [selectedFilter, loadTags]);

  // Smooth scroll to results on filter/tag change (Mobile only)
  useEffect(() => {
    if (window.innerWidth <= 992 && resultsRef.current) {
      const yOffset = -100; // Offset for sticky navbar/header
      const element = resultsRef.current;
      const y =
        element.getBoundingClientRect().top + window.pageYOffset + yOffset;
      window.scrollTo({ top: y, behavior: 'smooth' });
    }
  }, [selectedFilter, selectedTag]);

  const handleFilterClick = (filter: FilterType): void => {
    const nextParams = new URLSearchParams(searchParams);
    if (selectedFilter === filter) {
      nextParams.delete('filter');
    } else {
      nextParams.set('filter', filter);
      nextParams.delete('tag');
    }
    setSearchParams(nextParams);
  };

  const handleTagSelect = (tagSlug: string | null): void => {
    const nextParams = new URLSearchParams(searchParams);
    if (tagSlug) {
      nextParams.set('tag', tagSlug);
    } else {
      nextParams.delete('tag');
    }
    setSearchParams(nextParams);
    setIsTagsDrawerOpen(false);
  };

  const toggleTagsDrawer = (): void => {
    setIsTagsDrawerOpen(!isTagsDrawerOpen);
  };

  const handleImageClick = (image: AstroImage): void => {
    const nextParams = new URLSearchParams(searchParams);
    nextParams.set('img', image.slug || image.pk.toString());
    setSearchParams(nextParams);
  };

  const closeModal = (): void => {
    const nextParams = new URLSearchParams(searchParams);
    nextParams.delete('img');
    setSearchParams(nextParams);
  };

  if (isInitialLoading) return <LoadingScreen />;
  if (error) return <div className={styles.error}>{error}</div>;

  return (
    <div className={styles.container}>
      <div
        className={styles.hero}
        style={{
          backgroundImage: `url(${background || ASSETS.galleryFallback})`,
        }}
      >
        <h1 className={styles.heroTitle}>Gallery</h1>
      </div>
      <div className={styles.mainContent}>
        <h3 className={styles.sidebarLabel}>
          Filter by category or explore images using the tags below.
        </h3>

        <button
          className={styles.mobileFilterToggle}
          onClick={toggleTagsDrawer}
          aria-expanded={isTagsDrawerOpen}
        >
          <Sliders size={18} />
          Explore Tags
        </button>

        <div
          className={`${styles.overlay} ${isTagsDrawerOpen ? styles.visible : ''}`}
          onClick={toggleTagsDrawer}
        />

        <div className={styles.sidebarContainer}>
          <TagSidebar
            tags={tags}
            selectedTag={selectedTag}
            onTagSelect={handleTagSelect}
            isOpen={isTagsDrawerOpen}
            onToggle={toggleTagsDrawer}
          />
        </div>

        <div className={styles.filtersSection}>
          {categories.map((filter: FilterType) => {
            const isActive = selectedFilter === filter;
            return (
              <button
                key={filter}
                type='button'
                className={`${styles.filterBox} ${isActive ? styles.activeFilter : ''}`}
                onClick={() => handleFilterClick(filter)}
                aria-pressed={isActive}
              >
                {filter}
              </button>
            );
          })}
        </div>

        <div className={styles.gridSection}>
          <div ref={resultsRef} className={styles.scrollAnchor} />
          <div className={styles.grid}>
            {isImagesLoading ? (
              <div className={styles.noResults}>
                <p>Scanning deep space sectors...</p>
              </div>
            ) : images.length > 0 ? (
              images.map((image: AstroImage) => (
                <GalleryCard
                  key={image.pk}
                  item={image}
                  onClick={handleImageClick}
                />
              ))
            ) : (
              <div className={styles.noResults}>
                <p>No images found for this filter.</p>
                <p className={styles.noResultsHint}>
                  Try selecting a different category or tag to see more images.
                </p>
              </div>
            )}
          </div>
        </div>
        <ImageModal image={modalImage} onClose={closeModal} />
      </div>
    </div>
  );
};

export default AstroGallery;
