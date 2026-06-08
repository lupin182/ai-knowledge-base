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
  ['kb-redacted-topic',     '/kb/redacted-topic/'],
  ['kb-redacted-project',      '/kb/redacted-project/'],
  ['kb-research-notes',      '/kb/research-notes/'],
  ['kb-chemistry',          '/kb/chemistry/'],
  ['paper-artgs',           '/kb/redacted-topic/wiki/papers/artgs/'],
  ['paper-redacted-project',   '/kb/redacted-project/wiki/papers/redacted-project/'],
  ['methods-paper-reading', '/kb/research-notes/methods/paper-critical-reading/'],
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
