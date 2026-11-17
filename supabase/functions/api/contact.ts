import { isIP } from "node:net";
import { ownerHtml, senderHtml } from "./contact_emails.ts";
import { db } from "./db.ts";
import { detail, json } from "./http.ts";
import { sendWithRetry } from "./mail.ts";

const MAX_READ = 64 * 1024; // hard cap while reading; above this we never buffer more
const MAX_PAYLOAD = 10000; // Django _check_payload_size

const bad = (body: unknown) => json(body, 400);

/** Body as bytes, or null once it exceeds MAX_READ. */
async function readCapped(req: Request): Promise<Uint8Array | null> {
  if (Number(req.headers.get("content-length")) > MAX_READ) return null;
  if (!req.body) return new Uint8Array();
  const chunks: Uint8Array[] = [];
  let n = 0;
  for await (const c of req.body) {
    n += c.length;
    if (n > MAX_READ) return null; // leaving the loop cancels the stream
    chunks.push(c);
  }
  const out = new Uint8Array(n);
  let o = 0;
  for (const c of chunks) (out.set(c, o), o += c.length);
  return out;
}

function clientIp(req: Request): string {
  // The Supabase gateway overwrites X-Real-IP/X-Forwarded-For with the connecting peer (the
  // Worker's Cloudflare egress), so the Worker sends the visitor in X-Visitor-IP. Trusted only
  // because the router already checked the origin secret.
  const visitor = req.headers.get("x-visitor-ip")?.trim() ?? "";
  if (isIP(visitor)) return visitor;
  const real = req.headers.get("x-real-ip")?.trim() ?? "";
  if (isIP(real)) return real;
  const fwd = req.headers.get("x-forwarded-for")?.split(",")[0].trim() ?? "";
  return isIP(fwd) ? fwd : "unknown";
}

type Obj = Record<string, unknown>;
const isObj = (v: unknown): v is Obj => typeof v === "object" && v !== null && !Array.isArray(v);

