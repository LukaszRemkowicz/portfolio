// frontend/src/utils/env.ts

/**
 * Safely access environment variables defined by Webpack's DefinePlugin.
 * Prevents "ReferenceError: process is not defined" in the browser.
 */
export const getEnv = (key: string, fallback: string = ''): string => {
  try {
    // In Webpack 5, process.env is often replaced literally.
    // However, if it's not replaced, we need to handle the ReferenceError.

    // We use a switch with literal paths so DefinePlugin can easily find and replace them.
    switch (key) {
      case 'API_URL':
        return process.env.API_URL || fallback;
      case 'GA_TRACKING_ID':
        return process.env.GA_TRACKING_ID || fallback;
      case 'ENABLE_GA':
        return process.env.ENABLE_GA || fallback;
      case 'NODE_ENV':
        return process.env.NODE_ENV || fallback;
      default:
        return fallback;
    }
  } catch {
    // If process is not defined, we'll hit this block
    return fallback;
  }
};
