import puppeteer from 'puppeteer';
import { mkdir } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
const __dirname = dirname(fileURLToPath(import.meta.url));
const outDir = resolve(__dirname, '..', 'screenshots', 'real');
await mkdir(outDir, { recursive: true });

// 2026-05-29 起改多 KB 布局：/kb/<slug>/...
const urls = [
  ['home', '/'],
  ['kb-example-dt',     '/kb/example-dt/'],
  ['kb-example-vqla',      '/kb/example-agent/'],
  ['kb-research-workspace',      '/kb/research-workspace/'],
  ['kb-chemistry',          '/kb/chemistry/'],
  ['paper-artgs',           '/kb/example-dt/wiki/papers/artgs/'],
  ['paper-example-vqla',   '/kb/example-agent/wiki/papers/example-vqla/'],
  ['methods-paper-reading', '/kb/research-workspace/methods/paper-critical-reading/'],
];
const browser = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox'] });
for (const [name, url] of urls) {
  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900 });
  await page.goto('http://localhost:4321' + url, { waitUntil: 'networkidle0', timeout: 30000 });
  await new Promise(r => setTimeout(r, 1200));
  await page.screenshot({ path: resolve(outDir, name + '.png'), fullPage: false });
  console.log('saved', name);
  await page.close();
}
await browser.close();
