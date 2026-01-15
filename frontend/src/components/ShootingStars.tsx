import React, { useState, useEffect } from "react";
import styles from "../styles/components/ShootingStars.module.css";
import { CONFIG } from "../config";

interface ShootingStar {
    id: number;
    left: string;
    top: string;
    duration: number;
    angle: number;
    distance: number;
}

interface ShootingStarsProps {
    minDelay?: number;
    maxDelay?: number;
    initialDelay?: number;
    className?: string;
    random?: boolean;
}

const ShootingStars: React.FC<ShootingStarsProps> = ({
    minDelay = 4000,
    maxDelay = 12000,
    initialDelay = 5000,
    className = "",
    random = CONFIG.randomShootingStars,
}) => {
    const [shootingStars, setShootingStars] = useState<ShootingStar[]>([]);

    useEffect(() => {
        let timeoutId: NodeJS.Timeout;

        const createShootingStar = () => {
            const id = Date.now();
            const left = `${Math.random() * (window.innerWidth + 300)}px`;
            const top = `${Math.random() * (window.innerHeight / 2)}px`;
            const duration = Math.random() * 1.5 + 1;

            // Use fixed trajectory if random is false
            const angle = random ? Math.random() * 90 - 45 : -45;
            const distance = random ? Math.random() * 400 + 400 : 600;

            const newStar = { id, left, top, duration, angle, distance };
            setShootingStars((prev) => [...prev, newStar]);

            // Remove the star after its animation completes
            setTimeout(() => {
                setShootingStars((prev) => prev.filter((star) => star.id !== id));
            }, duration * 1000);

            // Schedule next star
            const nextDelay = Math.random() * (maxDelay - minDelay) + minDelay;
            timeoutId = setTimeout(createShootingStar, nextDelay);
        };

        timeoutId = setTimeout(createShootingStar, initialDelay);

        return () => clearTimeout(timeoutId);
    }, [minDelay, maxDelay, initialDelay, random]);

    return (
        <div className={`${styles.starContainer} ${className}`}>
            {shootingStars.map((star) => (
                <div
                    key={star.id}
                    className={styles.shootingStar}
                    style={
                        {
                            left: star.left,
                            top: star.top,
                            animation: `${styles.fall} ${star.duration}s linear forwards`,
                            "--angle": `${star.angle}deg`,
                            "--distance": `${star.distance}px`,
                        } as React.CSSProperties
                    }
                />
            ))}
        </div>
    );
};

export default ShootingStars;
