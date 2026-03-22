import {
  getFrontendTransportRoute,
  getImageFilesBackendRoute,
  getImagesBackendRoute,
  getTravelBackendRoute,
} from '../../server/views/bff.js';

describe('BFF route sanitization', () => {
  it('rejects invalid image-file slugs before building backend paths', () => {
    expect(
      getImageFilesBackendRoute('/app/image-files/../etc/passwd/serve/', 'GET')
    ).toBeNull();

    expect(
      getImageFilesBackendRoute('/app/image-files/m31_2026-03.22/serve/', 'GET')
    ).toMatchObject({
      backendPath: '/image-files/m31_2026-03.22/serve/',
      kind: 'image-file',
    });
  });

  it('rejects invalid image helper slugs', () => {
    expect(getImagesBackendRoute('/app/images/bad%2fslug/', 'GET')).toBeNull();
    expect(
      getImagesBackendRoute('/app/images/m31-final/', 'GET')
    ).toMatchObject({
      backendPath: '/image-urls/m31-final/',
    });
  });

  it('rejects invalid travel detail path segments', () => {
    expect(
      getTravelBackendRoute('/app/travel/pl/krakow/2026-03-22%2fboom/', 'GET')
    ).toBeNull();

    expect(
      getTravelBackendRoute('/app/travel/pl/krakow/2026-03-22/', 'GET')
    ).toMatchObject({
      backendPath: '/v1/travel/pl/krakow/2026-03-22/',
      kind: 'travel',
    });
  });

  it('returns null for invalid astroimage detail slugs through the unified resolver', () => {
    expect(
      getFrontendTransportRoute('/app/astroimages/unsafe?slug/', 'GET')
    ).toBeNull();

    expect(
      getFrontendTransportRoute('/app/astroimages/m31-andromeda/', 'GET')
    ).toMatchObject({
      backendPath: '/v1/astroimages/m31-andromeda/',
      kind: 'astroimages',
    });
  });
});
