import React from 'react';
import styles from './styles/components/Gallery.module.css';
import { galleryItems } from './data/galleryItems';

const Gallery = () => {
  return (
    <section className={styles.gallery}>
      {galleryItems.map((item, index) => (
        <div key={index} className={styles.galleryItem} style={{ backgroundImage: `url(${item.imageUrl})` }}>
          <div className={styles.overlay}>
            <h3 className={styles.title}>{item.title}</h3>
          </div>
        </div>
      ))}
    </section>
  );
};

export default Gallery; 