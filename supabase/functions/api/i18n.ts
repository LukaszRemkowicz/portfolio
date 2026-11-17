// Language selection and translation fallback, mirroring TranslationService.get_translation,
// TranslatedSerializerMixin.translate_fields and parler's active-language lookup.
import { COUNTRIES } from "./countries.ts";

export type Lang = "en" | "pl";
export const DEFAULT_LANG: Lang = "en";
export const FAILED_PREFIX = "[TRANSLATION FAILED]";

/** One translation row (`<model>_translation`), `language_code` plus the translated columns. */
export type TrRow = { language_code: string } & Record<string, string | null>;

/** Language Django ends up with for `?lang=`; unsupported codes behave like the default. */
export function activeLang(lang: string | null): Lang {
  const l = (lang ?? "").toLowerCase();
  return l === "pl" ? "pl" : DEFAULT_LANG;
}

const isBlankHtml = (v: string) => v.trim() === "<p>&nbsp;</p>";

/** TranslationService._read_translation */
function read(rows: TrRow[], field: string, lang: string): string {
  const row = rows.find((r) => r.language_code === lang);
  if (!row) return "";
  const value = row[field] ?? "";
  if (value.startsWith(FAILED_PREFIX) || isBlankHtml(value)) return "";
  return value;
}

/** TranslationService.get_translation: requested -> default -> (optionally) any language. */
export function getTranslation(
  rows: TrRow[],
  field: string,
  lang: string,
  { allowAny = true }: { allowAny?: boolean } = {},
): string {
  const requested = lang || DEFAULT_LANG;
  const value = read(rows, field, requested);
  if (value) return value;
  if (requested !== DEFAULT_LANG) {
    const fallback = read(rows, field, DEFAULT_LANG);
    if (fallback) return fallback;
  }
  if (!allowAny) return "";
  for (const row of rows) {
    if (row.language_code !== requested && row.language_code !== DEFAULT_LANG) {
      const fallback = read(rows, field, row.language_code);
      if (fallback) return fallback;
    }
  }
  return "";
}

/** parler attribute access: active language row, else the default row; null when absent. */
export function parlerValue(rows: TrRow[], field: string, active: Lang): string | null {
  const row = rows.find((r) => r.language_code === active) ??
    rows.find((r) => r.language_code === DEFAULT_LANG);
  return row?.[field] ?? null;
}

/** TranslatedSerializerMixin.translate_fields for a single field (null stays null without lang). */
export function translateField(
  rows: TrRow[],
  field: string,
  lang: string | null,
  active: Lang,
): string | null {
  if (lang) {
    const val = getTranslation(rows, field, lang);
    return isBlankHtml(val) ? "" : val;
  }
  const value = parlerValue(rows, field, active);
  if (value === null) return null;
  return value.startsWith(FAILED_PREFIX) || isBlankHtml(value) ? "" : value;
}

const NAMES = new Map(COUNTRIES.map(([code, en, pl]) => [code, { en, pl }]));

/** django-countries `Country.name` in the active language. */
export function countryName(code: string | null, active: Lang): string {
  return code ? NAMES.get(code)?.[active] ?? "" : "";
}

/** Gallery `travel` filter lookups (English names, as django-countries yields them). */
export const COUNTRY_CODES = new Map(COUNTRIES.map(([code]) => [code.toLowerCase(), code]));
export const COUNTRY_BY_NAME = new Map(COUNTRIES.map(([code, en]) => [en.toLowerCase(), code]));
