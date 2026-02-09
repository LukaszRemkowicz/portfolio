declare global {
  interface Window {
    _ENV_?: {
      GA_TRACKING_ID?: string;
    };
  }
}

/**
 * Safely access environment variables defined by Webpack's DefinePlugin
 * or injected at runtime via window._ENV_.
 */
export const getEnv = (key: string, fallback: string = ''): string => {
  // 1. Check runtime configuration (Site Domain, Tracking ID, etc.)
  if (typeof window !== 'undefined' && window._ENV_) {
    const runtimeVal = (window._ENV_ as Record<string, string | undefined>)[
      key
    ];
    if (runtimeVal && runtimeVal !== `__${key}__`) {
      return runtimeVal;
    }
  }

  try {
    // 2. Check build-time DefinePlugin configuration
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
    return fallback;
  }
};
