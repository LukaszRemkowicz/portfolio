import { assertEquals } from "@std/assert";
import postgres from "postgres";
import { and, galleryFilter, or } from "../astrophotography.ts";
import { db, setDbForTests } from "../db.ts";

// Render a postgres.js fragment to text ($n for bound values) without a connection.
// deno-lint-ignore no-explicit-any
function render(q: any, n = { i: 0 }): string {
  return q.strings.reduce((acc: string, s: string, i: number) => {
    if (i >= q.args.length) return acc + s;
    const a = q.args[i];
    return acc + s + (a && a.strings ? render(a, n) : `$${++n.i}`);
  }, "").replace(/\s+/g, " ").trim();
}

setDbForTests(postgres({ host: "localhost", max: 1 })); // never connects: fragments only
const sql = db();

Deno.test("and/or parenthesise every operand", () => {
  assertEquals(render(and([sql`a`, sql`b`])), "((true) and (a)) and (b)");
  assertEquals(render(or([sql`a`, sql`b`])), "((false) or (a)) or (b)");
});

Deno.test("and([cat, or([A, B])]) keeps the or grouped", () => {
  const out = render(and([sql`cat = ${1}`, or([sql`x`, sql`y`])]));
  assertEquals(
    out,
    "((true) and (cat = $1)) and (((false) or (x)) or (y))",
  );
});

Deno.test("galleryFilter: travel + filter composes as (filter) and (A or B)", () => {
  const { where } = galleryFilter(
    new URL("http://h/v1/astroimages/?travel=spain&filter=Landscape"),
  );
  assertEquals(
    render(where),
    "((true) and (a.celestial_object = $1)) and " +
      "(((false) or (upper(pt1.name) like upper($2))) or (p1.country = $3))",
  );
});
