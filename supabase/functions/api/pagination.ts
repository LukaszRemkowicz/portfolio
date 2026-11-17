// DRF PageNumberPagination (AstroImagePagination: page_size 15, `limit`, max 48).
export const PAGE_SIZE = 15;
export const MAX_PAGE_SIZE = 48;

export type Envelope<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};

/** `limit` query value -> page size; invalid or non-positive falls back to the default. */
export function pageSize(limit: string | null): number {
  if (limit === null || !/^\s*[+-]?\d+\s*$/.test(limit)) return PAGE_SIZE;
  const n = Number.parseInt(limit, 10);
  return n <= 0 ? PAGE_SIZE : Math.min(n, MAX_PAGE_SIZE);
}

/** Resolve the requested page against the total; null means DRF's 404 "Invalid page.". */
export function resolvePage(raw: string | null, count: number, size: number): number | null {
  const numPages = Math.max(1, Math.ceil(count / size));
  if (raw === "last") return numPages;
  const page = raw === null || raw === ""
    ? 1
    : /^\s*[+-]?\d+\s*$/.test(raw)
    ? Number.parseInt(raw, 10)
    : NaN;
  return Number.isInteger(page) && page >= 1 && page <= numPages ? page : null;
}

/** Python urllib.parse.quote_plus */
function quotePlus(s: string): string {
  return encodeURIComponent(s)
    .replace(/[!'()*]/g, (c) => "%" + c.charCodeAt(0).toString(16).toUpperCase())
    .replace(/%20/g, "+");
}

/** DRF replace_query_param / remove_query_param: sorted keys, quote_plus encoding. */
export function pageLink(base: string, path: string, url: URL, page: number | null): string {
  const params = new Map<string, string[]>();
  for (const [k, v] of url.searchParams) params.set(k, [...(params.get(k) ?? []), v]);
  if (page === null) params.delete("page");
  else params.set("page", [String(page)]);
  const qs = [...params.keys()].sort().flatMap((k) =>
    params.get(k)!.map((v) => `${quotePlus(k)}=${quotePlus(v)}`)
  ).join("&");
  return `${base}${path}${qs ? "?" + qs : ""}`;
}

export function envelope<T>(
  results: T[],
  count: number,
  page: number,
  size: number,
  link: (page: number | null) => string,
): Envelope<T> {
  const numPages = Math.max(1, Math.ceil(count / size));
  return {
    count,
    next: page < numPages ? link(page + 1) : null,
    previous: page > 1 ? link(page - 1 === 1 ? null : page - 1) : null,
    results,
  };
}
