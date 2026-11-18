import { assertEquals, assertThrows } from "@std/assert";
import tls from "node:tls";
import "../db.ts";

Deno.test("TLS write drops the stale null write and passes everything else through", () => {
  const write = tls.TLSSocket.prototype.write;
  assertEquals(write.call({} as tls.TLSSocket, null as never), true);
  // Real data still reaches the original stream write (which rejects this fake socket).
  assertThrows(() => write.call({} as tls.TLSSocket, "data"));
});
