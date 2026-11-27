import { assert, assertEquals } from "@std/assert";
import { REQUIRED_ENV } from "../config.ts";
import { setDbForTests } from "../db.ts";
import { r2 } from "../r2.ts";
import { handler, ORIGIN_SECRET_HEADER } from "../router.ts";
import { signedParams } from "../signing.ts";
import { drfDateTime } from "../format.ts";
import { clearOfferCacheForTests } from "../offer.ts";

const KEY = "handler-test-key";
const BASE = "https://p.supabase.co/functions/v1/api";
const SLUG = "some-slug";
const SECRET = "origin-secret";
/** Request as the FE Worker sends it (with the origin secret). */
const req = (url: string) => new Request(url, { headers: { [ORIGIN_SECRET_HEADER]: SECRET } });

let dbCalls = 0;
let presignCalls = 0;
let rowsFor: (text: string, params: unknown[]) => unknown[] = () => [];
/** Every stub query: SQL text (params as `?`) and its parameters. */
let log: { text: string; params: unknown[] }[] = [];

function setup(env: Record<string, string> = {}) {
  for (const k of REQUIRED_ENV) Deno.env.set(k, "x");
  Deno.env.set("MEDIA_SIGNING_KEY", KEY);
  Deno.env.set("API_PUBLIC_BASE_URL", BASE);
  Deno.env.set("API_ORIGIN_SECRET", SECRET);
  for (const [k, v] of Object.entries(env)) Deno.env.set(k, v);
  dbCalls = 0;
  presignCalls = 0;
  rowsFor = () => [];
  log = [];
  setDbForTests((strings: TemplateStringsArray, ...params: unknown[]) => {
    // sql("table") / sql(["col"]) are identifier helpers, not queries.
    if (!Object.hasOwn(strings, "raw")) return { identifier: strings };
    dbCalls++;
    const text = strings.join("?");
    log.push({ text, params });
    return Promise.resolve(rowsFor(text, params));
  });
  r2.presignGet = (_cfg, key) => {
    presignCalls++;
    return Promise.resolve(`https://r2.example/${key}?X-Amz-Signature=stub`);
  };
}

const serve = (qs: string) => handler(req(`http://h/api/image-files/${SLUG}/serve/${qs}`));

Deno.test("serve: missing, tampered and expired signatures are 403 without DB or presign", async () => {
  setup();
  const now = Math.floor(Date.now() / 1000);
  const ok = await signedParams(KEY, SLUG, 3600, now);
  const expired = await signedParams(KEY, SLUG, -10, now);
  for (
    const qs of [
      "",
      "?s=abc",
      "?e=123",
      `?s=${ok.s}&e=${ok.e + 1}`,
      `?s=${"0".repeat(64)}&e=${ok.e}`,
      `?s=${expired.s}&e=${expired.e}`,
    ]
  ) {
    assertEquals((await serve(qs)).status, 403, qs);
  }
  assertEquals(dbCalls, 0);
  assertEquals(presignCalls, 0);
});

Deno.test("serve: valid signature -> 302 to presigned URL, no-store", async () => {
  setup();
  rowsFor = (t) => (t.includes("high_resolution") ? [{ file: "images/hi/a b.webp" }] : []);
  const { s, e } = await signedParams(KEY, SLUG, 3600);
  const res = await serve(`?s=${s}&e=${e}`);
  assertEquals(res.status, 302);
  assertEquals(res.headers.get("cache-control"), "private, no-store, max-age=0");
  assertEquals(
    res.headers.get("location"),
    "https://r2.example/images/hi/a b.webp?X-Amz-Signature=stub",
  );
  assertEquals(presignCalls, 1);
});

Deno.test("serve: valid signature, unknown slug -> 404", async () => {
  setup();
  const { s, e } = await signedParams(KEY, SLUG, 3600);
  assertEquals((await serve(`?s=${s}&e=${e}`)).status, 404);
  assertEquals(presignCalls, 0);
});

