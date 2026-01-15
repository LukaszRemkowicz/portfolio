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
   * Master switch to enable/disable shooting stars animation.
   * Controlled via ENABLE_SHOOTING_STARS env var (default: true).
   */
  enableShootingStars: process.env.ENABLE_SHOOTING_STARS !== "false",
  /**
   * Chance of a shooting star being a bolid (fireball).
   * 0.05 = 5% chance.
   */
  bolidChance: 0.1,
  /**
   * Minimum interval between bolids in seconds (e.g., 60 = 1 minute).
   */
  bolidMinInterval: 60,
  /**
   * Duration ranges (in seconds) on screen.
   * Speed = PathDistance / Duration.
   * - Smaller duration + Larger distance = High speed.
   * - Larger duration + Smaller distance = Low speed.
   */
  starDurationRange: [0.4, 1.2] as [number, number],
  bolidDurationRange: [0.4, 0.9] as [number, number],
  /**
   * Path distance ranges (total travel) in pixels.
   * Horizontal displacement across the background.
   */
  starPathRange: [50, 500] as [number, number],
  bolidPathRange: [50, 500] as [number, number],
  /**
   * Streak length (visual trail size) ranges in pixels.
   */
  starStreakRange: [100, 200] as [number, number],
  bolidStreakRange: [20, 100] as [number, number],
  /**
   * Opacity (brightness) ranges.
   * 0.0 = transparent, 1.0 = fully opaque.
   */
  starOpacityRange: [0.4, 0.8] as [number, number],
  bolidOpacityRange: [0.7, 1.0] as [number, number],
  /**
   * Smoke opacity range.
   */
  smokeOpacityRange: [0.5, 0.8] as [number, number],
};
