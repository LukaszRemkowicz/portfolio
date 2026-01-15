import React, { useState, useEffect } from "react";
import styles from "../styles/components/ShootingStars.module.css";
import { CONFIG } from "../config";

interface DustParticle {
    id: number;
    offsetX: number;
    offsetY: number;
    size: number;
    blur: number;
    driftX: number;
    driftY: number;
    duration: number;
    delay: number;
}

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
    dustParticles?: DustParticle[];
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

            // Generate smoke segments for bolids (the "Burn")
            const dustParticles: DustParticle[] = [];
            if (isBolid) {
                const particleCount = 4 + Math.floor(Math.random() * 3); // 4-6 larger blobs
                for (let i = 0; i < particleCount; i++) {
                    dustParticles.push({
                        id: Math.random(),
                        // Wider offsets for irregular cloud shape
                        offsetX: (Math.random() - 0.5) * 30,
                        offsetY: (Math.random() - 0.5) * 30,
                        // Significantly larger blobs
                        size: 30 + Math.random() * 40,
                        blur: 8 + Math.random() * 8, // More blur for smoky look
                        driftX: (Math.random() - 0.5) * 60,
                        driftY: (Math.random() - 0.5) * 60,
                        duration: 1.5 + Math.random() * 2.0, // Longer lingering smoke
                        delay: duration * 0.6 + (Math.random() - 0.5) * 0.1, // Near flash point
                    });
                }
            }

            const newStar = { id, left, top, duration, angle, distance, width, opacity, isBolid, dustParticles };
            setShootingStars((prev) => [...prev, newStar]);

            // Calculate when to remove the star from state
            // Bolids need to hang around longer for their dust to finish
            let totalLifetime = duration * 1000;
            if (isBolid && dustParticles.length > 0) {
                const maxDustTime = Math.max(...dustParticles.map(p => p.delay + p.duration));
                totalLifetime = Math.max(totalLifetime, maxDustTime * 1000);
            }

            // Remove the star after its animation (and dust) completes
            setTimeout(() => {
                setShootingStars((prev) => prev.filter((star) => star.id !== id));
            }, totalLifetime + 100); // Add small buffer

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
                            animation: `${styles.move} ${star.duration}s linear forwards`,
                            "--angle": `${star.angle}deg`,
                            "--distance": `${star.distance}px`,
                            "--width": `${star.width}px`,
                        } as React.CSSProperties
                    }
                >
                    <div
                        className={styles.streak}
                        style={
                            {
                                animation: `${styles.streakFade} ${star.duration}s linear forwards`,
                                "--opacity": star.opacity,
                            } as React.CSSProperties
                        }
                    />
                    {star.isBolid && (
                        <>
                            <div
                                className={styles.bolidFlash}
                                style={{
                                    animation: `${styles.explode} ${star.duration * 0.4}s ease-out forwards`,
                                    animationDelay: `${star.duration * 0.6}s`,
                                }}
                            />
                            {star.dustParticles?.map((particle) => (
                                <div
                                    key={particle.id}
                                    className={styles.bolidDust}
                                    style={{
                                        "--p-size": `${particle.size}px`,
                                        "--p-blur": `${particle.blur}px`,
                                        "--p-x": `${particle.offsetX}px`,
                                        "--p-y": `${particle.offsetY}px`,
                                        "--p-drift-x": `${particle.driftX}px`,
                                        "--p-drift-y": `${particle.driftY}px`,
                                        animation: `${styles.driftAndFade} ${particle.duration}s ease-out forwards`,
                                        animationDelay: `${particle.delay}s`,
                                    } as React.CSSProperties}
                                />
                            ))}
                        </>
                    )}
                </div>
            ))}
        </div>
    );
};

export default ShootingStars;