Deno.test("image-urls: validation errors, malformed ids and DB uuid errors", async () => {
  setup();
  const get = (qs: string) => handler(req(`http://h/image-urls/${qs}`));
  assertEquals((await get("")).status, 400);
  assertEquals((await get("?ids=")).status, 400);
  assertEquals((await get("?ids=a,b")).status, 400);
  for (const ids of ["zzz", "{a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11}"]) {
    const res = await get(`?ids=${encodeURIComponent(ids)}`);
    assertEquals(res.status, 200);
    assertEquals(await res.json(), {});
  }
  assertEquals(dbCalls, 0);
  setDbForTests(() => Promise.reject(Object.assign(new Error("bad uuid"), { code: "22P02" })));
  const res = await get("?ids=a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11");
  assertEquals(res.status, 200);
  assertEquals(await res.json(), {});
});

Deno.test("image-urls: link is built from API_PUBLIC_BASE_URL and signed", async () => {
  setup();
  const pk = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11";
  rowsFor = (t) => (t.includes("high_resolution") ? [] : [{ id: pk, slug: SLUG }]);
  const res = await handler(req(`http://evil.example/api/image-urls/?ids=${pk}`));
  const url = (await res.json())[pk] as string;
  assert(url.startsWith(`${BASE}/image-files/${SLUG}/serve/?s=`), url);
  const u = new URL(url);
  assertEquals(
    (await serve(`?s=${u.searchParams.get("s")}&e=${u.searchParams.get("e")}`)).status,
    404, // signature accepted (no 403); stub has no variant row
  );
});

Deno.test("image-urls retrieve: unknown slug 404", async () => {
  setup();
  assertEquals((await handler(req("http://h/image-urls/nope/"))).status, 404);
});

Deno.test("bad percent-encoding in a path segment is a 404, not a 500", async () => {
  setup();
  const res = await handler(req("http://h/v1/astroimages/%ZZ/"));
  assertEquals(res.status, 404);
  assertEquals((await res.json()).detail, "No AstroImage matches the given query.");
});

Deno.test("health: 200 when configured, 503 naming missing vars only", async () => {
  setup();
  assertEquals((await handler(req("http://h/health"))).status, 200);
  Deno.env.delete("MEDIA_SIGNING_KEY");
  const res = await handler(req("http://h/health"));
  assertEquals(res.status, 503);
  const body = await res.json();
  assertEquals(body.missing, ["MEDIA_SIGNING_KEY"]);
  assertEquals(JSON.stringify(body).includes(KEY), false);
  // Without the origin secret the names stay hidden.
  const anon = await handler(new Request("http://h/health"));
  assertEquals(anon.status, 403);
  assertEquals((await anon.json()).missing, undefined);
});

Deno.test("hidden API: no API_ORIGIN_SECRET configured fails closed with a bare 503", async () => {
  setup();
  Deno.env.delete("API_ORIGIN_SECRET");
  for (const r of [req("http://h/health"), new Request("http://h/health")]) {
    const res = await handler(r);
    assertEquals(res.status, 503);
    assertEquals(await res.json(), { detail: "Service misconfigured." });
  }
  assertEquals(dbCalls, 0);
});

Deno.test("hidden API: missing or wrong origin secret is 403 before routing or DB", async () => {
  setup();
  const cases: Record<string, string>[] = [{}, { [ORIGIN_SECRET_HEADER]: "wrong" }, {
    [ORIGIN_SECRET_HEADER]: "",
  }];
  for (const headers of cases) {
    for (const path of ["/api/health", "/api/v1/settings/", `/api/image-files/${SLUG}/serve/`]) {
      const res = await handler(new Request(`http://h${path}`, { headers }));
      assertEquals(res.status, 403, `${path} ${JSON.stringify(headers)}`);
    }
  }
  const post = await handler(new Request("http://h/api/v1/contact/", { method: "POST" }));
  assertEquals(post.status, 403);
  assertEquals(dbCalls, 0);
  assertEquals((await handler(req("http://h/api/health"))).status, 200);
});

// ---------------------------------------------------------------- pagination, profile, settings

const listQueries = () => ({
  count: log.filter((q) => q.text.includes("count(*)::int as count")),
  rows: log.filter((q) => q.text.includes("order by a.created_at desc, a.id desc limit")),
});

