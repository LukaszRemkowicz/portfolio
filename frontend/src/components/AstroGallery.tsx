import React, { useState, useEffect, useRef, useMemo } from 'react';
import {
  useSearchParams,
  useParams,
  useNavigate,
  useLocation,
  Navigate,
} from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import styles from '../styles/components/AstroGallery.module.css';
import { ASSETS } from '../api/routes';
import { AstroImage, FilterType } from '../types';
import ImageModal from './common/ImageModal';
import LoadingScreen from './common/LoadingScreen';
import GalleryCard from './common/GalleryCard';
import GallerySkeleton from './skeletons/GallerySkeleton';
import TagSidebar from './TagSidebar';
import CategorySidebar from './CategorySidebar';
import { Sliders, LayoutGrid } from 'lucide-react';
import SEO from './common/SEO';
import { useAstroImages } from '../hooks/useAstroImages';
import { useTags } from '../hooks/useTags';
import { APP_ROUTES } from '../api/constants';
import { useCategories } from '../hooks/useCategories';
import { useBackground } from '../hooks/useBackground';
import { useImageUrls } from '../hooks/useImageUrls';

const AstroGallery: React.FC = () => {
  const [searchParams] = useSearchParams();
  const { slug: imgSlug } = useParams<{ slug?: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const [isTagsDrawerOpen, setIsTagsDrawerOpen] = useState(false);
  const [isFiltersOpen, setIsFiltersOpen] = useState(false);
  const resultsRef = useRef<HTMLDivElement>(null);

  const selectedFilter = searchParams.get('filter') as FilterType | null;
  const selectedTag = searchParams.get('tag');

  const { t } = useTranslation();

  const { data: background } = useBackground();
  const { data: categories = [] } = useCategories();
  const { data: tags = [] } = useTags(selectedFilter || undefined);

  const params = useMemo(
    () => ({
      ...(selectedFilter ? { filter: selectedFilter } : {}),
      ...(selectedTag ? { tag: selectedTag } : {}),
    }),
    [selectedFilter, selectedTag]
  );

  const {
    data: images = [],
    isLoading: isImagesLoading,
    error: queryError,
  } = useAstroImages(params);

  // Pre-fetch all signed urls
  useImageUrls();

  const error = queryError ? 'Failed to fetch gallery images.' : null;
  const isInitialLoading = isImagesLoading && images.length === 0 && !error;

  const modalImage = useMemo(() => {
    if (!imgSlug) return null;
    return (
      images.find(i => i.slug === imgSlug || String(i.pk) === imgSlug) || null
    );
  }, [imgSlug, images]);
  // Smooth scroll to results on filter/tag change (Mobile only)
  useEffect(() => {
    if (window.innerWidth <= 992 && resultsRef.current) {
      requestAnimationFrame(() => {
        if (!resultsRef.current) return;
        const yOffset = -100; // Offset for sticky navbar/header
        const element = resultsRef.current;
        const y =
          element.getBoundingClientRect().top + window.pageYOffset + yOffset;
        window.scrollTo({ top: y, behavior: 'smooth' });
      });
    }
  }, [selectedFilter, selectedTag]);

  // Redirect if URL refers to a non-existent image slug
  if (!isImagesLoading && imgSlug && !modalImage && images.length > 0) {
    return <Navigate to={APP_ROUTES.ASTROPHOTOGRAPHY} replace />;
  }

  const handleFilterClick = (filter: FilterType): void => {
    // Build clean params from known state — never copy from searchParams
    // to avoid leaking stale params (e.g. ?img=) into the URL.
    const nextParams = new URLSearchParams();
    if (selectedFilter === filter) {
      // deselect — drop filter entirely
    } else {
      nextParams.set('filter', filter);
      setIsFiltersOpen(false);
    }
    // Keep active tag unless it was cleared
    if (selectedTag && selectedFilter !== filter)
      nextParams.set('tag', selectedTag);
    const qs = nextParams.toString() ? `?${nextParams.toString()}` : '';
    navigate(`/astrophotography${qs}`);
  };

  const handleTagSelect = (tagSlug: string | null): void => {
    // Same: build fresh params, never inherit from searchParams.
    const nextParams = new URLSearchParams();
    if (tagSlug) nextParams.set('tag', tagSlug);
    if (selectedFilter) nextParams.set('filter', selectedFilter);
    const qs = nextParams.toString() ? `?${nextParams.toString()}` : '';
    navigate(`/astrophotography${qs}`);
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
    // Build clean params from known state — only filter and tag.
    const nextParams = new URLSearchParams();
    if (selectedFilter) nextParams.set('filter', selectedFilter);
    if (selectedTag) nextParams.set('tag', selectedTag);
    const qs = nextParams.toString() ? `?${nextParams.toString()}` : '';
    navigate(`/astrophotography/${image.slug}${qs}`);
  };

  const closeModal = (): void => {
    const backgroundLocation = location.state?.backgroundLocation as
      | { pathname?: string; search?: string; hash?: string }
      | undefined;

    if (backgroundLocation?.pathname) {
      navigate(
        `${backgroundLocation.pathname}${backgroundLocation.search || ''}${backgroundLocation.hash || ''}`,
        { replace: true }
      );
      return;
    }

    // Build clean params from known state — only filter and tag.
    const nextParams = new URLSearchParams();
    if (selectedFilter) nextParams.set('filter', selectedFilter);
    if (selectedTag) nextParams.set('tag', selectedTag);
    const qs = nextParams.toString() ? `?${nextParams.toString()}` : '';
    navigate(`/astrophotography${qs}`);
  };

  if (isInitialLoading) return <LoadingScreen />;
  if (error) return <div className={styles.error}>{error}</div>;

  return (
    <div className={styles.container}>
      <SEO title={t('common.gallery')} />
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
              <GallerySkeleton count={9} />
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
