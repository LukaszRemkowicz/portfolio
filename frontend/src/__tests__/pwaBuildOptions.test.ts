import { createPwaOptions } from '../utils/pwaBuildOptions';

describe('PWA build options', () => {
  it('does not let the service worker serve the static Vite shell for SSR navigations', () => {
    const options = createPwaOptions('production', 'Portfolio Owner');

    expect(options.injectRegister).toBe(false);
    expect(options.workbox?.navigateFallback).toBe('');
    expect(options.workbox?.globIgnores).toContain('**/index.html');
  });
});