Deno.test("gallery: numeric page fetches count and rows together; beyond the count is 404", async () => {
  setup();
  rowsFor = (t) => (t.includes("count(*)::int as count") ? [{ count: 3 }] : []);
  const ok = await handler(req("http://h/v1/astroimages/?limit=2&page=2"));
  assertEquals(ok.status, 200);
  const body = await ok.json();
  assertEquals([body.count, body.next, body.results], [3, null, []]);
  assert(String(body.previous).endsWith("/v1/astroimages/?limit=2"));
  assertEquals(listQueries().rows[0].params.slice(-2), [2, 2]); // limit 2 offset 2

  setup();
  rowsFor = (t) => (t.includes("count(*)::int as count") ? [{ count: 3 }] : []);
  const beyond = await handler(req("http://h/v1/astroimages/?limit=2&page=3"));
  assertEquals(beyond.status, 404);
  assertEquals(await beyond.json(), { detail: "Invalid page." });
});

Deno.test("gallery: page=last counts first, then reads that page", async () => {
  setup();
  rowsFor = (t) => (t.includes("count(*)::int as count") ? [{ count: 5 }] : []);
  const res = await handler(req("http://h/v1/astroimages/?limit=2&page=last"));
  assertEquals(res.status, 200);
  const { count, rows } = listQueries();
  assertEquals([count.length, rows.length], [1, 1]);
  assert(log.indexOf(count[0]) < log.indexOf(rows[0]));
  assertEquals(rows[0].params.slice(-2), [2, 4]); // page 3 of 3
  const body = await res.json();
  assertEquals(body.next, null);
  assert(String(body.previous).endsWith("page=2"));
});

Deno.test("gallery: malformed or non-positive page is 404 before any query", async () => {
  for (const page of ["abc", "0", "-1", "1.5"]) {
    setup();
    const res = await handler(req(`http://h/v1/astroimages/?page=${page}`));
    assertEquals(res.status, 404, page);
    const { count, rows } = listQueries();
    assertEquals([count.length, rows.length], [0, 0], page);
  }
});

const USER = { id: 1, first_name: "A", last_name: "B", is_active: true, contact_email: "a@b.c" };

Deno.test("profile: no user and inactive user are 404 with DRF messages", async () => {
  setup();
  const none = await handler(req("http://h/v1/profile/"));
  assertEquals(none.status, 404);
  assertEquals(await none.json(), { detail: "No user found." });

  setup();
  rowsFor = (t) => (t.includes("contact_email") ? [{ ...USER, is_active: false }] : []);
  const inactive = await handler(req("http://h/v1/profile/"));
  assertEquals(inactive.status, 404);
  assertEquals(await inactive.json(), { detail: "User is not active." });
});

const SETTINGS = {
  programming_enabled: true,
  contact_form_enabled: false,
  travel_highlights_enabled: true,
  lastimages_enabled: true,
  shop_enabled: false,
};

Deno.test("settings: no meteors config gives meteors null; missing settings row is 404", async () => {
  setup();
  rowsFor = (t) =>
    t.includes("from core_landingpagesettings s")
      ? [{ ...SETTINGS, meteors_found: false, random_stars_shooting: null }]
      : t.includes("sum(calculated_exposure_hours)")
      ? [{ total: null }]
      : [];
  const res = await handler(req("http://h/v1/settings/"));
  assertEquals(res.status, 200);
  assertEquals(await res.json(), {
    programming: true,
    contactForm: false,
    travelHighlights: true,
    lastimages: true,
    shop: false,
    total_time_spent: 2,
    meteors: null,
  });

  setup();
  rowsFor = (t) => (t.includes("sum(calculated_exposure_hours)") ? [{ total: 1 }] : []);
  const missing = await handler(req("http://h/v1/settings/"));
  assertEquals(missing.status, 404);
  assertEquals(await missing.json(), { detail: "Landing Page Settings not initialized." });
});

