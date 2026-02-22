// frontend/src/vite-env.d.ts
/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string;
  readonly VITE_GA_TRACKING_ID: string;
  readonly VITE_ENABLE_GA: string;
  readonly VITE_SENTRY_DSN_FE: string;
  readonly VITE_ENVIRONMENT: string;
  readonly MODE: string;
  readonly DEV: boolean;
  readonly PROD: boolean;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
