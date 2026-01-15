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
};
