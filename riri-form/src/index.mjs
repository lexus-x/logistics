const MAX_FILE = 25_000_000; // KV's value limit is 25 MiB
const newId = () => `${new Date().toISOString()}-${crypto.randomUUID().slice(0, 8)}`;

// Static files in public/ are served first; only unmatched requests reach this.
export default {
  async fetch(req, env) {
    const path = new URL(req.url).pathname;

    if (req.method === "PUT" && path === "/api/file") {
      // No route reads files back, so an upload can't be opened from this site. That's why any file type is fine here.
      const size = Number(req.headers.get("content-length"));
      if (!size) return new Response("Length required", { status: 411 });
      if (size > MAX_FILE) return new Response("Too large", { status: 413 });
      const key = `file/${newId()}`;
      await env.ANSWERS.put(key, req.body); // streamed, so a big file doesn't hit the free plan's CPU limit
      return new Response(key);
    }

    if (req.method !== "POST" || path !== "/api/answer")
      return new Response("Not found", { status: 404 });
    const body = await req.text();
    if (body.length > 100000) return new Response("Too long", { status: 413 });
    let data;
    try { data = JSON.parse(body); } catch { return new Response("Bad request", { status: 400 }); }
    if (typeof data !== "object" || data === null || Array.isArray(data)) return new Response("Bad request", { status: 400 });
    // shortcut: no rate limit, the URL is unlisted; add one if junk shows up in KV
    await env.ANSWERS.put(newId(), body);
    return new Response("ok");
  },
};
