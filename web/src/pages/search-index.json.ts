// 构建期生成的全站搜索索引（静态文件 /search-index.json）。
// 站点是静态 MPA，没有服务端搜索；侧栏搜索框由 client.ts 懒加载这份 JSON 做即时过滤。
// 每条 = 一个已发布页面：标题（同 [...slug].astro 的取法）、URL、所属 KB slug、正文纯文本（截断控体积）。
import { getCollection } from 'astro:content';

// 静态构建：在 build 时跑一次，产出 dist/search-index.json（由后端随 web/dist 一起静态 serve）。
export const prerender = true;

const TEXT_CAP = 2000; // 每页正文纳入索引的字符上限——够覆盖标题/小节/开头，又不让索引膨胀。

function toPlainText(md: string): string {
  return md
    .replace(/```[\s\S]*?```/g, ' ')          // 代码块
    .replace(/`[^`]*`/g, ' ')                  // 行内代码
    .replace(/!\[[^\]]*\]\([^)]*\)/g, ' ')     // 图片
    .replace(/\[([^\]]*)\]\([^)]*\)/g, '$1')   // 链接 → 链接文字
    .replace(/^[\s>#*+\-|]+/gm, ' ')           // 行首的引用/标题/列表/表格标记
    .replace(/[#*`~|>]/g, ' ')                 // 残余标记符
    .replace(/\s+/g, ' ')
    .trim();
}

export async function GET() {
  const docs = await getCollection('docs');
  const entries = docs.map((e: any) => {
    const body: string = e.body || '';
    const headingMatch = body.match(/^#{1,6}\s+(.+)$/m);
    const fileSeg = e.id.replace(/\/index$/, '').split('/').pop() || e.id;
    const title =
      (e.data && e.data.title) ||
      (headingMatch ? headingMatch[1].replace(/[#*`]/g, '').trim() : '') ||
      fileSeg.replace(/[-_]/g, ' ');
    // id → URL：index / */index 归一成目录路由（与 [...slug].astro 一致）。
    let id: string = e.id;
    if (id === 'index') id = '';
    else if (id.endsWith('/index')) id = id.slice(0, -'/index'.length);
    const url = '/' + (id ? id + '/' : '');
    const slug = (e.id.match(/^kb\/([^/]+)/) || [])[1] || e.id.split('/')[0] || '';
    return { title, url, slug, text: toPlainText(body).slice(0, TEXT_CAP) };
  });
  return new Response(JSON.stringify(entries), {
    headers: { 'Content-Type': 'application/json; charset=utf-8' },
  });
}
