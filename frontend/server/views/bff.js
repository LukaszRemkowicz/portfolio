/**
 * Frontend-owned transport routes for browser-side JSON flows.
 *
 * This module is the server-side source of truth for mapping FE transport
 * endpoints to their backend counterparts. It keeps route resolution out of the
 * raw HTTP server so SSR/BFF behavior stays easier to reason about and test.
 */

export const BFF_ROUTES = {
  contact: '/app/contact',
  images: '/app/images/',
  imageFiles: '/app/image-files/',
  profile: '/app/profile/',
  background: '/app/background/',
  astroImages: '/app/astroimages/',
  shop: '/app/shop/',
  settings: '/app/settings/',
  travelHighlights: '/app/travel-highlights/',
  tags: '/app/tags/',
  categories: '/app/categories/',
  travelBySlug: '/app/travel/',
};

/**
 * Normalize a dynamic URL path segment before interpolating it into a backend
 * path. Reject empty or non-whitelisted values instead of forwarding them.
 */
function sanitizePathSegment(segment) {
  if (typeof segment !== 'string') {
    return null;
  }

  const trimmed = segment.trim();
  if (!trimmed) {
    return null;
  }

  return /^[A-Za-z0-9._-]+$/.test(trimmed) ? trimmed : null;
}

/**
 * Resolve the contact transport route to its backend API path.
 */
export function getContactBackendRoute(pathname, method) {
  if (pathname !== BFF_ROUTES.contact) {
    return null;
  }

  return {
    allow: 'POST',
    backendPath: '/v1/contact/',
    kind: 'contact',
    methodNotAllowed: method !== 'POST',
  };
}

/**
 * Resolve a travel-detail transport route to its backend API path.
 */
export function getTravelBackendRoute(pathname, method) {
  const match = pathname.match(/^\/app\/travel\/([^/]+)\/([^/]+)\/([^/]+)\/?$/);
  if (!match) {
    return null;
  }

  const [, rawCountrySlug, rawPlaceSlug, rawDateSlug] = match;
  const countrySlug = sanitizePathSegment(rawCountrySlug);
  const placeSlug = sanitizePathSegment(rawPlaceSlug);
  const dateSlug = sanitizePathSegment(rawDateSlug);
  if (!countrySlug || !placeSlug || !dateSlug) {
    return null;
  }

  return {
    allow: 'GET',
    backendPath: `/v1/travel/${countrySlug}/${placeSlug}/${dateSlug}/`,
    kind: 'travel',
    methodNotAllowed: method !== 'GET',
  };
}

/**
 * Resolve image helper transport routes to backend API paths.
 */
export function getImagesBackendRoute(pathname, method) {
  if (pathname === BFF_ROUTES.images || pathname === '/app/images') {
    return {
      allow: 'GET',
      backendPath: '/image-urls/',
      kind: 'images',
      methodNotAllowed: method !== 'GET',
    };
  }

  const match = pathname.match(/^\/app\/images\/([^/]+)\/?$/);
  if (!match) {
    return null;
  }

  const [, rawSlug] = match;
  const slug = sanitizePathSegment(rawSlug);
  if (!slug) {
    return null;
  }

  return {
    allow: 'GET',
    backendPath: `/image-urls/${slug}/`,
    kind: 'images',
    methodNotAllowed: method !== 'GET',
  };
}

export function getImageFilesBackendRoute(pathname, method) {
  const match = pathname.match(/^\/app\/image-files\/([^/]+)\/serve\/?$/);
  if (!match) {
    return null;
  }

  const [, rawSlug] = match;
  const slug = sanitizePathSegment(rawSlug);
  if (!slug) {
    return null;
  }

  return {
    allow: 'GET',
    backendPath: `/image-files/${slug}/serve/`,
    kind: 'image-file',
    methodNotAllowed: method !== 'GET',
  };
}

function getReadBackendRoute(pathname, method) {
  const routes = [
    {
      pathname: BFF_ROUTES.profile,
      backendPath: '/v1/profile/',
      kind: 'profile',
    },
    {
      pathname: BFF_ROUTES.background,
      backendPath: '/v1/background/',
      kind: 'background',
    },
    {
      pathname: BFF_ROUTES.settings,
      backendPath: '/v1/settings/',
      kind: 'settings',
    },
    {
      pathname: BFF_ROUTES.shop,
      backendPath: '/v1/shop/products/',
      kind: 'shop',
    },
    {
      pathname: BFF_ROUTES.travelHighlights,
      backendPath: '/v1/travel-highlights/',
      kind: 'travel-highlights',
    },
    {
      pathname: BFF_ROUTES.categories,
      backendPath: '/v1/categories/',
      kind: 'categories',
    },
    {
      pathname: BFF_ROUTES.tags,
      backendPath: '/v1/tags/',
      kind: 'tags',
    },
  ];

  for (const route of routes) {
    if (
      pathname === route.pathname ||
      pathname === route.pathname.slice(0, -1)
    ) {
      return {
        allow: 'GET',
        backendPath: route.backendPath,
        kind: route.kind,
        methodNotAllowed: method !== 'GET',
      };
    }
  }

  if (
    pathname === BFF_ROUTES.astroImages ||
    pathname === BFF_ROUTES.astroImages.slice(0, -1)
  ) {
    return {
      allow: 'GET',
      backendPath: '/v1/astroimages/',
      kind: 'astroimages',
      methodNotAllowed: method !== 'GET',
    };
  }

  const latestMatch = pathname.match(/^\/app\/astroimages\/latest\/?$/);
  if (latestMatch) {
    return {
      allow: 'GET',
      backendPath: '/v1/astroimages/latest/',
      kind: 'astroimages',
      methodNotAllowed: method !== 'GET',
    };
  }

  const detailMatch = pathname.match(/^\/app\/astroimages\/([^/]+)\/?$/);
  if (detailMatch) {
    const [, rawSlug] = detailMatch;
    const slug = sanitizePathSegment(rawSlug);
    if (!slug) {
      return null;
    }

    return {
      allow: 'GET',
      backendPath: `/v1/astroimages/${slug}/`,
      kind: 'astroimages',
      methodNotAllowed: method !== 'GET',
    };
  }

  return null;
}

/**
 * Return route metadata for a frontend-owned transport endpoint.
 *
 * Returns `null` when the pathname is not a known FE-owned transport endpoint.
 */
export function getFrontendTransportRoute(pathname, method) {
  return (
    getImageFilesBackendRoute(pathname, method) ||
    getContactBackendRoute(pathname, method) ||
    getTravelBackendRoute(pathname, method) ||
    getImagesBackendRoute(pathname, method) ||
    getReadBackendRoute(pathname, method)
  );
}
