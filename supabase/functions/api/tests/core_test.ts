import { assertEquals } from "@std/assert";
import { totalTimeSpent } from "../core.ts";
import { loadConfig, missingEnv, REQUIRED_ENV } from "../config.ts";
import { makeCtx } from "../http.ts";

Deno.test("totalTimeSpent: +2h buffer, fraction >= .5 rounds up", () => {
  assertEquals(totalTimeSpent(null), 2);
  assertEquals(totalTimeSpent(34.4), 36);
  assertEquals(totalTimeSpent(34.5), 37);
  assertEquals(totalTimeSpent(34.9), 37);
});

Deno.test("makeCtx: /api prefix stripped; base comes only from API_PUBLIC_BASE_URL", () => {
  const cfg = loadConfig((k) =>
    k === "API_PUBLIC_BASE_URL" ? "https://p.supabase.co/functions/v1/api/" : undefined
  );
  const deployed = makeCtx(new Request("https://evil.example/api/v1/tags/?lang=pl"), cfg);
  assertEquals(deployed.path, "/v1/tags/");
  assertEquals(deployed.base, "https://p.supabase.co/functions/v1/api");
  assertEquals(deployed.lang, "pl");
  const local = makeCtx(new Request("http://localhost:8001/v1/tags/"), cfg);
  assertEquals(local.path, "/v1/tags/");
  assertEquals(local.lang, null);
});

Deno.test("missingEnv lists names only", () => {
  const all = Object.fromEntries(REQUIRED_ENV.map((k) => [k, "secret-value"]));
  assertEquals(missingEnv((k) => all[k]), []);
  assertEquals(missingEnv((k) => (k === "MEDIA_SIGNING_KEY" ? undefined : all[k])), [
    "MEDIA_SIGNING_KEY",
  ]);
});

Deno.test("makeCtx: last lang value wins like Django QueryDict", () => {
  const ctx = makeCtx(
    new Request("http://h/v1/tags/?lang=en&lang=pl"),
    loadConfig(() => undefined),
  );
  assertEquals(ctx.lang, "pl");
});
