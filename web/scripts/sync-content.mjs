// Sync KB markdown content from repo root into web/src/content/docs/.
//
// 用法：node scripts/sync-content.mjs [--watch]
//
// 2026-05-29 起 KB 改成 multi-KB 布局：所有内容在 knowledge_bases/<slug>/。
// 本脚本自动枚举 knowledge_bases/ 下的每个子目录作为一个 KB，sync 到
// src/content/docs/kb/<slug>/，URL 模式 /kb/<slug>/<path>。
//
// 同步语义：one-way mirror（删 web 端有但 KB 端没有的）。
// 不处理 KB 根的 README.md（Astro 首页是手写的 index.astro）。
//
// 外部 mount（EXTERNAL_MOUNTS in server/.env）仍按原 URL 前缀（不带 /kb/）
// 同步到 web/src/content/docs/<prefix>/，例如 external-reports/。

import { promises as fs, watch as fsWatch } from 'node:fs';
import { dirname, resolve, relative, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const KB_ROOT = resolve(__dirname, '..', '..');
const ASTRO_CONTENT = resolve(__dirname, '..', 'src', 'content', 'docs');
const ASTRO_PUBLIC = resolve(__dirname, '..', 'public');
const KB_DIR = resolve(KB_ROOT, 'knowledge_bases');

// 自动枚举：knowledge_bases/ 下的每个目录就是一个 KB。
// 注意：OneDrive "Files On-Demand" 会把云端化的文件夹标成 ReparsePoint，
// Dirent.isDirectory() 在这种情况下返回 false。改用 fs.stat() 跟链。
async function discoverKBs() {
  try {
    const names = await fs.readdir(KB_DIR);
    const kbs = [];
    for (const name of names) {
      if (name.startsWith('.')) continue;
      try {
        const st = await fs.stat(resolve(KB_DIR, name));  // 跟链
        if (st.isDirectory()) kbs.push(name);
      } catch { /* skip 损坏 */ }
    }
    return kbs.sort();
  } catch {
    return [];
  }
}

// 解析 server/.env 里的 EXTERNAL_MOUNTS（跨盘挂载，例如 external-reports
// → F:/onedrive-ex-jason/.../cluster_sync/reports），把它们也 sync 进来。
async function readExternalMounts() {
  try {
    const envText = await fs.readFile(resolve(KB_ROOT, 'server', '.env'), 'utf-8');
    const m = envText.match(/^\s*EXTERNAL_MOUNTS\s*=\s*(.+)$/m);
    if (!m) return {};
    let json = m[1].trim();
    // 去掉可能的引号
    if ((json.startsWith('"') && json.endsWith('"')) || (json.startsWith("'") && json.endsWith("'"))) {
      json = json.slice(1, -1);
    }
    return JSON.parse(json);
  } catch (e) {
    console.warn('  (EXTERNAL_MOUNTS 解析失败:', e.message, ')');
    return {};
  }
}

// 同步 .md（剥 frontmatter 后写入）+ 图片/PDF/JSON（原样拷）
const ASSET_EXTS = new Set(['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.pdf', '.json', '.csv']);

async function walk(dir) {
  const out = { md: [], asset: [] };
  async function recurse(d) {
    let names;
    try { names = await fs.readdir(d); }
    catch { return; }
    for (const name of names) {
      const full = resolve(d, name);
      // OneDrive 云端化文件夹是 ReparsePoint，Dirent.isDirectory 不准；用 stat 跟链。
      let st;
      try { st = await fs.stat(full); } catch { continue; }
      if (st.isDirectory()) {
        // 跳过 . / _ 前缀目录（如 chemistry/_extracted —— PDF 抽取的临时文本，
        // gitignore 且可再生，不该当成内容页发布）、node_modules、__pycache__。
        if (name.startsWith('.') || name.startsWith('_') || name === 'node_modules' || name === '__pycache__') continue;
        await recurse(full);
      } else if (st.isFile()) {
        // _sidebar.md 等 _ 前缀 markdown 是导航/元数据，不是内容页：
        // Sidebar.astro 直接从 knowledge_bases/<slug>/_sidebar.md import，
        // 不需要进内容集合，否则会渲染出 /kb/<slug>/_sidebar/ 噪音页。
        if (name.startsWith('_')) continue;
        if (name.endsWith('.md')) out.md.push(full);
        else if (ASSET_EXTS.has(name.slice(name.lastIndexOf('.')).toLowerCase())) out.asset.push(full);
      }
    }
  }
  await recurse(dir);
  return out;
}

function stripFrontmatter(text) {
  if (!text.startsWith('---\n') && !text.startsWith('---\r\n')) return text;
  // 按行找闭合：第一行 trim()==='---' 才算结束，避免子串 indexOf('\n---')
  // 误命中 '\n----'（更长虚线）或 '\n--- 正文' 而提前/错误截断 frontmatter。
  const lines = text.split('\n');
  for (let i = 1; i < lines.length; i++) {
    if (lines[i].trim() === '---') {
      return lines.slice(i + 1).join('\n');
    }
  }
  return text;  // 无闭合 → 原样返回
}

// 把相对 URL（相对当前文件所在目录）解析成绝对 /kb/<slug>/... 路径。
// baseDir 形如 '/kb/ai-ml-interview/大模型/基础理论/'（始终 / 开头 + / 结尾）。
// 用 URL 段语义处理 . / ..，与操作系统路径分隔符无关。
function resolveUrl(baseDir, rel) {
  const stack = baseDir.split('/').filter(Boolean);
  for (const seg of rel.split('/')) {
    if (seg === '' || seg === '.') continue;
    if (seg === '..') { if (stack.length) stack.pop(); }
    else stack.push(seg);
  }
  let out = '/' + stack.join('/');
  if ((rel === '' || rel.endsWith('/')) && !out.endsWith('/')) out += '/';
  return out;
}

// Markdown 链接重写：
//   [text](foo.md)            → [text](/kb/<slug>/<dir>/foo/)   （相对 → 绝对）
//   [text](foo/README.md)     → [text](/kb/<slug>/<dir>/foo/)
//   [text](/x/y/z.md)         → [text](/x/y/z/)                 （已绝对，仅 .md→/）
//   [text](../bar.md#hash)    → [text](/kb/<slug>/.../bar/#hash)
//   ![alt](../viz/x.png)      → ![alt](/<prefix>/viz/x.png)     （资产→绝对 public 路径）
//
// 关键：相对链接锚定**源文件所在目录**（baseUrlDir）解析成绝对路径。
// Astro trailingSlash:'always' 下页面是"目录式 URL"，浏览器按页面目录解析 ../ 会
// 比作者按"文件"写时少跳一层而错位；同步时锚定源文件路径产出绝对路径可彻底规避。
//
// 还把 <iframe src="docs/tools/pdf-reader.html?..." 改成绝对路径 /docs/tools/...
function rewriteLinks(text, baseUrlDir) {
  function convert(url) {
    // README.md → 目录；其他 .md → 去扩展加 /
    if (/(\/|^)README\.md$/i.test(url)) {
      url = url.replace(/(\/|^)README\.md$/i, (mm, sep) => sep || '');
      // 裸 README.md（同目录，无前缀）→ 剥后为空，输出 './' 指当前目录而非空串坏链。
      if (!url) url = './';
      else if (!url.endsWith('/')) url += '/';
    } else {
      url = url.replace(/\.md$/i, '/');
    }
    // 相对链接（不以 / 开头）→ 锚定源文件目录解析成绝对
    if (baseUrlDir && !url.startsWith('/')) url = resolveUrl(baseUrlDir, url);
    return url;
  }
  // markdown links
  text = text.replace(/(\]\()([^)]+?)(\))/g, (m, open, url, close) => {
    // 锚点 / 外部 URL / mailto / 资产 → 不动
    if (url.startsWith('#') || url.startsWith('http') || url.startsWith('mailto:') || url.startsWith('data:')) return m;
    // 拆 hash
    let hash = '';
    const hashIdx = url.indexOf('#');
    if (hashIdx >= 0) { hash = url.slice(hashIdx); url = url.slice(0, hashIdx); }
    if (/\.md$/i.test(url)) return open + convert(url) + hash + close;
    // 相对的目录/无扩展页面链接（如 ../00-foo/、./bar）→ 锚定源文件目录解析成绝对。
    if (baseUrlDir && !url.startsWith('/') && (/\/$/.test(url) || !/\.[a-z0-9]+$/i.test(url.replace(/\/$/, '')))) {
      return open + resolveUrl(baseUrlDir, url.endsWith('/') ? url : url + '/') + hash + close;
    }
    // 相对资产（图片 .png/.jpg… + .pdf/.csv 等，带扩展名）→ 锚定解析成绝对 public 路径。
    // 资产都已被拷到 web/public 同路径，绝对引用就走静态——图片因此不进 Astro image pipeline
    // （避免那条会崩的优化/emit）。
    if (baseUrlDir && !url.startsWith('/') && /\.[a-z0-9]+$/i.test(url)) {
      return open + resolveUrl(baseUrlDir, url) + hash + close;
    }
    return open + url + hash + close;
  });
  // 引号包裹的 .md（如 <a href="x.md">、HTML 内嵌 等）
  text = text.replace(/(href|src)="([^"]+?\.md)"/g, (m, attr, url) => {
    let hash = '';
    const hashIdx = url.indexOf('#');
    if (hashIdx >= 0) { hash = url.slice(hashIdx); url = url.slice(0, hashIdx); }
    return `${attr}="${convert(url)}${hash}"`;
  });
  // iframe 相对 src docs/tools/... → 绝对 /docs/tools/...
  text = text.replace(/src="docs\/tools\//g, 'src="/docs/tools/');
  return text;
}

