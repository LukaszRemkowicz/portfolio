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
