// programming app: Project list (unpaginated; gated by LandingPageSettings.programming_enabled).
import { db } from "./db.ts";
import { type Ctx, detail, json } from "./http.ts";
import { getTranslation } from "./i18n.ts";
import { loadTranslations } from "./loaders.ts";
import { drfDateTime } from "./format.ts";
import { loadVariants, variantPayload } from "./media.ts";
import { type LivePrice, livePrice } from "./offer.ts";

/** FE renders the label: null (none), free, or paid with a 2-decimal amount. */
function priceTag(
  i: { pricing: string; price: string | null; currency: string },
  live: LivePrice | null = null,
) {
  if (i.pricing === "free") return { type: "free" };
  if (i.pricing === "paid" && live) return { type: "paid", ...live };
  if (i.pricing === "paid" && i.price !== null) {
    return { type: "paid", amount: Number(i.price).toFixed(2), currency: i.currency };
  }
  return null;
}

/** GET /v1/projects/ */
export async function projects(ctx: Ctx): Promise<Response> {
  const sql = db();
  const [flags] = await sql<{ programming_enabled: boolean }[]>`
    select programming_enabled from core_landingpagesettings order by id desc limit 1`;
  if (!flags?.programming_enabled) return detail("Projects are currently not available.", 404);

  const items = await sql<
    {
      id: string;
      technologies: string;
      github_url: string;
      live_url: string;
      pricing: string;
      price: string | null;
      currency: string;
      price_source_url: string;
      created_epoch: string;
    }[]
  >`select id::text as id, technologies, github_url, live_url, pricing,
      price::text as price, currency, price_source_url,
      extract(epoch from created_at)::text as created_epoch
    from programming_project where is_active order by created_at desc`;
  const ids = items.map((i) => i.id);
  const [tr, variants, live] = await Promise.all([
    loadTranslations("programming_project_translation", ids, ["name", "description", "badge"]),
    loadVariants("programming", "project", ids),
    Promise.all(
      items.map((i) =>
        i.pricing === "paid" && i.price_source_url ? livePrice(i.price_source_url) : null
      ),
    ),
  ]);
  const lang = ctx.lang ?? "";
  return json({
    projects: items.map((i, n) => ({
      id: i.id,
      name: getTranslation(tr.get(i.id) ?? [], "name", lang),
      description: getTranslation(tr.get(i.id) ?? [], "description", lang),
      badge: getTranslation(tr.get(i.id) ?? [], "badge", lang),
      technologies: i.technologies.split(",").map((t) => t.trim()).filter(Boolean),
      github_url: i.github_url,
      live_url: i.live_url,
      price_tag: priceTag(i, live[n]),
      created_at: drfDateTime(i.created_epoch),
      ...variantPayload(variants.get(i.id) ?? [], "thumbnail", 800, ctx.cfg.publicDomain),
    })),
  });
}