Deno.test("shop enabled: settings head merged with products; price stays a string", async () => {
  setup();
  const has = (params: unknown[], v: string) =>
    params.some((p) => p === v || (p as { identifier?: unknown })?.identifier === v);
  const variant = (owner: string, role: string, width: number, file: string) => ({
    owner,
    role,
    width,
    height: 100,
    mime_type: "image/webp",
    file,
  });
  rowsFor = (t, params) => {
    if (t.includes("select shop_enabled")) return [{ shop_enabled: true }];
    if (t.includes("from shop_shopproduct where is_active")) {
      return [{
        id: "7",
        price: "12.50",
        currency: "PLN",
        external_url: "https://shop.example/print",
        is_active: true,
        created_epoch: "1700000000",
      }];
    }
    if (t.includes("from shop_shopsettings")) return [{ id: 1 }];
    if (has(params, "shop_shopproduct_translation")) {
      return [{ master: "7", language_code: "en", title: "Print", description: "Nice" }];
    }
    if (has(params, "shop_shopsettings_translation")) {
      return [{ master: "1", language_code: "en", title: "Shop", description: "Buy" }];
    }
    if (has(params, "shopproduct")) return [variant("7", "thumbnail", 560, "shop/t.webp")];
    if (has(params, "shopsettings")) return [variant("1", "background", 2560, "shop/bg.webp")];
    return [];
  };
  const res = await handler(req("http://h/v1/shop/products/?lang=pl"));
  assertEquals(res.status, 200);
  const body = await res.json();
  assertEquals([body.title, body.description], ["Shop", "Buy"]); // pl falls back to en
  assert(body.fallback_image.url.endsWith("/shop/bg.webp"));
  assertEquals(body.variants.background.length, 1);
  assertEquals(body.products.length, 1);
  const [p] = body.products;
  assertEquals(
    {
      id: p.id,
      title: p.title,
      description: p.description,
      price: p.price,
      currency: p.currency,
      external_url: p.external_url,
      is_active: p.is_active,
      created_at: p.created_at,
    },
    {
      id: "7",
      title: "Print",
      description: "Nice",
      price: "12.50",
      currency: "PLN",
      external_url: "https://shop.example/print",
      is_active: true,
      created_at: drfDateTime("1700000000"),
    },
  );
  assert(p.fallback_image.url.endsWith("/shop/t.webp"));
  assertEquals(p.variants.thumbnail.length, 1);
});

let projectPricing: Record<string, unknown> = {};
function projectRows(t: string, params: unknown[], enabled = true): unknown[] {
  const has = (v: string) =>
    params.some((p) => p === v || (p as { identifier?: unknown })?.identifier === v);
  if (t.includes("select programming_enabled")) return [{ programming_enabled: enabled }];
  if (t.includes("from programming_project where is_active")) {
    return [{
      id: "3",
      technologies: " Python, Django ,, React ",
      github_url: "https://github.com/x/y",
      live_url: "",
      pricing: "",
      price: null,
      currency: "PLN",
      created_epoch: "1700000000",
      ...projectPricing,
    }];
  }
  if (has("programming_project_translation")) {
    return [{
      master: "3",
      language_code: "en",
      name: "Proj",
      description: "<p>D</p>",
      badge: "First on macOS",
    }];
  }
  if (has("project")) {
    return [{
      owner: "3",
      role: "thumbnail",
      width: 800,
      height: 500,
      mime_type: "image/webp",
      file: "programming/projects/thumbnail/a b.webp",
    }];
  }
  return [];
}

Deno.test("projects: flag off is 404", async () => {
  setup();
  rowsFor = (t, p) => projectRows(t, p, false);
  const res = await handler(req("http://h/v1/projects/"));
  assertEquals(res.status, 404);
  assertEquals(await res.json(), { detail: "Projects are currently not available." });
});

Deno.test("projects: shape, technologies split, R2 vs API_MEDIA_BASE_URL variant URL", async () => {
  setup();
  Deno.env.delete("API_MEDIA_BASE_URL");
  rowsFor = (t, p) => projectRows(t, p);
  const res = await handler(req("http://h/v1/projects/?lang=pl"));
  assertEquals(res.status, 200);
  const { projects } = await res.json();
  assertEquals(projects.length, 1);
  const [p] = projects;
  assertEquals(
    {
      id: p.id,
      name: p.name,
      description: p.description,
      badge: p.badge,
      technologies: p.technologies,
      github_url: p.github_url,
      live_url: p.live_url,
      created_at: p.created_at,
    },
    {
      id: "3",
      name: "Proj",
      description: "<p>D</p>",
      badge: "First on macOS",
      technologies: ["Python", "Django", "React"],
      github_url: "https://github.com/x/y",
      live_url: "",
      created_at: drfDateTime("1700000000"),
    },
  );
  assertEquals(
    p.fallback_image.url,
    "https://media.lukaszremkowicz.com/programming/projects/thumbnail/a%20b.webp",
  );
  assertEquals(p.variants.thumbnail.length, 1);

  setup({ API_MEDIA_BASE_URL: "http://localhost:8000/media/" });
  try {
    rowsFor = (t, params) => projectRows(t, params);
    const local = await (await handler(req("http://h/v1/projects/"))).json();
    assertEquals(
      local.projects[0].fallback_image.url,
      "http://localhost:8000/media/programming/projects/thumbnail/a%20b.webp",
    );
  } finally {
    Deno.env.delete("API_MEDIA_BASE_URL");
  }
});

