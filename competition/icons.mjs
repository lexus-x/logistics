// Rasterize the Tabler outline icons (figs/icons/svg, MIT, figs/icons/LICENSE-tabler-icons.txt) in the deck's colours:
//   figs/icons/<name>_<colour>.png, 384 px, transparent.
// shortcut: Playwright is only installed in .bin/pw; run as  cp competition/icons.mjs .bin/pw/ && node .bin/pw/icons.mjs competition/figs/icons
import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';

const DIR = path.resolve(process.argv[2]);
const COLOURS = { white: '#ffffff', green: '#0e5a3f', asphalt: '#3a4148' };
const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 200, height: 200 }, deviceScaleFactor: 4 });
for (const f of fs.readdirSync(path.join(DIR, 'svg')).filter((f) => f.endsWith('.svg'))) {
  const src = fs.readFileSync(path.join(DIR, 'svg', f), 'utf8').replace('width="24"', 'width="96"').replace('height="24"', 'height="96"');
  for (const [name, hex] of Object.entries(COLOURS)) {
    await p.setContent(`<body style="margin:0;background:transparent">${src.replace(/currentColor/g, hex)}</body>`);
    await p.locator('svg').first().screenshot({ path: path.join(DIR, `${f.slice(0, -4)}_${name}.png`), omitBackground: true });
  }
}
await b.close();
console.log('icons done');
