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
    width: number;
    opacity: number;
    isBolid?: boolean;
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
    const [lastBolidTime, setLastBolidTime] = useState<number>(0);

    useEffect(() => {
        let timeoutId: NodeJS.Timeout;

        const createShootingStar = () => {
            const now = Date.now();
            const id = now;
            const left = `${Math.random() * window.innerWidth}px`;
            const top = `${Math.random() * window.innerHeight}px`;
            // Bolid logic
            const timeSinceLastBolid = now - lastBolidTime;
            const canSpawnBolid = timeSinceLastBolid >= CONFIG.bolidMinInterval * 1000;
            const isBolid = canSpawnBolid && Math.random() < CONFIG.bolidChance;

            if (isBolid) {
                setLastBolidTime(now);
            }

            // Duration (speed) randomization
            const [minDur, maxDur] = isBolid ? CONFIG.bolidDurationRange : CONFIG.starDurationRange;
            const duration = Math.random() * (maxDur - minDur) + minDur;

            // Streak length (visual thickness) randomization
            const [minStreak, maxStreak] = isBolid ? CONFIG.bolidStreakRange : CONFIG.starStreakRange;
            const width = Math.random() * (maxStreak - minStreak) + minStreak;

            // Opacity (lightness) randomization
            const [minOp, maxOp] = isBolid ? CONFIG.bolidOpacityRange : CONFIG.starOpacityRange;
            const opacity = Math.random() * (maxOp - minOp) + minOp;

            // Use fixed trajectory if random is false
            const angle = random ? Math.random() * 360 : -45;

            // Path distance (length of travel) randomization
            const [p1, p2] = isBolid ? CONFIG.bolidPathRange : CONFIG.starPathRange;
            const minPath = Math.min(p1, p2);
            const maxPath = Math.max(p1, p2);
            const distance = random ? Math.random() * (maxPath - minPath) + minPath : 600;

            const newStar = { id, left, top, duration, angle, distance, width, opacity, isBolid };
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
    }, [minDelay, maxDelay, initialDelay, random, lastBolidTime]);

    return (
        <div className={`${styles.starContainer} ${className}`}>
            {shootingStars.map((star) => (
                <div
                    key={star.id}
                    className={`${styles.shootingStar} ${star.isBolid ? styles.bolid : ""}`}
                    style={
                        {
                            left: star.left,
                            top: star.top,
                            animation: `${styles.fall} ${star.duration}s linear forwards`,
                            "--angle": `${star.angle}deg`,
                            "--distance": `${star.distance}px`,
                            "--width": `${star.width}px`,
                            "--opacity": star.opacity,
                        } as React.CSSProperties
                    }
                >
                    {star.isBolid && (
                        <div
                            className={styles.bolidFlash}
                            style={{
                                animation: `${styles.explode} ${star.duration * 0.4}s ease-out forwards`,
                                animationDelay: `${star.duration * 0.6}s`,
                            }}
                        />
                    )}
                </div>
            ))}
        </div>
    );
};

export default ShootingStars;
