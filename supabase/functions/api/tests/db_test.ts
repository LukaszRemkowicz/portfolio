import { assertEquals } from "@std/assert";
import { Writable } from "node:stream";
import tls from "node:tls";
import "../db.ts";

Deno.test("TLS write drops the stale null write and forwards real data", () => {
  const written: string[] = [];
  // The guard delegates to the inherited stream write, so a plain Writable records what it gets.
  const sink = new Writable({
    write(chunk, _enc, cb) {
      written.push(String(chunk));
      cb();
    },
  });
  const write = tls.TLSSocket.prototype.write;
  assertEquals(write.call(sink as never, null as never), true);
  write.call(sink as never, "data");
  assertEquals(written, ["data"]);
});
