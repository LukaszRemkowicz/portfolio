// Mirrors ImageVariantModelMixin.get_variant_candidates / get_variant_payload.
import { db, type Frag } from "./db.ts";

export type Variant = {
  role: string;
  width: number;
  height: number;
  mime_type: string;
  file: string;
};
export type Candidate = { url: string; width: number; height: number; mime_type: string };
export type VariantPayload = {
  fallback_image: Candidate | null;
  variants: Record<string, Candidate[]>;
};

/** Public URL as django-storages builds it with a custom domain (filepath_to_uri quoting). */
export function publicUrl(domain: string, name: string): string {
  const path = name.replace(/\\/g, "/").split("/").map(encodeURIComponent).join("/");
  return `https://${domain}/${path}`;
}

export function candidates(variants: Variant[], role: string, domain: string): Candidate[] {
  return variants
    .filter((v) => v.role === role && v.file)
    .sort((a, b) => a.width - b.width)
    .map((v) => ({
      url: publicUrl(domain, v.file),
      width: v.width,
      height: v.height,
      mime_type: v.mime_type,
    }));
}

export function variantPayload(
  variants: Variant[],
  role: string,
  fallbackWidth: number,
  domain: string,
  responseRole?: string,
): VariantPayload {
  const list = candidates(variants, role, domain);
  const fallback = list.find((c) => c.width === fallbackWidth) ?? list.at(-1) ?? null;
  return { fallback_image: fallback, variants: { [responseRole ?? role]: list } };
}

/** Variants of generic-relation owners, keyed by owner id. */
export async function loadVariants(
  app: string,
  model: string,
  ownerIds: string[] | Frag,
): Promise<Map<string, Variant[]>> {
  const out = new Map<string, Variant[]>();
  if (Array.isArray(ownerIds) && !ownerIds.length) return out;
  const sql = db();
  const owners = Array.isArray(ownerIds)
    ? sql`v.object_id = any(${ownerIds}::text[])`
    : sql`v.object_id in (${ownerIds})`;
  const rows = await sql<(Variant & { owner: string })[]>`
    select v.object_id as owner, v.role, v.width, v.height, v.mime_type, v.file
    from core_imagevariant v
    join django_content_type ct on ct.id = v.content_type_id
    where ct.app_label = ${app} and ct.model = ${model}
      and ${owners} and v.file <> ''
    order by v.role, v.width`;
  for (const r of rows) {
    const list = out.get(r.owner) ?? [];
    list.push(r);
    out.set(r.owner, list);
  }
  return out;
}
