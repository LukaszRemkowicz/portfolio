import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import styles from "./styles/components/Gallery.module.css";
import { galleryItems } from "./data/galleryItems";
import { GalleryItem } from "./types";
import { fetchEnabledFeatures } from "./api/services";

const Gallery: React.FC = () => {
  const [isProgrammingEnabled, setIsProgrammingEnabled] =
    useState<boolean>(false);

  useEffect(() => {
    const checkEnablement = async () => {
      try {
        const features = await fetchEnabledFeatures();
        setIsProgrammingEnabled(features.programming === true);
      } catch (error) {
        console.error(
          "Failed to check programming enablement in Gallery:",
          error,
        );
        setIsProgrammingEnabled(false);
      }
    };
    checkEnablement();
  }, []);
  const renderGalleryItem = (
    item: GalleryItem,
    index: number,
  ): React.ReactNode => {
    const content = (
      <div
        className={styles.galleryItem}
        style={{ backgroundImage: `url(${item.imageUrl})` }}
      >
        <div className={styles.overlay}>
          <h3 className={styles.title}>{item.title}</h3>
        </div>
      </div>
    );

    // Make Astrophotography clickable
    if (item.title.includes("ASTROPHOTOGRAPHY")) {
      return (
        <Link key={index} to="/astrophotography" className={styles.galleryLink}>
          {content}
        </Link>
      );
    }

    // Make Programming clickable
    if (item.title.includes("PROGRAMMING")) {
      return (
        <Link key={index} to="/programming" className={styles.galleryLink}>
          {content}
        </Link>
      );
    }

    return <div key={index}>{content}</div>;
  };

  const filteredItems = galleryItems.filter((item) => {
    if (item.title.includes("PROGRAMMING")) {
      return isProgrammingEnabled;
    }
    return true;
  });

  return (
    <section className={styles.gallery}>
      {filteredItems.map((item: GalleryItem, index: number) =>
        renderGalleryItem(item, index),
      )}
    </section>
  );
};

export default Gallery;
