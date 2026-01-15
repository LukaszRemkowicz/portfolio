/**
 * Frontend configuration for feature toggles and visual constants.
 */
export const CONFIG = {
    /**
     * Toggle between randomized shooting star trajectories and fixed diagonal paths.
     * - true: Random angles and distances.
     * - false: Fixed -45 degree angle and 600px distance.
     */
    randomShootingStars: true,
    /**
     * Chance of a shooting star being a bolid (fireball).
     * 0.05 = 5% chance.
     */
    bolidChance: 1,
    /**
     * Minimum interval between bolids in seconds (e.g., 60 = 1 minute).
     */
    bolidMinInterval: 1,
    /**
     * Duration ranges (in seconds) for animations.
     * Lower values = faster speed.
     */
    starDurationRange: [1.0, 3.0] as [number, number],
    bolidDurationRange: [0.5, 1.5] as [number, number],
    /**
     * Width ranges (in pixels) for streaks.
     */
    starWidthRange: [100, 200] as [number, number],
    bolidWidthRange: [200, 400] as [number, number],
};
