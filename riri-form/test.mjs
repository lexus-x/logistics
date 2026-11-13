// Self-check for the worker, no network: node test.mjs
import assert from "node:assert/strict";
import { webcrypto } from "node:crypto";
import worker from "./src/index.mjs";

globalThis.crypto ??= webcrypto; // Node 18 has no global crypto

async function call(method, path, { body = "", length } = {}) {
  const saved = new Map();
  const headers = new Headers(length === undefined ? {} : { "content-length": String(length) });
  const req = { method, url: `http://x${path}`, headers, body, text: async () => body };
  const res = await worker.fetch(req, { ANSWERS: { put: async (k, v) => saved.set(k, v) } });
  return { status: res.status, text: await res.text(), saved };
}

let r = await call("PUT", "/api/file", { body: "abc", length: 3 });
assert.equal(r.status, 200);
assert.match(r.text, /^file\//);
assert.equal(r.saved.get(r.text), "abc");

assert.equal((await call("PUT", "/api/file", { body: "abc" })).status, 411);
r = await call("PUT", "/api/file", { body: "abc", length: 25_000_001 });
assert.equal(r.status, 413);
assert.equal(r.saved.size, 0);
assert.equal((await call("GET", "/api/file")).status, 404);
assert.equal((await call("GET", "/file/anything")).status, 404);

const answer = JSON.stringify({ other: "hello", files: [{ key: "file/x", name: "a.xlsx" }] });
r = await call("POST", "/api/answer", { body: answer });
assert.equal(r.status, 200);
assert.deepEqual([...r.saved.values()], [answer]);

assert.equal((await call("POST", "/api/answer", { body: "nope" })).status, 400);
assert.equal((await call("POST", "/api/answer", { body: "[1]" })).status, 400);
assert.equal((await call("POST", "/api/answer", { body: "null" })).status, 400);
r = await call("POST", "/api/answer", { body: JSON.stringify({ a: "x".repeat(100001) }) });
assert.equal(r.status, 413);
assert.equal(r.saved.size, 0);

console.log("ok");
