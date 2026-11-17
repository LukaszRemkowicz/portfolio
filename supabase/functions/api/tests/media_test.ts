import { assertEquals } from "@std/assert";
import { publicUrl, type Variant, variantPayload } from "../media.ts";

const D = "media.example.com";
const v = (
  role: string,
  width: number,
  file = `images/thumbnail/${role}_${width}.webp`,
): Variant => ({
  role,
  width,
  height: width / 2,
  mime_type: "image/webp",
  file,
});

Deno.test("publicUrl quotes like filepath_to_uri", () => {
  assertEquals(publicUrl(D, "a b/ü~!*()'.webp"), `https://${D}/a%20b/%C3%BC~!*()'.webp`);
});

Deno.test("variantPayload: exact fallback width, candidates sorted by width", () => {
  const p = variantPayload(
    [v("thumbnail", 560), v("thumbnail", 320), v("detail", 1920)],
    "thumbnail",
    560,
    D,
  );
  assertEquals(p.fallback_image?.width, 560);
  assertEquals(p.variants.thumbnail.map((c) => c.width), [320, 560]);
  assertEquals(Object.keys(p.variants), ["thumbnail"]);
  assertEquals(p.fallback_image?.url, `https://${D}/images/thumbnail/thumbnail_560.webp`);
});

Deno.test("variantPayload: no exact width -> largest candidate", () => {
  const p = variantPayload([v("thumbnail", 320), v("thumbnail", 400)], "thumbnail", 560, D);
  assertEquals(p.fallback_image?.width, 400);
});

Deno.test("variantPayload: missing variants -> null fallback and empty list", () => {
  assertEquals(variantPayload([], "hero", 2560, D), {
    fallback_image: null,
    variants: { hero: [] },
  });
  assertEquals(variantPayload([v("hero", 960, "")], "hero", 2560, D).fallback_image, null);
});

Deno.test("variantPayload: response role renames the key (user images)", () => {
  const p = variantPayload(
    [v("avatar__original_format", 280)],
    "avatar__original_format",
    2560,
    D,
    "original_format",
  );
  assertEquals(Object.keys(p.variants), ["original_format"]);
  assertEquals(p.fallback_image?.width, 280);
});
