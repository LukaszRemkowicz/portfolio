export type Mail = {
  from: string;
  to: string[];
  subject: string;
  html: string;
  reply_to?: string;
  /** Resend Idempotency-Key, e.g. `contact-12-owner`. */
  key: string;
};

/** Thrown by `send`; `retry` false means a permanent (non-429 4xx) rejection. */
export class MailError extends Error {
  constructor(msg: string, readonly retry: boolean) {
    super(msg);
  }
}

/** One attempt against Resend (Supabase blocks SMTP ports). */
async function send(m: Mail): Promise<void> {
  const { key, ...body } = m;
  let res: Response;
  try {
    res = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: {
        "authorization": `Bearer ${Deno.env.get("RESEND_API_KEY")}`,
        "content-type": "application/json",
        "idempotency-key": key,
      },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(3000),
    });
  } catch (e) {
    throw new MailError(`network: ${(e as Error).name}`, true);
  }
  await res.body?.cancel();
  if (!res.ok) throw new MailError(`resend ${res.status}`, res.status === 429 || res.status >= 500);
}

// Indirection so tests can stub sending and skip the backoff wait.
export const mailer = { send, sleep: (ms: number) => new Promise<void>((r) => setTimeout(r, ms)) };

const BACKOFF_MS = [500, 1500];

/** Up to 3 attempts on network error / 429 / 5xx; true when delivered. Never throws. */
export async function sendWithRetry(m: Mail): Promise<boolean> {
  for (let attempt = 0; attempt <= BACKOFF_MS.length; attempt++) {
    try {
      await mailer.send(m);
      return true;
    } catch (e) {
      const retry = !(e instanceof MailError) || e.retry;
      const last = attempt === BACKOFF_MS.length;
      console.warn(
        `mail ${m.key} attempt ${attempt + 1} failed: ${
          e instanceof MailError ? e.message : "error"
        }`,
      );
      if (!retry || last) return false;
      await mailer.sleep(BACKOFF_MS[attempt]);
    }
  }
  return false;
}
