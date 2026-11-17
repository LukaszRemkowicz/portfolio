import { assertEquals } from "@std/assert";
import { envelope, MAX_PAGE_SIZE, pageLink, pageSize, resolvePage } from "../pagination.ts";

const BASE = "https://x.supabase.co/functions/v1/api";
const PATH = "/v1/astroimages/";
const mk = (qs: string) => new URL(`http://h${PATH}${qs}`);

Deno.test("pageSize: default, limit, cap, invalid", () => {
  assertEquals(pageSize(null), 15);
  assertEquals(pageSize("2"), 2);
  assertEquals(pageSize("100"), MAX_PAGE_SIZE);
  assertEquals(pageSize("0"), 15);
  assertEquals(pageSize("-3"), 15);
  assertEquals(pageSize("abc"), 15);
});

Deno.test("resolvePage: valid, last, invalid", () => {
  assertEquals(resolvePage(null, 34, 15), 1);
  assertEquals(resolvePage("3", 34, 15), 3);
  assertEquals(resolvePage("last", 34, 15), 3);
  assertEquals(resolvePage("4", 34, 15), null);
  assertEquals(resolvePage("0", 34, 15), null);
  assertEquals(resolvePage("abc", 34, 15), null);
  assertEquals(resolvePage(null, 0, 15), 1); // empty first page is allowed
  assertEquals(resolvePage("2", 0, 15), null);
});

Deno.test("pageLink: sorted params, page replaced or removed", () => {
  const url = mk("?limit=2&lang=pl");
  assertEquals(pageLink(BASE, PATH, url, 2), `${BASE}${PATH}?lang=pl&limit=2&page=2`);
  assertEquals(
    pageLink(BASE, PATH, mk("?page=2&limit=2&lang=pl"), null),
    `${BASE}${PATH}?lang=pl&limit=2`,
  );
  assertEquals(pageLink(BASE, PATH, mk("?page=2"), null), `${BASE}${PATH}`);
  assertEquals(pageLink(BASE, PATH, mk("?tag=a%20b%27"), 2), `${BASE}${PATH}?page=2&tag=a+b%27`);
});

Deno.test("envelope: count/next/previous/results", () => {
  const url = mk("?limit=2&page=2");
  const link = (p: number | null) => pageLink(BASE, PATH, url, p);
  const mid = envelope(["a", "b"], 5, 2, 2, link);
  assertEquals(mid, {
    count: 5,
    next: `${BASE}${PATH}?limit=2&page=3`,
    previous: `${BASE}${PATH}?limit=2`, // previous page 1 drops the page param
    results: ["a", "b"],
  });
  const last = envelope(["e"], 5, 3, 2, link);
  assertEquals(last.next, null);
  assertEquals(last.previous, `${BASE}${PATH}?limit=2&page=2`);
  assertEquals(envelope([], 0, 1, 15, link), { count: 0, next: null, previous: null, results: [] });
});
