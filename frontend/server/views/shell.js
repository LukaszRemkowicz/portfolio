/**
 * Server-side view helpers for shared shell data.
 *
 * These helpers define which shell resources are cached by the frontend SSR
 * layer and provide a small loader wrapper that applies the shared cache policy
 * consistently across SSR routes.
 */

import { getCachedShellData } from '../ssrCache.js';

export const SHELL_RESOURCES = {
  background: {
    resource: 'background',
    tags: ['background'],
  },
  latestAstroImages: {
    resource: 'latest-astro-images',
    tags: ['latest-astro-images'],
  },
  profile: {
    resource: 'profile',
    tags: ['profile'],
  },
  settings: {
    resource: 'settings',
    tags: ['settings'],
  },
  travelHighlights: {
    resource: 'travel-highlights',
    tags: ['travel-highlights'],
  },
};

/**
 * Build a cache-aware loader for shared shell resources.
 *
 * The returned function accepts a shell resource descriptor plus a loader
 * function. It applies the standard SSR shell cache keying strategy based on
 * resource name, language, and request origin.
 */
export function getCachedShellLoader(language, requestOrigin) {
  return async (resourceConfig, loader) =>
    getCachedShellData({
      resource: resourceConfig.resource,
      language,
      requestOrigin,
      tags: resourceConfig.tags,
      loader,
    });
}
