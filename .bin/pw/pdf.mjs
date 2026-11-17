import { chromium } from 'playwright';
const [src, out] = process.argv.slice(2);
const b = await chromium.launch();
const p = await b.newPage();
await p.goto('file://' + src, { waitUntil: 'networkidle' });
await p.evaluate(() => document.fonts.ready);
await p.pdf({ path: out, format: 'A4', printBackground: true, preferCSSPageSize: true });
await b.close();
