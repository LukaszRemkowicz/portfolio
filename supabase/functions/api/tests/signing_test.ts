import { assert, assertEquals, assertFalse } from "@std/assert";
import { sign, signedParams, validateSigned } from "../signing.ts";

const KEY = "unit-test-key";
const NOW = 1_800_000_000;

Deno.test("sign: HMAC-SHA256 hex of 'id:expiry' (known vector)", async () => {
  // python: hmac.new(b"unit-test-key", b"slug:1800003600", sha256).hexdigest()
  const s = await sign(KEY, "slug", 1_800_003_600);
  assertEquals(s, "a494cab6426cf701fee59544cdec5881477c0792d479ca975c6e22e58540f1f0");
  assertEquals(s, await sign(KEY, "slug", 1_800_003_600));
  assert(s !== (await sign(KEY, "slug", 1_800_003_601)));
});

Deno.test("signedParams uses now + expiration", async () => {
  const { s, e } = await signedParams(KEY, "slug", 3600, NOW);
  assertEquals(e, NOW + 3600);
  assertEquals(s, await sign(KEY, "slug", e));
});

Deno.test("validateSigned: valid link passes", async () => {
  const { s, e } = await signedParams(KEY, "slug", 3600, NOW);
  assert(await validateSigned(KEY, "slug", s, String(e), NOW));
});

Deno.test("validateSigned: expired link fails, boundary second still valid", async () => {
  const { s, e } = await signedParams(KEY, "slug", 3600, NOW);
  assert(await validateSigned(KEY, "slug", s, String(e), e));
  assertFalse(await validateSigned(KEY, "slug", s, String(e), e + 1));
});

Deno.test("validateSigned: tampering fails (id, expiry, signature, key)", async () => {
  const { s, e } = await signedParams(KEY, "slug", 3600, NOW);
  assertFalse(await validateSigned(KEY, "other-slug", s, String(e), NOW));
  assertFalse(await validateSigned(KEY, "slug", s, String(e + 1), NOW));
  assertFalse(
    await validateSigned(KEY, "slug", s.replace(/.$/, s.endsWith("0") ? "1" : "0"), String(e), NOW),
  );
  assertFalse(await validateSigned("another-key", "slug", s, String(e), NOW));
  assertFalse(await validateSigned(KEY, "slug", s.slice(0, 63), String(e), NOW));
});

Deno.test("validateSigned: garbage input and missing key fail closed", async () => {
  const { s } = await signedParams(KEY, "slug", 3600, NOW);
  assertFalse(await validateSigned(KEY, "slug", s, "abc", NOW));
  assertFalse(await validateSigned(KEY, "slug", s, "", NOW));
  assertFalse(await validateSigned("", "slug", s, String(NOW + 10), NOW));
});
