// Latency: cold first request + median of 5 warm runs per endpoint, baseline vs function.
// Each run uses a fresh `cb` so DRF's DB response cache is bypassed (comparable work).
const B = Deno.env.get("BASELINE_URL") ?? "http://localhost:8000";
const F = Deno.env.get("FUNCTION_URL") ?? "http://localhost:8001";
const SECRET = Deno.env.get("API_ORIGIN_SECRET") ?? "";
const paths = [
  "/health",
  "/v1/settings/",
  "/v1/profile/?lang=en",
  "/v1/background/",
  "/v1/categories/",
  "/v1/tags/?lang=en",
  "/v1/astroimages/?lang=en&limit=15",
  "/v1/astroimages/latest/?lang=en",
  "/v1/travel-highlights/?lang=en",
];
const t = async (o: string, p: string) => {
  const s = performance.now();
  const r = await fetch(`${o}${p}${p.includes("?") ? "&" : "?"}cb=${crypto.randomUUID()}`, {
    headers: { "x-origin-secret": SECRET },
  });
  await r.text();
  return performance.now() - s;
};
const med = (a: number[]) => [...a].sort((x, y) => x - y)[Math.floor(a.length / 2)];
console.log("path | baseline median ms | function median ms | function first ms");
for (const p of paths) {
  const first = await t(F, p);
  const b: number[] = [], f: number[] = [];
  for (let i = 0; i < 5; i++) {
    b.push(await t(B, p));
    f.push(await t(F, p));
  }
  console.log(`${p} | ${med(b).toFixed(0)} | ${med(f).toFixed(0)} | ${first.toFixed(0)}`);
}
