import { assertEquals } from "@std/assert";
import {
  activeLang,
  countryName,
  FAILED_PREFIX,
  getTranslation,
  parlerValue,
  translateField,
  type TrRow,
} from "../i18n.ts";

const rows = (...r: [string, string | null][]): TrRow[] =>
  r.map(([language_code, name]) => ({ language_code, name }));

Deno.test("activeLang: pl (any case) is pl, everything else is the default", () => {
  assertEquals(activeLang("pl"), "pl");
  assertEquals(activeLang("PL"), "pl");
  assertEquals(activeLang("de"), "en");
  assertEquals(activeLang(null), "en");
});

Deno.test("getTranslation: requested language wins", () => {
  assertEquals(getTranslation(rows(["en", "Sun"], ["pl", "Słońce"]), "name", "pl"), "Słońce");
});

Deno.test("getTranslation: falls back to default when requested is empty or missing", () => {
  assertEquals(getTranslation(rows(["en", "Sun"], ["pl", ""]), "name", "pl"), "Sun");
  assertEquals(getTranslation(rows(["en", "Sun"]), "name", "pl"), "Sun");
  assertEquals(getTranslation(rows(["en", "Sun"], ["pl", null]), "name", "pl"), "Sun");
});

Deno.test("getTranslation: failure marker and empty CKEditor paragraph count as missing", () => {
  assertEquals(
    getTranslation(rows(["en", "Sun"], ["pl", `${FAILED_PREFIX} boom`]), "name", "pl"),
    "Sun",
  );
  assertEquals(getTranslation(rows(["en", "Sun"], ["pl", "<p>&nbsp;</p>"]), "name", "pl"), "Sun");
});

Deno.test("getTranslation: any-language fallback only when allowed", () => {
  const r = rows(["en", ""], ["de", "Sonne"]);
  assertEquals(getTranslation(r, "name", "pl"), "Sonne");
  assertEquals(getTranslation(r, "name", "pl", { allowAny: false }), "");
  assertEquals(getTranslation([], "name", ""), "");
});

Deno.test("getTranslation: empty language means the default language", () => {
  assertEquals(getTranslation(rows(["en", "Sun"], ["pl", "Słońce"]), "name", ""), "Sun");
});

Deno.test("translateField: lang given -> translation service rules", () => {
  const r = rows(["en", "Sun"], ["pl", "<p>&nbsp;</p>"]);
  assertEquals(translateField(r, "name", "pl", "pl"), "Sun");
  assertEquals(translateField(rows(["en", "Sun"], ["pl", "Słońce"]), "name", "pl", "pl"), "Słońce");
});

Deno.test("translateField: no lang -> parler value with failure markers stripped", () => {
  assertEquals(translateField(rows(["en", "Sun"], ["pl", "Słońce"]), "name", null, "en"), "Sun");
  assertEquals(translateField(rows(["en", `${FAILED_PREFIX} x`]), "name", null, "en"), "");
  assertEquals(translateField(rows(["en", "<p>&nbsp;</p>"]), "name", null, "en"), "");
});

Deno.test("parlerValue: active row, else default row", () => {
  assertEquals(parlerValue(rows(["en", "Sun"]), "name", "pl"), "Sun");
  assertEquals(parlerValue(rows(["en", "Sun"], ["pl", ""]), "name", "pl"), "");
});

Deno.test("translateField: no lang and no translation row/value -> null (parler returns None)", () => {
  assertEquals(translateField([], "name", null, "en"), null);
  assertEquals(translateField(rows(["en", null]), "name", null, "en"), null);
  assertEquals(translateField([], "name", "pl", "pl"), "");
});

Deno.test("countryName: en/pl names, blank for unknown", () => {
  assertEquals(countryName("ES", "en"), "Spain");
  assertEquals(countryName("ES", "pl"), "Hiszpania");
  assertEquals(countryName(null, "en"), "");
  assertEquals(countryName("ZZ", "en"), "");
});
