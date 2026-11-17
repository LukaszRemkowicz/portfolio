import type { Config } from "./config.ts";
import { activeLang, type Lang } from "./i18n.ts";

export type Ctx = {
  url: URL;
  /** Logical path as DRF sees it (function prefix stripped), e.g. `/v1/astroimages/`. */
  path: string;
  /** Absolute prefix for generated links: API_PUBLIC_BASE_URL (never derived from the request). */
  base: string;
  /** Raw `lang` query value (null when absent/empty). */
  lang: string | null;
  /** Language Django would have active (parler + country names). */
  active: Lang;
  cfg: Config;
};

/** Function prefix as deployed: `/functions/v1/api/<path>`; the runtime hands us `/api/<path>`. */
const FN_PREFIX = /^\/api(?=\/|$)/;

export function makeCtx(req: Request, cfg: Config): Ctx {
  const url = new URL(req.url);
  const path = url.pathname.replace(FN_PREFIX, "") || "/";
  const lang = qget(url, "lang") || null;
  return {
    url,
    path,
    base: cfg.publicBaseUrl,
    lang,
    active: activeLang(lang),
    cfg,
  };
}

/** Django QueryDict.get semantics: the last value wins. */
export function qget(url: URL, key: string): string | null {
  return url.searchParams.getAll(key).at(-1) ?? null;
}

export function json(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json" },
  });
}

export const detail = (message: string, status: number) => json({ detail: message }, status);

export function htmlError(status: number, title: string, message: string): Response {
  const body =
    `<!doctype html><html lang="en"><head><title>${status} - ${title}</title></head><body><h1>${status}</h1><h2>${title}</h2><p>${message}</p></body></html>`;
  return new Response(body, {
    status,
    headers: { "content-type": "text/html; charset=utf-8" },
  });
}
