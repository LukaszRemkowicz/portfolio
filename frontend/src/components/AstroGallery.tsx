import React, { useState, useEffect, useRef, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import styles from '../styles/components/AstroGallery.module.css';
import { ASSETS } from '../api/routes';
import { AstroImage, FilterType } from '../types';
import { useAppStore } from '../store/useStore';
import ImageModal from './common/ImageModal';
import LoadingScreen from './common/LoadingScreen';
import GalleryCard from './common/GalleryCard';
import TagSidebar from './TagSidebar';
import CategorySidebar from './CategorySidebar';
import { Sliders, LayoutGrid } from 'lucide-react';

const AstroGallery: React.FC = () => {
  const images = useAppStore(state => state.images);
  const categories = useAppStore(state => state.categories);
  const isInitialLoading = useAppStore(state => state.isInitialLoading);
  const isImagesLoading = useAppStore(state => state.isImagesLoading);
  const tags = useAppStore(state => state.tags);
  const background = useAppStore(state => state.backgroundUrl);
  const error = useAppStore(state => state.error);
  const loadInitialData = useAppStore(state => state.loadInitialData);
  const loadImages = useAppStore(state => state.loadImages);
  const loadCategories = useAppStore(state => state.loadCategories);
  const loadTags = useAppStore(state => state.loadTags);
  const [searchParams, setSearchParams] = useSearchParams();
  const [isTagsDrawerOpen, setIsTagsDrawerOpen] = useState(false);
  const [isFiltersOpen, setIsFiltersOpen] = useState(false);
  const resultsRef = useRef<HTMLDivElement>(null);

  const selectedFilter = searchParams.get('filter') as FilterType | null;
  const selectedTag = searchParams.get('tag');
  const imgParam = searchParams.get('img');

  const modalImage = useMemo(() => {
    if (!imgParam) return null;
    return (
      images.find(i => i.slug === imgParam || i.pk.toString() === imgParam) ||
      null
    );
  }, [imgParam, images]);

  useEffect(() => {
    loadInitialData();
    loadCategories();
  }, [loadInitialData, loadCategories]);

  const { t, i18n } = useTranslation();

  useEffect(() => {
    loadImages({
      ...(selectedFilter ? { filter: selectedFilter } : {}),
      ...(selectedTag ? { tag: selectedTag } : {}),
    });
  }, [selectedFilter, selectedTag, loadImages, i18n.language]);

  // Refresh tags when category changes
  useEffect(() => {
    loadTags(selectedFilter || undefined);
  }, [selectedFilter, loadTags, i18n.language]);

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
      setIsFiltersOpen(false); // Close menu on selection
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
    if (isFiltersOpen) setIsFiltersOpen(false);
  };

  const toggleFilters = (): void => {
    setIsFiltersOpen(!isFiltersOpen);
    if (isTagsDrawerOpen) setIsTagsDrawerOpen(false);
  };

  const handleImageClick = (image: AstroImage): void => {
    const nextParams = new URLSearchParams(searchParams);
    nextParams.set('img', image.slug);
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
        <h1 className={styles.heroTitle}>{t('common.gallery')}</h1>
      </div>
      <div className={styles.mainContent}>
        <h3 className={styles.sidebarLabel}>{t('common.gallerySubtitle')}</h3>

        <div className={styles.mobileActions}>
          <button
            className={styles.mobileFilterToggle}
            onClick={toggleTagsDrawer}
            aria-expanded={isTagsDrawerOpen}
          >
            <Sliders size={18} />
            {t('common.exploreTags')}
          </button>

          <button
            className={styles.mobileFilterToggle}
            onClick={toggleFilters}
            aria-expanded={isFiltersOpen}
          >
            <LayoutGrid size={18} />
            {t('common.categories')}
          </button>
        </div>

        <div
          className={`${styles.overlay} ${isTagsDrawerOpen || isFiltersOpen ? styles.visible : ''}`}
          onClick={() => {
            setIsTagsDrawerOpen(false);
            setIsFiltersOpen(false);
          }}
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

        <CategorySidebar
          categories={categories}
          selectedCategory={selectedFilter}
          onCategorySelect={handleFilterClick}
          isOpen={isFiltersOpen}
          onToggle={toggleFilters}
        />

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
                <p>{t('common.scanning')}</p>
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
                <p>{t('common.noImagesFound')}</p>
                <p className={styles.noResultsHint}>
                  {t('common.noImagesHint')}
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
