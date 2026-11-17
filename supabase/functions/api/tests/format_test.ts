import { assertEquals } from "@std/assert";
import {
  adventureDate,
  dateSlug,
  drfDateTime,
  parseDateSlug,
  previousDay,
  storyPreview,
} from "../format.ts";

// PostgreSQL daterange upper bound is the first day AFTER the range.
Deno.test("adventureDate: single day (upper = lower + 1 or open)", () => {
  assertEquals(adventureDate("2026-03-14", "2026-03-15"), "14 Mar 2026");
  assertEquals(adventureDate("2026-03-14", null), "14 Mar 2026");
});

Deno.test("adventureDate: same month range", () => {
  assertEquals(adventureDate("2026-08-10", "2026-08-19"), "10 - 18 Aug 2026");
});

Deno.test("adventureDate: same year, different months", () => {
  assertEquals(adventureDate("2026-01-20", "2026-02-06"), "20 Jan - 5 Feb 2026");
});

Deno.test("adventureDate: different years and month-boundary upper bound", () => {
  assertEquals(adventureDate("2025-01-20", "2026-01-06"), "20 Jan 2025 - 5 Jan 2026");
  assertEquals(adventureDate("2025-12-30", "2026-01-01"), "30 - 31 Dec 2025");
  assertEquals(adventureDate("2026-01-30", "2026-01-31"), "30 Jan 2026");
});

Deno.test("adventureDate: no lower bound", () => {
  assertEquals(adventureDate(null, "2026-01-01"), null);
});

Deno.test("previousDay crosses month/year/leap boundaries", () => {
  assertEquals(previousDay("2026-03-01"), "2026-02-28");
  assertEquals(previousDay("2024-03-01"), "2024-02-29");
  assertEquals(previousDay("2026-01-01"), "2025-12-31");
});

Deno.test("dateSlug / parseDateSlug", () => {
  assertEquals(dateSlug("2026-08-10"), "aug2026");
  assertEquals(parseDateSlug("aug2026"), ["2026-08-01", "2026-09-01"]);
  assertEquals(parseDateSlug("DEC2025"), ["2025-12-01", "2026-01-01"]);
  assertEquals(parseDateSlug("zzz2026"), null);
  assertEquals(parseDateSlug("augxx"), null);
  assertEquals(parseDateSlug("explore"), null);
});

Deno.test("drfDateTime: Europe/Warsaw offsets (CET/CEST) and microseconds", () => {
  const winter = Date.UTC(2026, 10, 10, 11, 0, 50) / 1000;
  assertEquals(drfDateTime(`${winter}.811028`), "2026-11-10T12:00:50.811028+01:00");
  const summer = Date.UTC(2026, 8, 8, 14, 40, 39) / 1000;
  assertEquals(drfDateTime(`${summer}.03`), "2026-09-08T16:40:39.030000+02:00");
  assertEquals(drfDateTime(`${summer}`), "2026-09-08T16:40:39+02:00");
});

Deno.test("drfDateTime: UTC renders as Z", () => {
  assertEquals(drfDateTime("0", "UTC"), "1970-01-01T00:00:00Z");
});

Deno.test("storyPreview: short stays, long cut at word boundary with ellipsis", () => {
  assertEquals(storyPreview("short"), "short");
  const long = "word ".repeat(40).trim();
  const out = storyPreview(long);
  assertEquals(out.endsWith("word..."), true);
  assertEquals(Array.from(out).length <= 153, true);
});

Deno.test("storyPreview counts code points (emoji) like Python len()", () => {
  const s = "🌠".repeat(150);
  assertEquals(storyPreview(s), s);
  assertEquals(storyPreview(s + "x"), s + "...");
});
