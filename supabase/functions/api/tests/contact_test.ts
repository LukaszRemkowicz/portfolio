import { assert, assertEquals } from "@std/assert";
import { REQUIRED_ENV } from "../config.ts";
import { setDbForTests } from "../db.ts";
import { type Mail, mailer, MailError } from "../mail.ts";
import { warsawTime } from "../contact.ts";
import { senderHtml } from "../contact_emails.ts";
import { handler, ORIGIN_SECRET_HEADER } from "../router.ts";

const URL_ = "http://h/api/v1/contact/";
const MAIL_ENV: Record<string, string> = {
  RESEND_API_KEY: "k",
  CONTACT_EMAIL: "owner@x.test",
  CONTACT_FROM_EMAIL: "kontakt@x.test",
  PROJECT_OWNER: "Owner",
  SITE_DOMAIN: "x.test",
};
const GOOD = {
  name: " Ann ",
  email: " Ann@Example.COM ",
  subject: "Hello there",
  message: "Line one\r\nline two <b>x</b>",
};

let enabled: boolean | null;
let throttle: () => boolean;
let submitId: number | null;
let modes: string[];
let throttleParams: unknown[];
let submitParams: unknown[];
let mails: Mail[];
let sendImpl: (m: Mail) => Promise<void>;
let profile: Record<string, string>[];
let sleeps: number;

function setup(env: Record<string, string> = MAIL_ENV) {
  for (const k of REQUIRED_ENV) Deno.env.set(k, "x");
  Deno.env.set("API_ORIGIN_SECRET", "s");
  Deno.env.set("API_PUBLIC_BASE_URL", "https://p");
  Deno.env.set("MEDIA_SIGNING_KEY", "k");
  for (const k of Object.keys(MAIL_ENV)) Deno.env.delete(k);
  for (const [k, v] of Object.entries(env)) Deno.env.set(k, v);
  enabled = true;
  throttle = () => true;
  submitId = 7;
  modes = [];
  throttleParams = [];
  submitParams = [];
  mails = [];
  profile = [];
  sleeps = 0;
  sendImpl = (m) => {
    mails.push(m);
    return Promise.resolve();
  };
  mailer.send = (m) => sendImpl(m);
  mailer.sleep = () => {
    sleeps++;
    return Promise.resolve();
  };
  const run = (strings: TemplateStringsArray, ...p: unknown[]) => {
    const t = strings.join("?");
    if (t.includes("contact_form_enabled")) {
      return Promise.resolve(enabled === null ? [] : [{ contact_form_enabled: enabled }]);
    }
    if (t.includes("contact_throttle")) {
      throttleParams = p;
      return Promise.resolve([{ ok: throttle() }]);
    }
    if (t.includes("contact_submit")) {
      submitParams = p;
      return Promise.resolve([{ id: submitId }]);
    }
    if (t.includes("users_profile")) return Promise.resolve(profile);
    return Promise.resolve([]);
  };
  setDbForTests(Object.assign(run, {
    begin: (mode: string, fn: (tx: unknown) => unknown) => {
      modes.push(mode);
      return Promise.resolve(fn(run));
    },
  }));
}

const post = (body: BodyInit | null, headers: Record<string, string> = {}) =>
  handler(
    new Request(URL_, {
      method: "POST",
      body,
      headers: { [ORIGIN_SECRET_HEADER]: "s", "x-real-ip": "1.2.3.4", ...headers },
    }),
  );
const postJson = (b: unknown, h?: Record<string, string>) => post(JSON.stringify(b), h);
const tick = () => new Promise((r) => setTimeout(r, 0));

Deno.test("contact: routing 405s", async () => {
  setup();
  const h = { [ORIGIN_SECRET_HEADER]: "s" };
  const g = await handler(new Request(URL_, { headers: h }));
  assertEquals(g.status, 405);
  assertEquals(await g.json(), { detail: 'Method "GET" not allowed.' });
  const p = await handler(new Request("http://h/api/v1/settings/", { method: "POST", headers: h }));
  assertEquals(p.status, 405);
});

