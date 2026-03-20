const DEFAULT_TTL_MS = 24 * 60 * 60 * 1000;

const state = globalThis.__portfolioSsrCacheState || {
  entries: new Map(),
  tagIndex: new Map(),
};

globalThis.__portfolioSsrCacheState = state;

function getHostKey(requestOrigin) {
  if (!requestOrigin) {
    return 'default';
  }

  try {
    return new URL(requestOrigin).host;
  } catch {
    return 'default';
  }
}

function makeKey(resource, language, requestOrigin) {
  return `${resource}:${language}:${getHostKey(requestOrigin)}`;
}

function indexTags(key, tags) {
  for (const tag of tags) {
    const taggedKeys = state.tagIndex.get(tag) || new Set();
    taggedKeys.add(key);
    state.tagIndex.set(tag, taggedKeys);
  }
}

function removeKey(key, tags = []) {
  state.entries.delete(key);

  for (const tag of tags) {
    const taggedKeys = state.tagIndex.get(tag);
    if (!taggedKeys) {
      continue;
    }

    taggedKeys.delete(key);
    if (taggedKeys.size === 0) {
      state.tagIndex.delete(tag);
    }
  }
}

export async function getCachedShellData({
  resource,
  language = 'en',
  requestOrigin,
  tags = [],
  ttlMs = DEFAULT_TTL_MS,
  loader,
}) {
  const key = makeKey(resource, language, requestOrigin);
  const now = Date.now();
  const cached = state.entries.get(key);

  if (cached && cached.expiresAt > now) {
    return cached.value;
  }

  if (cached) {
    removeKey(key, cached.tags);
  }

  const value = await loader();
  state.entries.set(key, {
    value,
    expiresAt: now + ttlMs,
    tags,
  });
  indexTags(key, tags);

  return value;
}

export function invalidateCacheTags(tags = []) {
  const normalizedTags = [...new Set(tags.filter(Boolean))];
  const keysToDelete = new Set();

  for (const tag of normalizedTags) {
    const taggedKeys = state.tagIndex.get(tag);
    if (!taggedKeys) {
      continue;
    }

    for (const key of taggedKeys) {
      keysToDelete.add(key);
    }
  }

  for (const key of keysToDelete) {
    const cached = state.entries.get(key);
    removeKey(key, cached?.tags || []);
  }

  return {
    invalidatedKeys: keysToDelete.size,
    tags: normalizedTags,
  };
}
