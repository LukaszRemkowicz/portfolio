/**
 * Normalize backend media URLs into frontend-safe public paths for BFF responses.
 */
export function normalizePublicMediaUrl(value) {
  if (typeof value !== 'string' || !value) {
    return value;
  }

  const toFrontendImageFilePath = pathname =>
    pathname.startsWith('/image-files/') ? `/app${pathname}` : pathname;

  const isRelativePublicMedia =
    value.startsWith('/media/') ||
    value.startsWith('/static/') ||
    value.startsWith('/app/image-files/') ||
    value.startsWith('/image-files/') ||
    /^\/v1\/images\/[^/]+\/serve\/?(?:\?.*)?$/.test(value);

  if (isRelativePublicMedia) {
    if (/^\/v1\/images\/[^/]+\/serve\/?(?:\?.*)?$/.test(value)) {
      return value.replace(/^\/v1\/images\//, '/app/image-files/');
    }
    return toFrontendImageFilePath(value);
  }

  if (!value.startsWith('http://') && !value.startsWith('https://')) {
    return value;
  }

  try {
    const parsed = new URL(value);
    const isPublicMedia = parsed.pathname.startsWith('/media/');
    const isPublicStatic = parsed.pathname.startsWith('/static/');
    const isFrontendImageFile = parsed.pathname.startsWith('/app/image-files/');
    const isInternalImageFile = parsed.pathname.startsWith('/image-files/');
    const isSecureImage = /^\/v1\/images\/[^/]+\/serve\/?$/.test(
      parsed.pathname
    );

    if (isPublicMedia || isPublicStatic || isFrontendImageFile) {
      return `${parsed.pathname}${parsed.search}`;
    }

    if (isInternalImageFile) {
      return `/app${parsed.pathname}${parsed.search}`;
    }

    if (isSecureImage) {
      return `${parsed.pathname.replace(/^\/v1\/images\//, '/app/image-files/')}${parsed.search}`;
    }
  } catch {
    return value;
  }

  return value;
}

export function normalizeBffPayload(payload, kind, requestOrigin) {
  if (!payload) return payload;

  const data =
    kind === 'astroimages' && payload.results ? payload.results : payload;

  if (kind !== 'images' && kind !== 'astroimages') {
    return data;
  }

  if (Array.isArray(data)) {
    return data.map(item =>
      typeof item === 'object' && item.url
        ? { ...item, url: normalizePublicMediaUrl(item.url, requestOrigin) }
        : item
    );
  }

  if (typeof data.url === 'string') {
    return {
      ...data,
      url: normalizePublicMediaUrl(data.url, requestOrigin),
    };
  }

  if (typeof data === 'object' && !Array.isArray(data)) {
    return Object.fromEntries(
      Object.entries(data).map(([key, value]) => [
        key,
        normalizePublicMediaUrl(value, requestOrigin),
      ])
    );
  }

  return data;
}