// Django EmailValidator (user part + domain part, case-insensitive).
const USER_RE =
  // deno-lint-ignore no-control-regex
  /^([-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*|"([\x01-\x08\x0b\x0c\x0e-\x1f!#-\[\]-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")$/i;
const DOMAIN_RE = /^((?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+)(?:[A-Z0-9-]{2,63}(?<!-))$/i;
// shortcut: no IP-literal domains ([1.2.3.4]) and no punycode retry for IDN domains; add if needed.
function validEmail(v: string): boolean {
  const at = v.lastIndexOf("@");
  return at > 0 && USER_RE.test(v.slice(0, at)) && DOMAIN_RE.test(v.slice(at + 1));
}

type Res = { err: string } | { ok: string } | undefined;
/** DRF CharField.to_internal_value + trim. */
function char(body: Obj, key: string, max: number | null, required = true): Res {
  if (!(key in body)) return required ? { err: "This field is required." } : undefined;
  const v = body[key];
  if (v === null) return { err: "This field may not be null." };
  if (typeof v === "boolean" || typeof v === "object") return { err: "Not a valid string." };
  const s = String(v).trim();
  if (s.includes("\0")) return { err: "Null characters are not allowed." };
  if (s === "" && key !== "website") return { err: "This field may not be blank." };
  if (max !== null && [...s].length > max) {
    return { err: `Ensure this field has no more than ${max} characters.` };
  }
  return { ok: s };
}

const pyType = (v: unknown) =>
  Array.isArray(v)
    ? "list"
    : typeof v === "string"
    ? "str"
    : typeof v === "boolean"
    ? "bool"
    : Number.isInteger(v)
    ? "int"
    : "float";

/** ModelSerializer semantics: first error per field, keys in field order. */
export function validate(
  body: unknown,
): { errors: Record<string, string[]> } | {
  clean: Record<"name" | "email" | "subject" | "message", string>;
} {
  if (body === null) return { errors: { non_field_errors: ["No data provided"] } };
  if (!isObj(body)) {
    return {
      errors: {
        non_field_errors: [`Invalid data. Expected a dictionary, but got ${pyType(body)}.`],
      },
    };
  }
  const errors: Record<string, string[]> = {};
  const clean: Record<string, string> = {};
  const rules: [string, number | null, (s: string) => string | undefined, boolean][] = [
    [
      "name",
      100,
      (s) => ([...s].length < 2 ? "Name must be at least 2 characters long." : undefined),
      true,
    ],
    ["email", 254, (s) => (validEmail(s) ? undefined : "Enter a valid email address."), true],
    [
      "subject",
      200,
      (s) => ([...s].length < 5 ? "Subject must be at least 5 characters long." : undefined),
      true,
    ],
    [
      "message",
      null,
      (s) => {
        const n = [...s].length;
        return n < 10
          ? "Message must be at least 10 characters long."
          : n > 5000
          ? "Message is too long (max 5000 characters)."
          : undefined;
      },
      true,
    ],
    ["website", null, (s) => (s ? "Bot detected." : undefined), false],
  ];
  for (const [key, max, extra, required] of rules) {
    const r = char(body, key, max, required);
    if (!r) continue;
    const err = "err" in r ? r.err : extra(r.ok);
    if (err) errors[key] = [err];
    else if ("ok" in r) clean[key] = key === "email" ? r.ok.toLowerCase() : r.ok;
  }
  return Object.keys(errors).length ? { errors } : { clean } as never;
}

const maskEmail = (e: string) => `${e.slice(0, 2)}***@${e.slice(e.lastIndexOf("@") + 1)}`;

/** `YYYY-MM-DD HH:MM:SS CET|CEST` in Europe/Warsaw. */
export function warsawTime(d: Date): string {
  const p = Object.fromEntries(
    new Intl.DateTimeFormat("en-CA", {
      timeZone: "Europe/Warsaw",
      hourCycle: "h23",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      timeZoneName: "shortOffset",
    }).formatToParts(d).map((x) => [x.type, x.value]),
  );
  const zone = p.timeZoneName === "GMT+2" ? "CEST" : "CET";
  return `${p.year}-${p.month}-${p.day} ${p.hour}:${p.minute}:${p.second} ${zone}`;
}

type Saved = { id: number; name: string; email: string; subject: string; message: string };

/** Owner notification first, then sender confirmation; failures are logged only. */
export async function sendEmails(m: Saved): Promise<void> {
  const env = Object.fromEntries(
    ["RESEND_API_KEY", "CONTACT_EMAIL", "CONTACT_FROM_EMAIL", "PROJECT_OWNER", "SITE_DOMAIN"]
      .map((k) => [k, Deno.env.get(k) ?? ""]),
  );
  const missing = Object.keys(env).filter((k) => !env[k]);
  if (missing.length) {
    console.error(`contact mail not sent, missing env: ${missing.join(", ")}`);
    return;
  }
  const from = `${env.PROJECT_OWNER} <${env.CONTACT_FROM_EMAIL}>`;
  const ok1 = await sendWithRetry({
    from,
    to: [env.CONTACT_EMAIL],
    subject: `New Contact Message: ${m.subject}`,
    reply_to: m.email,
    key: `contact-${m.id}-owner`,
    html: ownerHtml({
      portfolio_owner: env.PROJECT_OWNER,
      subject: m.subject,
      sender_name: m.name,
      sender_email: m.email,
      message: m.message,
      received_at: warsawTime(new Date()),
      message_id: m.id,
    }),
  });
  let social = { ig_url: "", fb_url: "", astrobin_url: "" };
  try {
    const [row] = await db()`
      select ig_url, fb_url, astrobin_url from users_profile
      where user_id = (select id from users_user order by id limit 1) and type = 'ASTRO'
      order by id limit 1`;
    if (row) {
      social = {
        ig_url: row.ig_url ?? "",
        fb_url: row.fb_url ?? "",
        astrobin_url: row.astrobin_url ?? "",
      };
    }
  } catch {
    console.warn("contact mail: profile lookup failed, sending without social links");
  }
  const ok2 = await sendWithRetry({
    from,
    to: [m.email],
    subject: "Message Received - Astrophotography Portfolio",
    reply_to: env.CONTACT_EMAIL,
    key: `contact-${m.id}-sender`,
    html: senderHtml({
      portfolio_owner: env.PROJECT_OWNER,
      gallery_url: `https://${env.SITE_DOMAIN}/astrophotography`,
      instagram_url: social.ig_url,
      facebook_url: social.fb_url,
      astrobin_url: social.astrobin_url,
      copyright_year: new Date().getFullYear(),
    }),
  });
  console.log(
    `contact ${m.id}: owner mail ${ok1 ? "sent" : "FAILED"}, sender mail ${
      ok2 ? "sent" : "FAILED"
    } (${maskEmail(m.email)})`,
  );
}

/** Run after the response: EdgeRuntime keeps the isolate alive; elsewhere just fire. */
function background(p: Promise<unknown>): void {
  const safe = p.catch(() => console.error("contact mail task failed"));
  // deno-lint-ignore no-explicit-any
  const rt = (globalThis as any).EdgeRuntime;
  if (rt?.waitUntil) rt.waitUntil(safe);
}

export async function submit(req: Request): Promise<Response> {
  const sql = db();
  const [settings] = await sql`
    select contact_form_enabled from core_landingpagesettings order by id desc limit 1`;
  if (!settings?.contact_form_enabled) {
    console.warn("Contact form request blocked - form disabled.");
    return bad({ message: "Contact form is currently disabled. Please try again later." });
  }

  const bytes = await readCapped(req);
  if (!bytes) return detail("Request payload too large.", 413);
  const text = new TextDecoder().decode(bytes);
  let body: unknown;
  try {
    // Empty body: DRF treats it as {} (required-field errors), not a parse error.
    body = text.trim() === "" ? {} : JSON.parse(text);
  } catch (e) {
    return bad({ detail: `JSON parse error - ${(e as Error).message}` });
  }

  const ip = clientIp(req);
  let email: string | null = null;
  if (isObj(body) && (typeof body.email === "string" || typeof body.email === "number")) {
    email = String(body.email).toLowerCase().trim() || null;
  }
  try {
    const allowed = await sql.begin(
      "read write",
      async (tx) => (await tx`select api_private.contact_throttle(${ip}, ${email}) as ok`)[0]?.ok,
    );
    if (allowed === false) {
      console.warn(`contact throttled: ${ip}`);
      return new Response(
        JSON.stringify({
          detail: "You've submitted too many messages. Please wait 1 hour to send another one.",
        }),
        {
          status: 429,
          headers: { "content-type": "application/json", "retry-after": "3600" },
        },
      );
    }
  } catch {
    console.warn("contact throttle unavailable, allowing request");
  }

  if (bytes.length > MAX_PAYLOAD) {
    console.warn(`Request too large: ${bytes.length} bytes from ${ip}`);
    return detail("Request payload too large.", 413);
  }

  const v = validate(body);
  if ("errors" in v) return bad(v.errors);
  const { name, email: mail, subject, message } = v.clean;

  const id = await sql.begin(
    "read write",
    async (tx) =>
      (await tx`select api_private.contact_submit(${name}, ${mail}, ${subject}, ${message}) as id`)[
        0
      ]
        ?.id,
  );
  if (id === null || id === undefined) {
    return detail("Please wait before submitting another message with the same subject.", 429);
  }
  const num = Number(id);
  console.log(`contact ${num} saved from ${ip} (${maskEmail(mail)})`);
  background(sendEmails({ id: num, name, email: mail, subject, message }));
  return json({ message: "Thank you! Your message has been sent successfully.", id: num }, 201);
}