Deno.test("contact: kill switch off or no row", async () => {
  for (const e of [false, null]) {
    setup();
    enabled = e;
    const r = await postJson(GOOD);
    assertEquals(r.status, 400);
    assertEquals(await r.json(), {
      message: "Contact form is currently disabled. Please try again later.",
    });
    assertEquals(modes.length, 0);
  }
});

Deno.test("contact: throttle false -> 429 with Retry-After; params and mode", async () => {
  setup();
  throttle = () => false;
  const r = await postJson(GOOD);
  assertEquals(r.status, 429);
  assertEquals(r.headers.get("retry-after"), "3600");
  assertEquals((await r.json()).detail.startsWith("You've submitted too many"), true);
  assertEquals(modes, ["read write"]);
  assertEquals(throttleParams, ["1.2.3.4", "ann@example.com"]);
});

Deno.test("contact: ip fallbacks and throwing throttle", async () => {
  setup();
  await postJson(GOOD, { "x-real-ip": "", "x-forwarded-for": "not-ip" });
  assertEquals(throttleParams[0], "unknown");
  await postJson(GOOD, { "x-real-ip": "bad", "x-forwarded-for": "2001:db8::1, 9.9.9.9" });
  assertEquals(throttleParams[0], "2001:db8::1");
  await postJson(GOOD, { "x-visitor-ip": "5.6.7.8" }); // wins over gateway-set X-Real-IP
  assertEquals(throttleParams[0], "5.6.7.8");
  await postJson(GOOD, { "x-visitor-ip": "nope" });
  assertEquals(throttleParams[0], "1.2.3.4");
  throttle = () => {
    throw new Error("db down");
  };
  const r = await postJson(GOOD);
  assertEquals(r.status, 201);
});

Deno.test("contact: oversize body -> 413 after throttle; hard cap skips throttle", async () => {
  setup();
  const r = await postJson({ ...GOOD, message: "x".repeat(10001) });
  assertEquals(r.status, 413);
  assertEquals(await r.json(), { detail: "Request payload too large." });
  assertEquals(modes, ["read write"]);
  setup();
  const big = await post("x".repeat(70 * 1024));
  assertEquals(big.status, 413);
  assertEquals(modes.length, 0);
});

Deno.test("contact: validation errors", async () => {
  setup();
  let r = await postJson({});
  assertEquals(await r.json(), {
    name: ["This field is required."],
    email: ["This field is required."],
    subject: ["This field is required."],
    message: ["This field is required."],
  });
  assertEquals(Object.keys(await (await postJson({})).json()), [
    "name",
    "email",
    "subject",
    "message",
  ]);
  r = await postJson({
    name: "  ",
    email: "nope@",
    subject: "abcd",
    message: "x".repeat(5001),
    website: "bot",
  });
  assertEquals(await r.json(), {
    name: ["This field may not be blank."],
    email: ["Enter a valid email address."],
    subject: ["Subject must be at least 5 characters long."],
    message: ["Message is too long (max 5000 characters)."],
    website: ["Bot detected."],
  });
  r = await postJson({ ...GOOD, name: "A", message: "short", email: "a".repeat(250) + "@b.co" });
  assertEquals(await r.json(), {
    name: ["Name must be at least 2 characters long."],
    email: ["Ensure this field has no more than 254 characters."],
    message: ["Message must be at least 10 characters long."],
  });
  r = await postJson({ ...GOOD, name: null, subject: true, message: ["x"], website: "" });
  assertEquals(await r.json(), {
    name: ["This field may not be null."],
    subject: ["Not a valid string."],
    message: ["Not a valid string."],
  });
  r = await postJson({ ...GOOD, website: "x" });
  assertEquals(await r.json(), { website: ["Bot detected."] });
});

Deno.test("contact: body shapes", async () => {
  setup();
  assertEquals(await (await postJson([1])).json(), {
    non_field_errors: ["Invalid data. Expected a dictionary, but got list."],
  });
  assertEquals(await (await postJson(1.5)).json(), {
    non_field_errors: ["Invalid data. Expected a dictionary, but got float."],
  });
  assertEquals(await (await post("null")).json(), { non_field_errors: ["No data provided"] });
  const r = await post("{oops");
  assertEquals(r.status, 400);
  assert((await r.json()).detail.startsWith("JSON parse error - "));
});

