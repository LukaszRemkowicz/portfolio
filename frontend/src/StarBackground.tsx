import React, { useEffect, useState } from "react";
import styles from "./styles/components/StarBackground.module.css";

interface Star {
  id: number;
  size: number;
  left: string;
  top: string;
  duration: string;
}

const StarBackground: React.FC = () => {
  const [stars, setStars] = useState<Star[]>([]);

  useEffect(() => {
    const starCount = 200;
    const newStars: Star[] = [];
    for (let i = 0; i < starCount; i++) {
      newStars.push({
        id: i,
        size: Math.random() * 2 + 1,
        left: `${Math.random() * 100}%`,
        top: `${Math.random() * 100}%`,
        duration: `${Math.random() * 3 + 2}s`,
      });
    }
    setStars(newStars);
  }, []);

  return (
    <div className={styles.container}>
      {stars.map((star) => (
        <div
          key={star.id}
          className={styles.star}
          style={
            {
              width: `${star.size}px`,
              height: `${star.size}px`,
              left: star.left,
              top: star.top,
              "--duration": star.duration,
            } as React.CSSProperties
          }
        />
      ))}
    </div>
  );
};

export default StarBackground;
