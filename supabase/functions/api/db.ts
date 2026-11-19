import tls from "node:tls";
import postgres from "postgres";

// postgres.js flushes buffered writes from a setImmediate timer and cancels it after a direct
// flush. Under Deno's node compat a cancelled timer can still fire with the buffer already sent,
// so the driver writes null to the TLS socket; the throw kills the isolate (every in-flight
// request gets 503). Nothing is pending in that case, so the null write is dropped.
const tlsWrite = tls.TLSSocket.prototype.write;
tls.TLSSocket.prototype.write = function (this: tls.TLSSocket, ...args: unknown[]) {
  if (args[0] === null) {
    console.warn("db: dropped null write from a stale postgres.js write timer");
    return true;
  }
  return tlsWrite.apply(this, args as Parameters<typeof tlsWrite>);
};

let sql: postgres.Sql | undefined;

/** A composable SQL fragment (also usable as a subquery). */
export type Frag = postgres.PendingQuery<postgres.Row[]>;

// Read-only role (portfolio_api) over a direct SQL connection; the Django tables are not
// exposed through the Data API. Prepared statements: a parameterised query costs one round trip
// (two without) and concurrent queries are pipelined; needs a direct or session-pooler connection.
let override: postgres.Sql | undefined;
/** Test seam: replace the connection with a stub. */
export function setDbForTests(fake: unknown): void {
  override = fake as postgres.Sql;
}

export function db(): postgres.Sql {
  if (override) return override;
  return sql ??= postgres({
    host: Deno.env.get("API_DB_HOST"),
    port: Number(Deno.env.get("API_DB_PORT") ?? 5432),
    database: Deno.env.get("API_DB_NAME"),
    username: Deno.env.get("API_DB_USER"),
    password: Deno.env.get("API_DB_PASSWORD"),
    // "disable" only for the local docker Postgres (infra/scripts/run_local_api.sh).
    ssl: Deno.env.get("API_DB_SSL") === "disable" ? false : "require",
    max: 1, // one connection per isolate: direct when deployed, session pooler (5432) locally
    prepare: true,
    idle_timeout: 20,
    connect_timeout: 10,
    onnotice: () => {},
  });
}