async function copy(src, dst, baseUrlDir) {
  await fs.mkdir(dirname(dst), { recursive: true });
  const raw = await fs.readFile(src, 'utf-8');
  const cleaned = rewriteLinks(stripFrontmatter(raw), baseUrlDir);
  await fs.writeFile(dst, cleaned, 'utf-8');
}

async function copyRaw(src, dst) {
  await fs.mkdir(dirname(dst), { recursive: true });
  await fs.copyFile(src, dst);
}

async function syncOne(srcDir, opts = {}) {
  // opts.absSrc：直接给一个绝对路径作为源（EXTERNAL_MOUNTS 用），否则相对 KB_ROOT
  // opts.dstSubDir：覆盖目标子路径（multi-KB 用 'kb/<slug>'），否则等于 srcDir
  const srcRoot = opts.absSrc || resolve(KB_ROOT, srcDir);
  const dstRoot = resolve(ASTRO_CONTENT, opts.dstSubDir || srcDir);
  try { await fs.access(srcRoot); }
  catch { console.log('  skip (not found):', srcDir); return { added: 0, updated: 0, deleted: 0 }; }

  const { md: mdFiles, asset: assetFiles } = await walk(srcRoot);
  // URL 前缀：KB 是 'kb/<slug>'，外部挂载是 prefix（如 'external-reports'）。
  const urlRoot = opts.dstSubDir || srcDir;
  let added = 0, updated = 0;
  for (const f of mdFiles) {
    let rel = relative(srcRoot, f);
    // 源文件所在目录（KB 相对，posix 分隔）→ 拼成 baseUrlDir 供相对链接解析。
    const relPosix = rel.split(sep).join('/');
    const slashIdx = relPosix.lastIndexOf('/');
    const dirPart = slashIdx >= 0 ? relPosix.slice(0, slashIdx) : '';
    const baseUrlDir = '/' + urlRoot + (dirPart ? '/' + dirPart : '') + '/';
    // KB 用 README.md 当目录 landing；Astro CC 跟 index.md 更顺手
    if (rel.endsWith('README.md')) {
      rel = rel.slice(0, -'README.md'.length) + 'index.md';
    }
    const dst = resolve(dstRoot, rel);
    const wasNew = !(await fs.stat(dst).catch(() => null));
    await copy(f, dst, baseUrlDir);  // strips frontmatter + 相对链接→绝对
    if (wasNew) added++; else updated++;
  }
  for (const f of assetFiles) {
    const rel = relative(srcRoot, f);
    // 所有资产（图片 + pdf/json/csv）→ public/ 同路径，按绝对 URL 静态访问。
    // 图片不再放 content/ 让 Astro 优化：它的图片 emit 管线在外部报告那种大批量图上会崩
    // （把优化图写进 web/.astro/_astro 又读不回 ENOENT；cacheDir/passthroughImageService/
    // junction 都救不了，因为崩在写死的 emit 步骤）。当静态图直接 serve。markdown 里的相对
    // 图片引用由 rewriteLinks 重写成绝对 public 路径，与此一一对应。
    const publicSubDir = opts.dstSubDir || srcDir;
    const dst = resolve(ASTRO_PUBLIC, publicSubDir, rel);
    const wasNew = !(await fs.stat(dst).catch(() => null));
    await copyRaw(f, dst);
    if (wasNew) added++; else updated++;
  }

  return { added, updated, deleted: 0 };
}

