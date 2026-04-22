import type { PublicEnvSchema } from '../utils/env';

export {};

declare global {
  interface Window {
    __PUBLIC_ENV__?: Partial<PublicEnvSchema>;
  }
}
