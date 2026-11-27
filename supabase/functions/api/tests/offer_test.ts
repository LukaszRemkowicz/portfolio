import { assertEquals } from "@std/assert";
import { clearOfferCacheForTests, livePrice, parseOffer } from "../offer.ts";

const NOW = Date.parse("2026-11-27T12:00:00Z");
const offer = (promotion: unknown = null) => ({ amount: 13899, currency: "eur", promotion });

Deno.test("parseOffer: running promotion, ended promotion, none, invalid", () => {
  assertEquals(parseOffer(offer({ amount: 10999, ends_at: "2026-12-24T23:00:00Z" }), NOW), {
    amount: "109.99",
    currency: "EUR",
  });
  assertEquals(parseOffer(offer({ amount: 10999, ends_at: "2026-11-01T00:00:00Z" }), NOW), {
    amount: "138.99",
    currency: "EUR",
  });
  assertEquals(parseOffer(offer(), NOW), { amount: "138.99", currency: "EUR" });
  assertEquals(parseOffer({ amount: "13899", currency: "eur" }, NOW), null);
  assertEquals(parseOffer({ amount: 13899, currency: "euro" }, NOW), null);
  assertEquals(parseOffer(null, NOW), null);
});

Deno.test("livePrice: caches per URL, null on HTTP error or network failure", async () => {
  const real = globalThis.fetch;
  let calls = 0;
  let mode: "ok" | "500" | "throw" = "ok";
  globalThis.fetch = (() => {
    calls++;
    if (mode === "throw") return Promise.reject(new Error("down"));
    return Promise.resolve(
      mode === "ok" ? Response.json(offer()) : new Response("x", { status: 500 }),
    );
  }) as typeof fetch;
  try {
    clearOfferCacheForTests();
    assertEquals(await livePrice("https://a/offer", NOW), { amount: "138.99", currency: "EUR" });
    assertEquals(await livePrice("https://a/offer", NOW + 1000), {
      amount: "138.99",
      currency: "EUR",
    });
    assertEquals(calls, 1);

    mode = "500";
    assertEquals(await livePrice("https://b/offer", NOW), null);
    mode = "throw";
    assertEquals(await livePrice("https://c/offer", NOW), null);
  } finally {
    globalThis.fetch = real;
    clearOfferCacheForTests();
  }
});
