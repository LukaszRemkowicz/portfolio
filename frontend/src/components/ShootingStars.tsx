// frontend/src/components/ShootingStars.tsx
import {
  useState,
  useEffect,
  memo,
  useRef,
  useCallback,
  type FC,
  type CSSProperties,
} from 'react';
import styles from '../styles/components/ShootingStars.module.css';
import { useSettings } from '../hooks/useSettings';
import { MeteorConfig } from '../types';

const DEFAULT_METEOR_CONFIG: MeteorConfig = {
  randomShootingStars: true,
  bolidChance: 0.1,
  bolidMinInterval: 60,
  starDurationRange: [0.4, 1.2],
  bolidDurationRange: [0.4, 0.9],
  starPathRange: [50, 500],
  bolidPathRange: [50, 500],
  starStreakRange: [100, 200],
  bolidStreakRange: [20, 100],
  starOpacityRange: [0.4, 0.8],
  bolidOpacityRange: [0.7, 1.0],
  smokeOpacityRange: [0.5, 0.8],
};

interface DustParticle {
  id: number;
  offsetX: number;
  offsetY: number;
  size: number;
  blur: number;
  rotate: string;
  skew: string;
  opacity: number;
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

const MemoizedStar = memo(({ star }: { star: ShootingStar }) => (
  <div
    className={`${styles.shootingStar} ${star.isBolid ? styles.bolid : ''}`}
    style={
      {
        left: star.left,
        top: star.top,
        animation: `${styles.move} ${star.duration}s linear forwards`,
        '--angle': `${star.angle}deg`,
        '--distance': `${star.distance}px`,
        '--width': `${star.width}px`,
      } as CSSProperties
    }
  >
    <div
      className={styles.streak}
      style={
        {
          animation: `${styles.streakFade} ${star.duration}s linear forwards`,
          '--opacity': star.opacity,
        } as CSSProperties
      }
    />
    {star.isBolid && (
      <>
        <div
          className={styles.bolidFlash}
          style={{
            animation: `${styles.explode} ${
              star.duration * 0.4
            }s ease-out forwards`,
            animationDelay: `${star.duration * 0.6}s`,
          }}
        />
        {star.dustParticles?.map(particle => (
          <div
            key={particle.id}
            className={styles.bolidDust}
            style={
              {
                '--p-size': `${particle.size}px`,
                '--p-blur': `${particle.blur}px`,
                '--p-opacity': particle.opacity,
                '--p-rotate': particle.rotate,
                '--p-skew': particle.skew,
                '--p-x': `${particle.offsetX}px`,
                '--p-y': `${particle.offsetY}px`,
                '--p-drift-x': `${particle.driftX}px`,
                '--p-drift-y': `${particle.driftY}px`,
                animation: `${styles.driftAndFade} ${particle.duration}s ease-out forwards`,
                animationDelay: `${particle.delay}s`,
              } as CSSProperties
            }
          />
        ))}
      </>
    )}
  </div>
));

MemoizedStar.displayName = 'MemoizedStar';

const ShootingStars: FC<ShootingStarsProps> = ({
  minDelay = 4000,
  maxDelay = 12000,
  initialDelay = 5000,
  className = '',
  random: randomProp,
}) => {
  const { data: settings } = useSettings();
  const features = settings;
  const dynamicConfig = settings?.meteors || null;
  const [shootingStars, setShootingStars] = useState<ShootingStar[]>([]);
  const lastBolidTimeRef = useRef<number>(0);

  // Helper to get value from dynamic config with fallback
  const getVal = useCallback(
    <K extends keyof MeteorConfig>(key: K): MeteorConfig[K] => {
      if (dynamicConfig && dynamicConfig[key] !== undefined) {
        return dynamicConfig[key];
      }
      return DEFAULT_METEOR_CONFIG[key];
    },
    [dynamicConfig]
  );

  useEffect(() => {
    if (!features?.meteors) return;

    let timeoutId: ReturnType<typeof setTimeout>;

    const createShootingStar = () => {
      const now = Date.now();
      const id = now;
      const left = `${Math.random() * window.innerWidth}px`;
      const top = `${Math.random() * window.innerHeight}px`;
      // Bolid logic
      const timeSinceLastBolid = now - lastBolidTimeRef.current;
      const bolidMinInterval = getVal('bolidMinInterval');
      const bolidChance = getVal('bolidChance');

      const canSpawnBolid = timeSinceLastBolid >= bolidMinInterval * 1000;
      const isBolid = canSpawnBolid && Math.random() < bolidChance;

      if (isBolid) {
        lastBolidTimeRef.current = now;
      }

      // Duration (speed) randomization
      const durationRange = isBolid
        ? getVal('bolidDurationRange')
        : getVal('starDurationRange');
      const duration =
        Math.random() * (durationRange[1] - durationRange[0]) +
        durationRange[0];

      // Streak length (visual thickness) randomization
      const streakRange = isBolid
        ? getVal('bolidStreakRange')
        : getVal('starStreakRange');
      const width =
        Math.random() * (streakRange[1] - streakRange[0]) + streakRange[0];

      // Opacity (lightness) randomization
      const opacityRange = isBolid
        ? getVal('bolidOpacityRange')
        : getVal('starOpacityRange');
      const opacity =
        Math.random() * (opacityRange[1] - opacityRange[0]) + opacityRange[0];

      // Use fixed trajectory if random is false
      const randomStars = randomProp ?? getVal('randomShootingStars');
      const angle = randomStars ? Math.random() * 360 : -45;

      // Path distance (length of travel) randomization
      const pathRange = isBolid
        ? getVal('bolidPathRange')
        : getVal('starPathRange');

      const minPath = Math.min(pathRange[0], pathRange[1]);
      const maxPath = Math.max(pathRange[0], pathRange[1]);
      const distance = randomStars
        ? Math.random() * (maxPath - minPath) + minPath
        : 600;

      // Generate smoke segments for bolids (Zig-Zag "Burn" - Line style)
      const dustParticles: DustParticle[] = [];
      if (isBolid) {
        const segmentCount = 20 + Math.floor(Math.random() * 10); // 20-30 pieces for continuous look
        const smokeOpacityRange = getVal('smokeOpacityRange');
        for (let i = 0; i < segmentCount; i++) {
          // Spread pieces along the flight path (roughly 30% to 90% of duration)
          const progress = 0.3 + (i / segmentCount) * 0.6;

          dustParticles.push({
            id: Math.random(),
            offsetX: (Math.random() - 0.5) * 2,
            offsetY: (Math.random() - 0.5) * 2,
            size: 40 + Math.random() * 40,
            blur: 1,
            rotate: `${(Math.random() - 0.5) * 10}deg`,
            skew: `0deg`,
            opacity:
              Math.random() * (smokeOpacityRange[1] - smokeOpacityRange[0]) +
              smokeOpacityRange[0],
            driftX: (Math.random() - 0.5) * 20,
            driftY: (Math.random() - 0.5) * 20,
            duration: 2.0 + Math.random() * 1.5,
            delay: duration + duration * progress,
          });
        }
      }

      const newStar = {
        id,
        left,
        top,
        duration,
        angle,
        distance,
        width,
        opacity,
        isBolid,
        dustParticles,
      };
      setShootingStars(prev => [...prev, newStar]);

      // Calculate when to remove the star from state
      let totalLifetime = duration * 1000;
      if (isBolid && dustParticles.length > 0) {
        const maxDustTime = Math.max(
          ...dustParticles.map(p => p.delay + p.duration)
        );
        totalLifetime = Math.max(totalLifetime, maxDustTime * 1000);
      }

      setTimeout(() => {
        setShootingStars(prev => prev.filter(star => star.id !== id));
      }, totalLifetime + 100);

      // Schedule next star
      const nextDelay = Math.random() * (maxDelay - minDelay) + minDelay;
      timeoutId = setTimeout(createShootingStar, nextDelay);
    };

    timeoutId = setTimeout(createShootingStar, initialDelay);

    return () => clearTimeout(timeoutId);
  }, [
    minDelay,
    maxDelay,
    initialDelay,
    randomProp,
    features?.meteors,
    dynamicConfig,
    getVal,
  ]);

  if (!features?.meteors) return null;

  return (
    <div className={`${styles.starContainer} ${className}`}>
      {shootingStars.map(star => (
        <MemoizedStar key={star.id} star={star} />
      ))}
    </div>
  );
};

export default ShootingStars;