// 框架资源（docs/{js,css,vendor,tools} 来自 kb-core，由 sync_core.py 同步到 KB 根的 docs/；
// preview 是本库的设计 demo）。Astro 前端从 web/public/docs/ serve 它们，所以构建时把根
// docs/ 镜像过去——单一来源是根 docs/，public/docs/ 是构建产物（已 gitignore），不再脱节。
// 递归扫描：返回 {newest: 最新文件 mtime(ms), count: 文件总数}。目录不存在返回 count:-1。
async function scanDir(dir) {
  let newest = 0, count = 0, entries;
  try { entries = await fs.readdir(dir, { withFileTypes: true }); } catch { return { newest: 0, count: -1 }; }
  for (const e of entries) {
    const p = resolve(dir, e.name);
    if (e.isDirectory()) {
      const r = await scanDir(p);
      if (r.newest > newest) newest = r.newest;
      count += Math.max(r.count, 0);
    } else {
      count++;
      try { const s = await fs.stat(p); if (s.mtimeMs > newest) newest = s.mtimeMs; } catch {}
    }
  }
  return { newest, count };
}

// rm+cp 带重试：OneDrive 同步该文件夹时会短暂占用 → EPERM/EBUSY，等一下重试。
async function rmCpWithRetry(src, dst) {
  for (let i = 0; i < 10; i++) {
    try {
      await fs.rm(dst, { recursive: true, force: true });
      await fs.cp(src, dst, { recursive: true });
      return;
    } catch (e) {
      if (i === 9) throw e;
      await new Promise((r) => setTimeout(r, 400));
    }
  }
}

