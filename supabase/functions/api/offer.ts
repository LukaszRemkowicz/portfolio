// Live price for a project from its JSON offer endpoint (Project.price_source_url), in the
// shape of Starligner's payments/offer: { amount, currency, promotion?: { amount, ends_at } },
// amounts in cents. The stored price stays the fallback when the source fails.

export type LivePrice = { amount: string; currency: string };

const TTL_MS = 10 * 60 * 1000;
const TIMEOUT_MS = 2000;
// shortcut: per-isolate cache only, so a cold isolate fetches again; enough for one endpoint.
const cache = new Map<string, { at: number; price: LivePrice | null }>();

const cents = (v: unknown) => Number.isInteger(v) && (v as number) >= 0 ? (v as number) : null;

/** The price now: the running promotion's amount, else the regular one. Null if invalid. */
export function parseOffer(body: unknown, now = Date.now()): LivePrice | null {
  if (!body || typeof body !== "object") return null;
  const o = body as Record<string, unknown>;
  const currency = typeof o.currency === "string" ? o.currency.toUpperCase() : "";
  let amount = cents(o.amount);
  if (!/^[A-Z]{3}$/.test(currency) || amount === null) return null;
  const promo = o.promotion as Record<string, unknown> | null | undefined;
  const promoAmount = cents(promo?.amount);
  const endsAt = Date.parse(String(promo?.ends_at ?? ""));
  if (promoAmount !== null && endsAt > now) amount = promoAmount;
  return { amount: (amount / 100).toFixed(2), currency };
}

export async function livePrice(url: string, now = Date.now()): Promise<LivePrice | null> {
  const hit = cache.get(url);
  if (hit && now - hit.at < TTL_MS) return hit.price;
  let price: LivePrice | null = null;
  try {
    const res = await fetch(url, {
      headers: { accept: "application/json" },
      signal: AbortSignal.timeout(TIMEOUT_MS),
    });
    if (res.ok) price = parseOffer(await res.json(), now);
    else await res.body?.cancel();
  } catch (e) {
    console.warn(`offer: ${url} failed: ${e instanceof Error ? e.message : e}`);
  }
  cache.set(url, { at: now, price });
  return price;
}

export function clearOfferCacheForTests() {
  cache.clear();
}
