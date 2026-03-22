import { API_BASE_URL as CONST_API_BASE_URL } from '../api/constants';
import { API_BASE_URL } from '../api/routes';

/**
 * Test suite for API Configuration
 *
 * Verifies that the API_BASE_URL is correctly resolved from environment variables
 * and that the application handles cases where 'process' might be undefined
 * (e.g., in some browser environments or restricted test runners).
 */
describe('API Configuration', () => {
  const originalProcess = global.process;

  afterEach(() => {
    global.process = originalProcess;
    jest.resetModules();
  });

  it('should have a defined API_BASE_URL', () => {
    expect(API_BASE_URL).toBeDefined();
    expect(typeof API_BASE_URL).toBe('string');
  });

  it('should fallback to default URL if process.env.API_URL is missing', () => {
    // We need to re-import because the constant is evaluated at load time
    jest.isolateModules(() => {
      const { API_BASE_URL: resolvedUrl } = require('../api/routes');
      expect(resolvedUrl).toBe(CONST_API_BASE_URL);
    });
  });

  it('should prefer browser same-origin over public API env', () => {
    const warnSpy = jest.spyOn(console, 'warn').mockImplementation(() => {});
    jest.isolateModules(() => {
      delete process.env.VITE_API_URL;
      const { API_BASE_URL: resolvedUrl } = require('../api/constants');
      expect(resolvedUrl).toBe(window.location.origin);
      expect(warnSpy).not.toHaveBeenCalled();
    });
    warnSpy.mockRestore();
  });

  it('returns empty string (not crash) when env is completely missing', () => {
    const warnSpy = jest.spyOn(console, 'warn').mockImplementation(() => {});
    jest.isolateModules(() => {
      delete process.env.VITE_API_URL;
      expect(() => require('../api/constants')).not.toThrow();
    });
    warnSpy.mockRestore();
  });
});
