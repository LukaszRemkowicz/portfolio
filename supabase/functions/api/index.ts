import { missingEnv } from "./config.ts";
import { handler } from "./router.ts";

const missing = missingEnv();
if (missing.length) console.error(`Missing required env: ${missing.join(", ")}`);

// Supabase Edge Functions call Deno.serve(handler); PORT is only for local runs.
const port = Deno.env.get("PORT");
if (port) Deno.serve({ port: Number(port) }, handler);
else Deno.serve(handler);
