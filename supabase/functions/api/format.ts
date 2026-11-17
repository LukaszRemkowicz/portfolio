const TZ = "Europe/Warsaw"; // settings.TIME_ZONE

const pad = (n: number, w = 2) => String(n).padStart(w, "0");
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/**
 * DRF DateTimeField output for a timestamptz selected as `extract(epoch ...)::text`
 * (keeps microseconds, which JS Date would lose): local ISO-8601 in Europe/Warsaw.
 */
export function drfDateTime(epoch: string, tz = TZ): string {
  const [secStr, frac = ""] = epoch.split(".");
  const micro = frac.padEnd(6, "0").slice(0, 6);
  const sec = Number(secStr);
  const parts = Object.fromEntries(
    new Intl.DateTimeFormat("en-CA", {
      timeZone: tz,
      hourCycle: "h23",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    }).formatToParts(new Date(sec * 1000)).map((p) => [p.type, Number(p.value)]),
  );
  const offsetMin = Math.round(
    (Date.UTC(parts.year, parts.month - 1, parts.day, parts.hour, parts.minute, parts.second) -
      sec * 1000) / 60000,
  );
  const sign = offsetMin < 0 ? "-" : "+";
  const abs = Math.abs(offsetMin);
  const offset = offsetMin === 0 ? "Z" : `${sign}${pad(Math.floor(abs / 60))}:${pad(abs % 60)}`;
  const fraction = micro === "000000" ? "" : `.${micro}`;
  return `${parts.year}-${pad(parts.month)}-${pad(parts.day)}T${pad(parts.hour)}:${
    pad(parts.minute)
  }:${pad(parts.second)}${fraction}${offset}`;
}

type YMD = { y: number; m: number; d: number };

export function parseDate(iso: string): YMD {
  const [y, m, d] = iso.split("-").map(Number);
  return { y, m, d };
}

/** `date - 1 day` for a YYYY-MM-DD string. */
export function previousDay(iso: string): string {
  const t = new Date(`${iso}T00:00:00Z`);
  t.setUTCDate(t.getUTCDate() - 1);
  return t.toISOString().slice(0, 10);
}

const dmy = ({ y, m, d }: YMD) => `${d} ${MONTHS[m - 1]} ${y}`;

/**
 * MainPageLocationSerializer.get_adventure_date. `lower`/`upper` are the PostgreSQL daterange
 * bounds as YYYY-MM-DD (upper is the first day AFTER the range).
 */
export function adventureDate(lower: string | null, upper: string | null): string | null {
  if (!lower) return null;
  const lo = parseDate(lower);
  const hi = upper ? parseDate(previousDay(upper)) : null;
  if (!hi || (lo.y === hi.y && lo.m === hi.m && lo.d === hi.d)) return dmy(lo);
  if (lo.y === hi.y) {
    if (lo.m === hi.m) return `${lo.d} - ${hi.d} ${MONTHS[lo.m - 1]} ${lo.y}`;
    return `${lo.d} ${MONTHS[lo.m - 1]} - ${dmy(hi)}`;
  }
  return `${dmy(lo)} - ${dmy(hi)}`;
}

/** MainPageLocation.date_slug: `aug2026`. */
export function dateSlug(lower: string): string {
  const { y, m } = parseDate(lower);
  return `${MONTHS[m - 1].toLowerCase()}${pad(y, 4)}`;
}

/** MainPageLocation._parse_date_slug: `jan2026` -> [first day, first day of next month) or null. */
export function parseDateSlug(slug: string): [string, string] | null {
  const m = MONTHS.findIndex((x) => x.toLowerCase() === slug.slice(0, 3).toLowerCase()) + 1;
  const yearStr = slug.slice(3);
  if (!m || !/^\s*[+-]?\d+\s*$/.test(yearStr)) return null;
  const y = Number.parseInt(yearStr, 10);
  if (y < 1 || y > 9999) return null;
  const [ny, nm] = m === 12 ? [y + 1, 1] : [y, m + 1];
  if (ny > 9999) return null;
  return [`${pad(y, 4)}-${pad(m)}-01`, `${pad(ny, 4)}-${pad(nm)}-01`];
}

/** Truncate to 150 code points at a word boundary (MainPageLocation.get_story_preview). */
export function storyPreview(story: string, maxLength = 150): string {
  const chars = Array.from(story);
  if (chars.length <= maxLength) return story;
  const cut = chars.slice(0, maxLength).join("");
  const i = cut.lastIndexOf(" ");
  return (i < 0 ? cut : cut.slice(0, i)) + "...";
}
