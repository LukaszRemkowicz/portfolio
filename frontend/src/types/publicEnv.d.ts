export {};

declare global {
  interface Window {
    __PUBLIC_ENV__?: {
      API_URL?: string;
      GA_TRACKING_ID?: string;
      ENABLE_GA?: string;
      PROJECT_OWNER?: string;
      SITE_DOMAIN?: string;
    };
  }
}
