import { useState, memo, useMemo } from 'react';
import styles from '../../styles/components/GalleryCard.module.css';
import { MapPin } from 'lucide-react';
import { AstroImage } from '../../types';
import { stripHtml } from '../../utils/html';

interface GalleryCardProps {
  item: AstroImage;
  onClick: (image: AstroImage) => void;
}

const GalleryCard = memo(({ item, onClick }: GalleryCardProps) => {
  const [isLoaded, setIsLoaded] = useState(false);

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

  return (
    <button
      className={styles.card}
      onClick={() => onClick(item)}
      aria-label={`View details for ${item.name}`}
      type='button'
    >
      {isNew(item.created_at) && <div className={styles.newBadge}>NEW</div>}
      <div className={styles.imageWrapper} aria-hidden='true'>
        <div
          className={`${styles.placeholder} ${isLoaded ? styles.hide : ''}`}
        />
        <img
          src={item.thumbnail_url || item.url}
          alt=''
          loading='lazy'
          onLoad={() => setIsLoaded(true)}
          className={`${styles.cardImage} ${isLoaded ? styles.show : ''}`}
        />
      </div>
      <div className={styles.cardContent}>
        <span className={styles.category}>{item.celestial_object}</span>
        <h3 className={styles.cardTitle}>{item.name}</h3>
        <p className={styles.cardLocation}>
          <MapPin size={12} className={styles.metaIcon} />
          {item.location}
        </p>
        <p className={styles.cardDescription}>{description}</p>
        <div className={styles.divider} aria-hidden='true'></div>
      </div>
    </button>
  );
});

GalleryCard.displayName = 'GalleryCard';

export default GalleryCard;
