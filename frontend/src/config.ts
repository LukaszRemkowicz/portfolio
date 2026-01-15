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
     * Duration ranges (in seconds) on screen.
     * Speed = PathDistance / Duration.
     * - Smaller duration + Larger distance = High speed.
     * - Larger duration + Smaller distance = Low speed.
     */
    starDurationRange: [2.0, 3.0] as [number, number],
    bolidDurationRange: [1.5, 1.5] as [number, number],
    /**
     * Path distance ranges (total travel) in pixels.
     * Horizontal displacement across the background.
     */
    starPathRange: [300, 500] as [number, number],
    bolidPathRange: [200, 500] as [number, number],
};
