// Rasterize SVG figures at 6x for the slides: node svg2png.mjs <figdir> <outdir> name...
// shortcut: Playwright is only installed in the session scratchpad (pw/); copy this file next to its node_modules to run it
import { chromium } from 'playwright';
const [FIG, OUT, ...names] = process.argv.slice(2);
const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 2000, height: 2000 }, deviceScaleFactor: 6 });
for (const n of names) {
  await p.goto(`file://${FIG}/${n}.svg`);
  await p.locator('svg').first().screenshot({ path: `${OUT}/${n}.png`, omitBackground: false });
  console.log(n);
}
await b.close();
