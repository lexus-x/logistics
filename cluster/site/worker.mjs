// Password gate for the results page (personal data: customer stop locations). Every request runs here first;
// files are served only with a valid signed session cookie. The password is the PASSWORD secret.
const DAYS = 30;
const enc = new TextEncoder();

async function sign(secret, msg) {
  const key = await crypto.subtle.importKey("raw", enc.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  return [...new Uint8Array(await crypto.subtle.sign("HMAC", key, enc.encode(msg)))].map(b => b.toString(16).padStart(2, "0")).join("");
}

function same(a, b) {  // constant-time string compare
  const x = enc.encode(a), y = enc.encode(b);
  let d = x.length ^ y.length;
  for (let i = 0; i < Math.max(x.length, y.length); i++) d |= (x[i] ?? 0) ^ (y[i] ?? 0);
  return d === 0;
}

async function authed(req, secret) {
  const m = /(?:^|;\s*)session=(\d+)\.([0-9a-f]{64})/.exec(req.headers.get("cookie") || "");
  return !!m && Number(m[1]) > Date.now() / 1000 && same(m[2], await sign(secret, `v1:${m[1]}`));
}

const SECURE = {
  "Cache-Control": "private, no-store",
  "X-Robots-Tag": "noindex, nofollow",
  "Referrer-Policy": "no-referrer",
  "X-Content-Type-Options": "nosniff",
  "Content-Security-Policy": "frame-ancestors 'none'",
};

function login(failed, status = 401) {
  const html = `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Delivery planning results</title><meta name="robots" content="noindex">
<style>
@font-face { font-family: Barlow; font-weight: 400; src: url(/fonts/barlow-400.woff2) format("woff2"); }
@font-face { font-family: "Barlow Condensed"; font-weight: 600; src: url(/fonts/barlow-condensed-600.woff2) format("woff2"); }
* { box-sizing: border-box; }
body { margin: 0; min-height: 100vh; display: grid; place-items: center; background: #1437a6; color: #101a33; font: 16px/1.5 Barlow, system-ui, sans-serif; padding: 16px; }
body::after { content: ""; position: fixed; left: 0; right: 0; bottom: 24px; height: 4px; background: repeating-linear-gradient(90deg, #e8be84 0 28px, transparent 28px 52px); }
form { background: #fff; border-radius: 16px; padding: 32px; width: min(420px, 100%); box-shadow: 0 20px 60px rgba(5, 15, 50, .35); }
h1 { font: 600 34px/1.05 "Barlow Condensed", Barlow, sans-serif; margin: 0 0 8px; }
p { color: #4a5470; margin: 0 0 20px; }
label { display: block; font-size: 14px; color: #4a5470; margin-bottom: 6px; }
input { width: 100%; font: inherit; padding: 10px 12px; border: 1px solid #c5cbd8; border-radius: 8px; }
input:focus-visible, button:focus-visible { outline: 2px solid #1437a6; outline-offset: 2px; }
button { margin-top: 16px; width: 100%; font: 600 16px Barlow, system-ui, sans-serif; color: #fff; background: #1437a6; border: 0; border-radius: 8px; padding: 11px; cursor: pointer; }
button:hover { background: #0f2b8a; }
.err { color: #b42318; font-size: 14px; margin: 10px 0 0; }
</style></head><body>
<form method="post" action="/login">
  <h1>Planning Ryry's bulky deliveries</h1>
  <p>Results of the delivery planning model. This page shows customer locations, so it is password protected.</p>
  <label for="pw">Password</label>
  <input id="pw" name="password" type="password" autocomplete="current-password" required autofocus>
  ${failed ? '<p class="err" role="alert">That password doesn\'t match. Try again.</p>' : ""}
  <button type="submit">Open the results</button>
</form></body></html>`;
  return new Response(html, { status, headers: { "Content-Type": "text/html; charset=utf-8", ...SECURE } });
}

export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    if (!env.PASSWORD) return new Response("Not configured yet", { status: 503 });
    if (url.pathname === "/login" && req.method === "POST") {
      const form = await req.formData().catch(() => null);
      // shortcut: no rate limit on guesses; the password is long and random, add Cloudflare rate limiting if it gets shared widely
      if (!form || !same(String(form.get("password") || ""), env.PASSWORD)) return login(true);
      const exp = Math.floor(Date.now() / 1000) + DAYS * 86400;
      const cookie = `session=${exp}.${await sign(env.PASSWORD, `v1:${exp}`)}; Path=/; Max-Age=${DAYS * 86400}; HttpOnly; Secure; SameSite=Lax`;
      return new Response(null, { status: 303, headers: { Location: "/", "Set-Cookie": cookie, ...SECURE } });
    }
    if (url.pathname === "/logout")
      return new Response(null, { status: 303, headers: { Location: "/", "Set-Cookie": "session=; Path=/; Max-Age=0; HttpOnly; Secure; SameSite=Lax", ...SECURE } });
    if (url.pathname.startsWith("/fonts/")) return env.ASSETS.fetch(req);  // public typefaces (OFL), used by the sign-in page
    if (!(await authed(req, env.PASSWORD))) return url.pathname === "/" || url.pathname === "/index.html" ? login(false) : new Response("Sign in first", { status: 401, headers: SECURE });
    const res = await env.ASSETS.fetch(req);
    const h = new Headers(res.headers);
    for (const [k, v] of Object.entries(SECURE)) h.set(k, v);
    return new Response(res.body, { status: res.status, headers: h });
  },
};
