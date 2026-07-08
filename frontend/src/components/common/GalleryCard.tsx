import { useState, memo, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import styles from '../../styles/components/GalleryCard.module.css';
import { MapPin } from 'lucide-react';
import { AstroImage } from '../../types';
import { stripHtml } from '../../utils/html';
import { useQueryClient } from '@tanstack/react-query';
import { fetchAstroImageDetail } from '../../api/services';
import ImageWithFallback from './ImageWithFallback';
import { buildResponsiveImageProps } from '../../utils/imageVariants';

interface GalleryCardProps {
  item: AstroImage;
  onClick: (image: AstroImage) => void;
  priority?: boolean;
}

const GALLERY_CARD_SIZES =
  '(max-width: 640px) 100vw, (max-width: 1024px) 50vw, (max-width: 1600px) 33vw, 25vw';

const GalleryCard = memo(
  ({ item, onClick, priority = false }: GalleryCardProps) => {
    const { t } = useTranslation();
    const [isLoaded, setIsLoaded] = useState(false);
    const [hasError, setHasError] = useState(!item.fallback_image?.url);
    const queryClient = useQueryClient();

    const isNew = (dateString?: string) => {
      if (!dateString) return false;
      const date = new Date(dateString);
      const now = new Date();
      const diffTime = Math.abs(now.getTime() - date.getTime());
      const diffDays = diffTime / (1000 * 60 * 60 * 24);
      return diffDays < 7;
    };

    const description = useMemo(() => {
      if (!item.description) return '';
      const plainDescription = stripHtml(item.description);
      return plainDescription.length > 80
        ? `${plainDescription.substring(0, 80)}...`
        : plainDescription;
    }, [item.description]);

    const responsiveImageProps = useMemo(
      () =>
        buildResponsiveImageProps({
          variants: item.variants,
          role: 'thumbnail',
          fallbackSrc: item.fallback_image?.url || '',
          preferredWidth: 560,
          sizes: GALLERY_CARD_SIZES,
        }),
      [item.fallback_image?.url, item.variants]
    );

    const handleMouseEnter = () => {
      queryClient.prefetchQuery({
        queryKey: ['astro-image', item.slug],
        queryFn: () => fetchAstroImageDetail(item.slug),
        staleTime: 5 * 60 * 1000,
      });
    };

    return (
      <button
        className={styles.card}
        onClick={() => onClick(item)}
        onMouseEnter={handleMouseEnter}
        onFocus={handleMouseEnter}
        aria-label={`View details for ${item.name}`}
        type='button'
        data-testid={`gallery-card-${item.slug}`}
      >
        {isNew(item.created_at) && <div className={styles.newBadge}>NEW!</div>}
        <div className={styles.imageWrapper} aria-hidden='true'>
          <div
            className={`${styles.placeholder} ${isLoaded ? styles.hide : ''}`}
          />
          <ImageWithFallback
            {...responsiveImageProps}
            alt=''
            loading={priority ? 'eager' : 'lazy'}
            decoding='async'
            onLoad={() => setIsLoaded(true)}
            onError={() => setHasError(true)}
            className={`${styles.cardImage} ${isLoaded || hasError ? styles.show : ''}`}
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            {...(priority ? ({ fetchpriority: 'high' } as any) : {})}
            draggable='false'
            onContextMenu={e => e.preventDefault()}
          />
          {hasError && (
            <div className={styles.placeholderOverlay}>
              <span className={styles.placeholderText}>[Placeholder]</span>
            </div>
          )}
        </div>
        <div className={styles.cardContent}>
          <span className={styles.category}>
            {t(`categories.${item.celestial_object}`)}
          </span>
          <h3 className={styles.cardTitle}>{item.name}</h3>
          <p className={styles.cardLocation}>
            <MapPin size={12} className={styles.metaIcon} />
            {item.place?.name || item.place?.country}
          </p>
          <p className={styles.cardDescription}>{description}</p>
          <div className={styles.divider} aria-hidden='true'></div>
        </div>
      </button>
    );
  }
);

GalleryCard.displayName = 'GalleryCard';

export default GalleryCard;
