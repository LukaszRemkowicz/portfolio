// Runtime configuration. Names mirror the Django settings they replace.
export type Config = {
  publicDomain: string; // R2_PUBLIC_DOMAIN
  signingKey: string; // MEDIA_SIGNING_KEY (not Django's SECRET_KEY)
  signedExpiration: number; // SECURE_MEDIA_URL_EXPIRATION
  publicBaseUrl: string; // API_PUBLIC_BASE_URL, required: prefix of every absolute URL
  r2: {
    endpoint: string; // R2_ENDPOINT_URL
    accessKeyId: string; // R2_ACCESS_KEY_ID
    secretAccessKey: string; // R2_SECRET_ACCESS_KEY
    privateBucket: string; // R2_PRIVATE_BUCKET
    signedExpire: number; // R2_SIGNED_URL_EXPIRE
  };
};

/** Env names that must be set; health and every route answer 503 listing the names if not. */
export const REQUIRED_ENV = [
  "API_DB_HOST",
  "API_DB_PORT",
  "API_DB_NAME",
  "API_DB_USER",
  "API_DB_PASSWORD",
  "MEDIA_SIGNING_KEY",
  "API_PUBLIC_BASE_URL",
  "API_ORIGIN_SECRET",
  "R2_ACCESS_KEY_ID",
  "R2_SECRET_ACCESS_KEY",
];

/** Names (never values) of required variables that are missing. */
export function missingEnv(get: (k: string) => string | undefined = (k) => Deno.env.get(k)) {
  return REQUIRED_ENV.filter((k) => !get(k));
}

export function loadConfig(
  get: (k: string) => string | undefined = (k) => Deno.env.get(k),
): Config {
  const s = (k: string, d = "") => get(k) || d;
  const n = (k: string, d: number) => Number.parseInt(get(k) ?? "", 10) || d;
  return {
    publicDomain: s("R2_PUBLIC_DOMAIN", "media.lukaszremkowicz.com"),
    signingKey: s("MEDIA_SIGNING_KEY"),
    signedExpiration: n("SECURE_MEDIA_URL_EXPIRATION", 3600),
    publicBaseUrl: s("API_PUBLIC_BASE_URL").replace(/\/+$/, ""),
    r2: {
      endpoint: s(
        "R2_ENDPOINT_URL",
        "https://8e28090942604cdb0c3620bd22f54145.r2.cloudflarestorage.com",
      ),
      accessKeyId: s("R2_ACCESS_KEY_ID"),
      secretAccessKey: s("R2_SECRET_ACCESS_KEY"),
      privateBucket: s("R2_PRIVATE_BUCKET", "portfolio-originals"),
      signedExpire: n("R2_SIGNED_URL_EXPIRE", 300),
    },
  };
}
