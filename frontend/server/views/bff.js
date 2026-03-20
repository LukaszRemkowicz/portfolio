export const BFF_ROUTES = {
  contact: '/app/contact',
  images: '/app/images/',
  travelBySlug: '/app/travel/',
};

export function getTravelBackendPath(pathname) {
  const match = pathname.match(/^\/app\/travel\/([^/]+)\/([^/]+)\/([^/]+)\/?$/);
  if (!match) {
    return null;
  }

  const [, countrySlug, placeSlug, dateSlug] = match;
  return `/v1/travel/${countrySlug}/${placeSlug}/${dateSlug}/`;
}

export function getImagesBackendPath(pathname) {
  if (pathname === BFF_ROUTES.images || pathname === '/app/images') {
    return '/v1/images/';
  }

  const match = pathname.match(/^\/app\/images\/([^/]+)\/?$/);
  if (!match) {
    return null;
  }

  const [, slug] = match;
  return `/v1/images/${slug}/`;
}

export function resolveBffBackendPath(pathname, method) {
  if (pathname === BFF_ROUTES.contact) {
    return {
      allow: 'POST',
      backendPath: '/v1/contact/',
      kind: 'contact',
      methodNotAllowed: method !== 'POST',
    };
  }

  const travelBackendPath = getTravelBackendPath(pathname);
  if (travelBackendPath) {
    return {
      allow: 'GET',
      backendPath: travelBackendPath,
      kind: 'travel',
      methodNotAllowed: method !== 'GET',
    };
  }

  const imagesBackendPath = getImagesBackendPath(pathname);
  if (imagesBackendPath) {
    return {
      allow: 'GET',
      backendPath: imagesBackendPath,
      kind: 'images',
      methodNotAllowed: method !== 'GET',
    };
  }

  return null;
}
