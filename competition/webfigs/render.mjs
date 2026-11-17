// Slide figures (fig.html, English and Korean) and the prototype's app screens, rendered with Playwright at 2x.
//   node competition/webfigs/render.mjs   (needs .bin/pw: Playwright + Chromium; Python 3 for two local servers)
import { createRequire } from 'node:module';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
const here = path.dirname(fileURLToPath(import.meta.url)), comp = path.dirname(here), root = path.dirname(comp);
const { chromium } = createRequire(path.join(root, '.bin/pw/package.json'))('playwright');
const serve = (dir, port) => spawn('python3', ['-m', 'http.server', String(port), '--bind', '127.0.0.1', '--directory', dir], { stdio: 'ignore' });
const servers = [serve(comp, 8791), serve(path.join(root, 'output/ryry_viz'), 8792)];
await new Promise(r => setTimeout(r, 1200));
const b = await chromium.launch();
try {
  for (const [fig, w, h] of [['results', 1200, 560], ['perjob', 1200, 336]]) for (const lang of ['en', 'ko']) {
    const p = await b.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 2 });
    await p.goto(`http://127.0.0.1:8791/webfigs/fig.html?fig=${fig}&lang=${lang}`); await p.waitForFunction(() => window.READY);
    const out = path.join(comp, lang === 'ko' ? 'figs/ko' : 'figs/slides', `slide_${fig}.png`);
    await p.locator('#fig').screenshot({ path: out }); console.log(out); await p.close();
  }
  // the prototype itself (Version 1 page): its header, and its per-job card; framed as a browser window by frame.py
  const p = await b.newPage({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 2 });
  await p.goto('http://127.0.0.1:8792/', { waitUntil: 'networkidle' }); await p.evaluate(() => document.fonts.ready); await p.waitForTimeout(1200);
  await p.locator('header').first().screenshot({ path: path.join(here, 'raw_header.png') });
  const card = p.locator('#c-jobs').locator('xpath=..'); await card.scrollIntoViewIfNeeded(); await p.waitForTimeout(2500);
  await card.screenshot({ path: path.join(here, 'raw_perjob.png'), animations: 'disabled' });
  console.log('app shots');
} finally { await b.close(); servers.forEach(s => s.kill()); }