async function mirrorFrameworkDocs() {
  const SUBDIRS = ['js', 'css', 'vendor', 'tools', 'preview'];
  const srcBase = resolve(KB_ROOT, 'docs');
  const dstBase = resolve(ASTRO_PUBLIC, 'docs');
  let n = 0, skipped = 0;
  for (const sub of SUBDIRS) {
    const src = resolve(srcBase, sub);
    try { await fs.access(src); } catch { continue; }
    const dst = resolve(dstBase, sub);
    // 没变就跳过：dst 文件数与 src 一致(完整) 且不比 src 旧 → 不动它。
    // 避免每次都删-重拷整个目录（OneDrive 锁的主因，vendor 还很大）；
    // 用「文件数一致」防止把上次没拷全的残缺目录也当成"没变"而漏修。
    const s = await scanDir(src);
    const d = await scanDir(dst);
    if (s.count > 0 && d.count === s.count && d.newest >= s.newest) { skipped++; continue; }
    await rmCpWithRetry(src, dst);
    n++;
  }
  console.log(`  framework docs/ → public/docs/ (${n} mirrored, ${skipped} unchanged)`);
}

async function main() {
  console.log('Syncing content from KB root → web/src/content/docs/');
  console.log('KB:', KB_ROOT);
  await mirrorFrameworkDocs();
  let total = { added: 0, updated: 0, deleted: 0 };

  const kbs = await discoverKBs();
  console.log(`  Found ${kbs.length} KB(s) under knowledge_bases/: ${kbs.join(', ')}`);
  for (const slug of kbs) {
    process.stdout.write(`  ${slug}: `);
    const r = await syncOne(`knowledge_bases/${slug}`, { dstSubDir: `kb/${slug}` });
    console.log(`+${r.added} ~${r.updated} -${r.deleted}`);
    total.added += r.added; total.updated += r.updated; total.deleted += r.deleted;
  }

  // EXTERNAL_MOUNTS：从 server/.env 解析（跨盘挂载）
  const externals = await readExternalMounts();
  for (const [prefix, absPath] of Object.entries(externals)) {
    process.stdout.write(`  ${prefix} (ext → ${absPath}): `);
    const r = await syncOne(prefix, { absSrc: absPath });
    console.log(`+${r.added} ~${r.updated} -${r.deleted}`);
    total.added += r.added; total.updated += r.updated; total.deleted += r.deleted;
  }

  console.log(`done. added=${total.added} updated=${total.updated} deleted=${total.deleted}`);
}

// --watch 模式：跑一次 main 后用 fs.watch 监视 SOURCES + EXTERNAL_MOUNTS，文件改动
// 触发增量 re-sync。注意 fs.watch 在 Windows 上对子目录支持有限，需要 recursive: true。
async function watchMode() {
  await main();
  console.log('[watch] watching for changes...');
  // 简单去抖：连续改动 500ms 后只跑一次 sync
  let pending = null;
  function trigger(label) {
    if (pending) clearTimeout(pending);
    pending = setTimeout(async () => {
      pending = null;
      console.log(`[watch] re-sync (${label})`);
      try { await main(); } catch (e) { console.error('[watch] sync failed:', e.message); }
    }, 500);
  }
  function watchDir(absRoot, label) {
    try {
      const w = fsWatch(absRoot, { recursive: true }, (eventType, filename) => {
        if (!filename) return;
        const s = String(filename);
        if (s.includes('node_modules') || s.includes('__pycache__') || s.startsWith('.')) return;
        if (!/\.(md|png|jpe?g|gif|svg|webp|pdf|json|csv)$/i.test(s)) return;
        trigger(`${label}/${s}`);
      });
      w.on('error', (e) => console.warn('[watch]', label, e.message));
    } catch (e) {
      console.warn('[watch] cannot watch', label, e.message);
    }
  }
  const kbs = await discoverKBs();
  for (const slug of kbs) watchDir(resolve(KB_DIR, slug), `kb:${slug}`);
  const externals = await readExternalMounts();
  for (const [prefix, absPath] of Object.entries(externals)) watchDir(absPath, prefix);
}

if (process.argv.includes('--watch')) {
  watchMode().catch((e) => { console.error(e); process.exit(1); });
} else {
  main().catch((e) => { console.error(e); process.exit(1); });
}