Deno.test("projects: price_tag shapes", async () => {
  const cases: [Record<string, unknown>, unknown][] = [
    [{}, null],
    [{ pricing: "free" }, { type: "free" }],
    [{ pricing: "paid", price: "49", currency: "EUR" }, {
      type: "paid",
      amount: "49.00",
      currency: "EUR",
    }],
  ];
  for (const [pricing, expected] of cases) {
    setup();
    projectPricing = pricing;
    rowsFor = (t, p) => projectRows(t, p);
    const { projects } = await (await handler(req("http://h/v1/projects/"))).json();
    assertEquals(projects[0].price_tag, expected);
  }
  projectPricing = {};
});

Deno.test("projects: live price from price_source_url, stored price when it fails", async () => {
  const real = globalThis.fetch;
  try {
    for (
      const [answer, expected] of [
        [Response.json({ amount: 13899, currency: "eur", promotion: null }), "138.99 EUR"],
        [new Response("x", { status: 503 }), "49.00 PLN"],
      ] as const
    ) {
      setup();
      clearOfferCacheForTests();
      globalThis.fetch = (() => Promise.resolve(answer)) as typeof fetch;
      projectPricing = {
        pricing: "paid",
        price: "49",
        currency: "PLN",
        price_source_url: "https://api.example/offer",
      };
      rowsFor = (t, p) => projectRows(t, p);
      const { projects } = await (await handler(req("http://h/v1/projects/"))).json();
      const tag = projects[0].price_tag;
      assertEquals(`${tag.amount} ${tag.currency}`, expected);
    }
  } finally {
    globalThis.fetch = real;
    clearOfferCacheForTests();
    projectPricing = {};
  }
});

Deno.test("sitemap: exact XML, Warsaw lastmod across midnight, headers", async () => {
  setup();
  const late = String(Date.parse("2026-03-01T23:30:00Z") / 1000); // Warsaw: 2026-03-02 00:30
  const early = String(Date.parse("2026-01-10T10:00:00Z") / 1000);
  rowsFor = (t) =>
    t.includes("core_landingpagesettings")
      ? [{ programming_enabled: true, shop_enabled: false }]
      : t.includes("astrophotography_astroimage")
      ? Array.from({ length: 31 }, (_, i) => ({ slug: `img-${i}`, updated: i ? early : late }))
      : t.includes("astrophotography_mainpagelocation")
      ? [
        { country_slug: "spain", place_slug: "", lower: "2026-08-03", updated: early },
        { country_slug: "peru", place_slug: "cusco", lower: null, updated: early },
      ]
      : [];
  const res = await handler(req("http://h/api/sitemap.xml"));
  assertEquals(res.status, 200);
  assertEquals(res.headers.get("content-type"), "application/xml");
  assertEquals(res.headers.get("cache-control"), "max-age=43200");
  const url = (p: string, last: string | null, f: string, pr: string) =>
    `<url><loc>https://p.supabase.co${p}</loc>${
      last ? `<lastmod>${last}</lastmod>` : ""
    }<changefreq>${f}</changefreq><priority>${pr}</priority></url>`;
  const urls = [
    ...["/", "/astrophotography", "/privacy", "/programming"].map((p) =>
      url(p, null, "daily", "1.0")
    ),
    url("/astrophotography?page=2", "2026-03-02", "weekly", "0.6"),
    url("/astrophotography?page=3", "2026-03-02", "weekly", "0.6"),
    url("/astrophotography/img-0", "2026-03-02", "weekly", "0.8"),
    ...Array.from(
      { length: 30 },
      (_, i) => url(`/astrophotography/img-${i + 1}`, "2026-01-10", "weekly", "0.8"),
    ),
    url("/travel/spain/explore/aug2026", "2026-01-10", "monthly", "0.7"),
  ].join("");
  assertEquals(
    await res.text(),
    `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n${urls}\n</urlset>\n`,
  );
});
