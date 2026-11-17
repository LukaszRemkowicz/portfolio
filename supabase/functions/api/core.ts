// core app: SettingsView (LandingPageSettingsSerializer) and the health check.
import { db } from "./db.ts";
import { detail, json } from "./http.ts";

export const health = () => json({ status: "healthy" });

const TOTAL_TIME_SAFETY_BUFFER_HOURS = 2;

/** LandingPageSettingsSerializer.get_total_time_spent: rounds half up on the fraction. */
export function totalTimeSpent(sumHours: number | null): number {
  const total = (sumHours ?? 0) + TOTAL_TIME_SAFETY_BUFFER_HOURS;
  const whole = Math.trunc(total);
  return total - whole < 0.5 ? whole : whole + 1;
}

type Meteors = Record<string, unknown>;

/** GET /v1/settings/ (one round trip: settings + meteors config joined, total in parallel) */
export async function settings(): Promise<Response> {
  const sql = db();
  const [[row], [{ total }]] = await Promise.all([
    sql<
      ({
        programming_enabled: boolean;
        contact_form_enabled: boolean;
        travel_highlights_enabled: boolean;
        lastimages_enabled: boolean;
        shop_enabled: boolean;
        meteors_found: boolean;
      } & Meteors)[]
    >`
      select s.programming_enabled, s.contact_form_enabled, s.travel_highlights_enabled,
        s.lastimages_enabled, s.shop_enabled, m.id is not null as meteors_found,
        m.random_stars_shooting, m.bolid_chance, m.bolid_interval, m.star_path_range,
        m.bolid_path_range, m.star_streak_range, m.bolid_streak_range, m.star_duration_range,
        m.bolid_duration_range, m.star_opacity_range, m.bolid_opacity_range, m.smoke_opacity_range
      from core_landingpagesettings s
      left join astrophotography_meteorsmainpageconfig m on m.id = s.meteors_id
      order by s.id desc limit 1`,
    sql<{ total: number | null }[]>`
      select sum(calculated_exposure_hours) as total from astrophotography_astroimage`,
  ]);
  if (!row) return detail("Landing Page Settings not initialized.", 404);
  const m = row;
  const meteors: Meteors | null = row.meteors_found
    ? {
      randomShootingStars: m.random_stars_shooting,
      bolidChance: m.bolid_chance,
      bolidMinInterval: m.bolid_interval,
      starPathRange: m.star_path_range,
      bolidPathRange: m.bolid_path_range,
      starStreakRange: m.star_streak_range,
      bolidStreakRange: m.bolid_streak_range,
      starDurationRange: m.star_duration_range,
      bolidDurationRange: m.bolid_duration_range,
      starOpacityRange: m.star_opacity_range,
      bolidOpacityRange: m.bolid_opacity_range,
      smokeOpacityRange: m.smoke_opacity_range,
    }
    : null;
  return json({
    programming: row.programming_enabled,
    contactForm: row.contact_form_enabled,
    travelHighlights: row.travel_highlights_enabled,
    lastimages: row.lastimages_enabled,
    shop: row.shop_enabled,
    total_time_spent: totalTimeSpent(total),
    meteors,
  });
}
