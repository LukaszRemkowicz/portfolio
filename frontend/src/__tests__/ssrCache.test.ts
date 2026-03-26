describe('ssrCache', () => {
  beforeEach(() => {
    jest.resetModules();
    delete (
      globalThis as typeof globalThis & {
        __portfolioSsrCacheState?: unknown;
      }
    ).__portfolioSsrCacheState;
  });

  it('returns cached shell data until TTL expires', async () => {
    jest.useFakeTimers();

    const { getCachedShellData } = await import('../../server/ssrCache.js');
    const loader = jest
      .fn()
      .mockResolvedValueOnce({ value: 1 })
      .mockResolvedValueOnce({ value: 2 });

    const first = await getCachedShellData({
      resource: 'profile',
      language: 'en',
      tags: ['profile'],
      ttlMs: 1000,
      loader,
    });

    const second = await getCachedShellData({
      resource: 'profile',
      language: 'en',
      tags: ['profile'],
      ttlMs: 1000,
      loader,
    });

    jest.advanceTimersByTime(1001);

    const third = await getCachedShellData({
      resource: 'profile',
      language: 'en',
      tags: ['profile'],
      ttlMs: 1000,
      loader,
    });

    expect(first).toEqual({ value: 1 });
    expect(second).toEqual({ value: 1 });
    expect(third).toEqual({ value: 2 });
    expect(loader).toHaveBeenCalledTimes(2);

    jest.useRealTimers();
  });

  it('invalidates all keys registered under a tag', async () => {
    const { getCachedShellData, invalidateCacheTags } =
      await import('../../server/ssrCache.js');

    const profileLoader = jest
      .fn()
      .mockResolvedValueOnce({ value: 'profile-v1' })
      .mockResolvedValueOnce({ value: 'profile-v2' });
    const settingsLoader = jest
      .fn()
      .mockResolvedValueOnce({ value: 'settings-v1' })
      .mockResolvedValueOnce({ value: 'settings-v2' });

    await getCachedShellData({
      resource: 'profile',
      language: 'en',
      tags: ['site-shell'],
      loader: profileLoader,
    });
    await getCachedShellData({
      resource: 'settings',
      language: 'en',
      tags: ['site-shell'],
      loader: settingsLoader,
    });

    expect(invalidateCacheTags(['site-shell'])).toEqual({
      invalidatedKeys: 2,
      tags: ['site-shell'],
    });

    const refreshedProfile = await getCachedShellData({
      resource: 'profile',
      language: 'en',
      tags: ['site-shell'],
      loader: profileLoader,
    });
    const refreshedSettings = await getCachedShellData({
      resource: 'settings',
      language: 'en',
      tags: ['site-shell'],
      loader: settingsLoader,
    });

    expect(refreshedProfile).toEqual({ value: 'profile-v2' });
    expect(refreshedSettings).toEqual({ value: 'settings-v2' });
    expect(profileLoader).toHaveBeenCalledTimes(2);
    expect(settingsLoader).toHaveBeenCalledTimes(2);
  });
});
