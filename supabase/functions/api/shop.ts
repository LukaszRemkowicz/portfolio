// shop app: ShopProductViewSet.list (unpaginated; gated by LandingPageSettings.shop_enabled).
import { db } from "./db.ts";
import { type Ctx, detail, json } from "./http.ts";
import { getTranslation } from "./i18n.ts";
import { loadTranslations } from "./loaders.ts";
import { drfDateTime } from "./format.ts";
import { loadVariants, variantPayload } from "./media.ts";

/** GET /v1/shop/products/ */
export async function products(ctx: Ctx): Promise<Response> {
  const sql = db();
  const [flags] = await sql<{ shop_enabled: boolean }[]>`
    select shop_enabled from core_landingpagesettings order by id desc limit 1`;
  if (!flags?.shop_enabled) return detail("Shop is currently not available.", 404);

  const items = await sql<
    {
      id: string;
      price: string | null;
      currency: string;
      external_url: string;
      is_active: boolean;
      created_epoch: string;
    }[]
  >`select id::text as id, price::text as price, currency, external_url, is_active,
      extract(epoch from created_at)::text as created_epoch
    from shop_shopproduct where is_active order by created_at desc`;
  const [shop] = await sql<{ id: number }[]>`
    select id::int as id from shop_shopsettings order by id desc limit 1`;
  const [tr, variants, settingsTr, settingsVariants] = await Promise.all([
    loadTranslations("shop_shopproduct_translation", items.map((i) => i.id), [
      "title",
      "description",
    ]),
    loadVariants("shop", "shopproduct", items.map((i) => i.id)),
    shop
      ? loadTranslations("shop_shopsettings_translation", [shop.id], ["title", "description"])
      : Promise.resolve(new Map()),
    shop ? loadVariants("shop", "shopsettings", [String(shop.id)]) : Promise.resolve(new Map()),
  ]);
  const lang = ctx.lang ?? "";
  const head = shop
    ? {
      title: getTranslation(settingsTr.get(String(shop.id)) ?? [], "title", lang),
      description: getTranslation(settingsTr.get(String(shop.id)) ?? [], "description", lang),
      ...variantPayload(
        settingsVariants.get(String(shop.id)) ?? [],
        "background",
        2560,
        ctx.cfg.publicDomain,
      ),
    }
    : { title: "", description: "" };
  return json({
    ...head,
    products: items.map((i) => ({
      id: i.id,
      title: getTranslation(tr.get(i.id) ?? [], "title", lang),
      description: getTranslation(tr.get(i.id) ?? [], "description", lang),
      price: i.price,
      currency: i.currency,
      external_url: i.external_url,
      is_active: i.is_active,
      created_at: drfDateTime(i.created_epoch),
      ...variantPayload(variants.get(i.id) ?? [], "thumbnail", 560, ctx.cfg.publicDomain),
    })),
  });
}
