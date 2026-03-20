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
  travelBySlug: '/app/travel/',
};

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

  const [, countrySlug, placeSlug, dateSlug] = match;
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
      backendPath: '/v1/images/',
      kind: 'images',
      methodNotAllowed: method !== 'GET',
    };
  }

  const match = pathname.match(/^\/app\/images\/([^/]+)\/?$/);
  if (!match) {
    return null;
  }

  const [, slug] = match;
  return {
    allow: 'GET',
    backendPath: `/v1/images/${slug}/`,
    kind: 'images',
    methodNotAllowed: method !== 'GET',
  };
}

/**
 * Return route metadata for a frontend-owned transport endpoint.
 *
 * Returns `null` when the pathname is not a known FE-owned transport endpoint.
 */
export function getFrontendTransportRoute(pathname, method) {
  return (
    getContactBackendRoute(pathname, method) ||
    getTravelBackendRoute(pathname, method) ||
    getImagesBackendRoute(pathname, method)
  );
}