Deno.test("contact: duplicate -> 429", async () => {
  setup();
  submitId = null;
  const r = await postJson(GOOD);
  assertEquals(r.status, 429);
  assertEquals(await r.json(), {
    detail: "Please wait before submitting another message with the same subject.",
  });
  assertEquals(mails.length, 0);
});

Deno.test("contact: success saves cleaned values and sends two mails", async () => {
  setup();
  profile = [{ ig_url: "https://ig", fb_url: "", astrobin_url: "" }];
  const r = await postJson({ ...GOOD, name: "<script>x</script>" });
  assertEquals(r.status, 201);
  assertEquals(await r.json(), {
    message: "Thank you! Your message has been sent successfully.",
    id: 7,
  });
  assertEquals(submitParams, [
    "<script>x</script>",
    "ann@example.com",
    "Hello there",
    "Line one\r\nline two <b>x</b>",
  ]);
  await tick();
  assertEquals(mails.length, 2);
  const [o, s] = mails;
  assertEquals(o.to, ["owner@x.test"]);
  assertEquals(o.from, "Owner <kontakt@x.test>");
  assertEquals(o.subject, "New Contact Message: Hello there");
  assertEquals(o.reply_to, "ann@example.com");
  assertEquals(o.key, "contact-7-owner");
  assert(!o.html.includes("<script>"));
  assert(o.html.includes("&lt;script&gt;x&lt;/script&gt;"));
  assert(o.html.includes("Line one<br>line two &lt;b&gt;x&lt;/b&gt;"));
  assertEquals(s.to, ["ann@example.com"]);
  assertEquals(s.subject, "Message Received - Astrophotography Portfolio");
  assertEquals(s.reply_to, "owner@x.test");
  assertEquals(s.key, "contact-7-sender");
  assert(s.html.includes("https://x.test/astrophotography"));
  assert(s.html.includes("https://ig") && !s.html.includes("Facebook"));
});

Deno.test("contact: mail failures never change the 201", async () => {
  setup();
  let n = 0;
  sendImpl = (m) => {
    n++;
    if (n <= 2) return Promise.reject(new Error("boom"));
    mails.push(m);
    return Promise.resolve();
  };
  assertEquals((await postJson(GOOD)).status, 201);
  await tick();
  await tick();
  assertEquals(n, 4); // owner: 2 failures + success; sender: success
  assertEquals(sleeps, 2);

  setup();
  sendImpl = () => Promise.reject(new MailError("resend 500", true));
  assertEquals((await postJson(GOOD)).status, 201);
  await tick();
  await tick();
  assertEquals(sleeps, 4); // 3 attempts each for owner and sender
  setup();
  let calls = 0;
  sendImpl = () => {
    calls++;
    return Promise.reject(new MailError("resend 422", false));
  };
  assertEquals((await postJson(GOOD)).status, 201);
  await tick();
  await tick();
  assertEquals(calls, 2); // no retry on permanent 4xx
});

Deno.test("contact: missing RESEND_API_KEY -> 201, nothing sent", async () => {
  const { RESEND_API_KEY: _, ...rest } = MAIL_ENV;
  setup(rest);
  assertEquals((await postJson(GOOD)).status, 201);
  await tick();
  assertEquals(mails.length, 0);
});

Deno.test("contact templates: social blocks, escaping and zone", () => {
  const base = {
    portfolio_owner: "O",
    gallery_url: "g",
    instagram_url: "",
    facebook_url: "",
    astrobin_url: "",
    copyright_year: 2026,
  };
  const none = senderHtml(base);
  assert(!/Instagram|Facebook|Astrobin|•/.test(none));
  const two = senderHtml({ ...base, instagram_url: "i", astrobin_url: "a" });
  assert(two.includes("Instagram") && two.includes("Astrobin") && two.includes("•"));
  assert(senderHtml({ ...base, portfolio_owner: `a"'&` }).includes("a&quot;&#x27;&amp;"));
  assertEquals(warsawTime(new Date("2026-01-15T10:00:00Z")), "2026-01-15 11:00:00 CET");
  assertEquals(warsawTime(new Date("2026-07-15T10:00:00Z")), "2026-07-15 12:00:00 CEST");
});
