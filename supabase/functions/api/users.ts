// users app: UserViewSet.profile (UserSerializer + ProfileSerializer).
import { db } from "./db.ts";
import { type Ctx, detail, json } from "./http.ts";
import { translateField } from "./i18n.ts";
import { loadTranslations } from "./loaders.ts";
import { loadVariants, variantPayload } from "./media.ts";

/** GET /v1/profile/ (singleton user: first by pk; everything loads in one round trip) */
export async function profile(ctx: Ctx): Promise<Response> {
  const sql = db();
  const firstUser = () => sql`select id from users_user order by id limit 1`;
  const userQuery = sql<
    {
      id: number;
      first_name: string;
      last_name: string;
      is_active: boolean;
      contact_email: string;
    }[]
  >`select id::int as id, first_name, last_name, is_active, contact_email
    from users_user order by id limit 1`;
  const profilesQuery = sql<
    {
      id: number;
      type: string;
      is_active: boolean;
      github_url: string;
      linkedin_url: string;
      astrobin_url: string;
      fb_url: string;
      ig_url: string;
    }[]
  >`select id::int as id, type, is_active, github_url, linkedin_url, astrobin_url, fb_url, ig_url
    from users_profile where user_id = (${firstUser()})
    order by type, id`; // DRF reads them via the unique (user, type) index, i.e. type order
  const [[user], profiles, userTr, profileTr, variants] = await Promise.all([
    userQuery,
    profilesQuery,
    loadTranslations("users_user_translation", firstUser(), ["short_description", "bio"]),
    loadTranslations(
      "users_profile_translation",
      sql`select id from users_profile where user_id = (${firstUser()})`,
      ["title", "specific_bio"],
    ),
    loadVariants("users", "user", sql`select id::text from users_user order by id limit 1`),
  ]);
  if (!user) return detail("No user found.", 404);
  if (!user.is_active) return detail("User is not active.", 404);
  const tr = userTr.get(String(user.id)) ?? [];
  const mine = variants.get(String(user.id)) ?? [];
  const image = (source: string) =>
    variantPayload(
      mine,
      `${source}__original_format`,
      2560,
      ctx.cfg.publicDomain,
      "original_format",
    );
  return json({
    first_name: user.first_name,
    last_name: user.last_name,
    short_description: translateField(tr, "short_description", ctx.lang, ctx.active),
    bio: translateField(tr, "bio", ctx.lang, ctx.active),
    contact_email: user.contact_email,
    avatar: image("avatar"),
    about_me_image: image("about_me_image"),
    about_me_image2: image("about_me_image2"),
    profiles: profiles.map((p) => {
      const rows = profileTr.get(String(p.id)) ?? [];
      return {
        type: p.type,
        is_active: p.is_active,
        title: translateField(rows, "title", ctx.lang, ctx.active),
        specific_bio: translateField(rows, "specific_bio", ctx.lang, ctx.active),
        github_url: p.github_url,
        linkedin_url: p.linkedin_url,
        astrobin_url: p.astrobin_url,
        fb_url: p.fb_url,
        ig_url: p.ig_url,
      };
    }),
  });
}
