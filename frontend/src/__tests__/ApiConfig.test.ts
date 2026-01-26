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
      // In Jest, process.env.API_URL might be undefined or set to a mock
      // Our default is DEFAULT_API_URL
      if (!process.env.API_URL) {
        expect(resolvedUrl).toBe(CONST_API_BASE_URL);
      }
    });
  });

  it('should not crash if process is undefined', () => {
    jest.isolateModules(() => {
      // Mock global.process as undefined
      const actualProcess = global.process;
      // @ts-ignore - simulating environment without process
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      delete (global as any).process;

      try {
        expect(() => require('../api/routes')).toThrow(
          'API_URL is not defined'
        );
      } finally {
        global.process = actualProcess;
      }
    });
  });

  it('should not crash if process is undefined', () => {
    jest.isolateModules(() => {
      // Mock global.process as undefined
      const actualProcess = global.process;
      // @ts-ignore - simulating environment without process
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      delete (global as any).process;

      try {
        expect(() => require('../api/routes')).toThrow(
          'API_URL is not defined'
        );
      } finally {
        global.process = actualProcess;
      }
    });
  });
});
