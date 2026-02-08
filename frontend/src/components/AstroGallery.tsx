import React, { useState, useEffect, useRef, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useQueryClient } from '@tanstack/react-query';
import styles from '../styles/components/AstroGallery.module.css';
import { ASSETS } from '../api/routes';
import { AstroImage, FilterType } from '../types';
import GalleryCard from './common/GalleryCard';
import ImageModal from './common/ImageModal';
import LoadingScreen from './common/LoadingScreen';
import SEO from './common/SEO';
import TagSidebar from './TagSidebar';
import CategorySidebar from './CategorySidebar';
import { LayoutGrid, Sliders } from 'lucide-react';
import { useAstroImages } from '../hooks/useAstroImages';
import GallerySkeleton from './skeletons/GallerySkeleton';
import { useBackground } from '../hooks/useBackground';
import { useCategories } from '../hooks/useCategories';
import { useTags } from '../hooks/useTags';
import { useProfile } from '../hooks/useProfile';
import { useSettings } from '../hooks/useSettings';
import { fetchAstroImageDetail } from '../api/services';

const AstroGallery: React.FC = () => {
  // Local state
  const [searchParams, setSearchParams] = useSearchParams();
  const [isTagsDrawerOpen, setIsTagsDrawerOpen] = useState(false);
  const [isFiltersOpen, setIsFiltersOpen] = useState(false);
  const resultsRef = useRef<HTMLDivElement>(null);

  const selectedFilter = searchParams.get('filter') as FilterType | null;
  const selectedTag = searchParams.get('tag');
  const imgParam = searchParams.get('img');

  const { t, i18n } = useTranslation();

  // Data Fetching (TanStack Query)
  const { data: background } = useBackground();
  const { data: categories = [] } = useCategories();
  const { data: tags = [] } = useTags(selectedFilter || undefined);
  const { isLoading: isProfileLoading } = useProfile();
  const { isLoading: isSettingsLoading } = useSettings();

  const isInitialLoading = isProfileLoading || isSettingsLoading;

  const {
    data: images = [],
    isLoading: isImagesLoading,
    error: queryError,
  } = useAstroImages({
    filter: selectedFilter,
    tag: selectedTag,
  });

  const modalImage = useMemo(() => {
    if (!imgParam) return null;
    return (
      images.find(i => i.slug === imgParam || i.pk.toString() === imgParam) ||
      null
    );
  }, [imgParam, images]);

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

  const queryClient = useQueryClient();

  const handlePrefetch = (slug: string) => {
    queryClient.prefetchQuery({
      queryKey: ['astroImageDetail', slug, i18n.language],
      queryFn: () => fetchAstroImageDetail(slug),
      staleTime: 1000 * 60 * 60, // 1 hour
    });
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
  if (queryError)
    return (
      <div className={styles.error}>
        {queryError.message || t('common.error')}
      </div>
    );

  return (
    <div className={styles.container}>
      <SEO
        title={t('common.gallery')}
        description={t('common.gallerySubtitle')}
      />
      {modalImage && (
        <SEO
          title={modalImage.name}
          description={modalImage.description || modalImage.name}
          image={modalImage.url}
          type='article'
        />
      )}
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
                {t(`categories.${filter}`)}
              </button>
            );
          })}
        </div>

        <div className={styles.gridSection}>
          <div ref={resultsRef} className={styles.scrollAnchor} />
          <div className={styles.grid}>
            {isImagesLoading ? (
              <>
                {[...Array(6)].map((_, i) => (
                  <GallerySkeleton key={i} />
                ))}
              </>
            ) : images.length > 0 ? (
              images.map((image: AstroImage) => (
                <GalleryCard
                  key={image.pk}
                  item={image}
                  onClick={handleImageClick}
                  onMouseEnter={() => handlePrefetch(image.slug)}
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
