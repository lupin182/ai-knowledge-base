# Web Frontend

这是 AI 知识库的 Astro 前端。FastAPI 后端在项目根目录的 `server/`，默认端口 `8001`；前端开发服务器默认端口 `4321`。

## 生产 / 单端口（推荐）

```bash
python run.py
```

`run.py` 会按需自动构建前端（缺 `web/dist` 或内容 / 前端源有更新时，自动 `npm install` + `npm run build`），然后在 `http://localhost:8001/` 单端口托管整站。一条命令即可，不用手动进 `web/` 构建。

## 开发模式（改前端代码时）

从项目根目录开两个终端，前端带热更新：

```bash
# 终端 1：后端 API
python run.py --no-build

# 终端 2：前端 dev server（热更新）
cd web
npm install
npm run dev
```

访问 `http://localhost:4321/`。开发模式下前端会调用 `http://localhost:8001/api/*`，后端已配置 CORS 允许 `localhost:4321`。

## 命令

`npm run build` 会先执行 `scripts/sync-content.mjs`，把 `knowledge_bases/` 同步到 `web/src/content/docs/`，并把根目录 `docs/` 镜像到 `web/public/docs/`，再 `astro build` 出 `web/dist/`，FastAPI 自动挂载它作为单端口前端。

| Command | Action |
| --- | --- |
| `npm install` | 安装前端依赖 |
| `npm run sync` | 同步知识库内容和公共静态资源 |
| `npm run dev` | 同步内容后启动 Astro dev server（:4321 热更新） |
| `npm run build` | 同步内容并构建到 `web/dist/` |
| `npm run preview` | 预览已构建的前端产物 |

## 目录

```text
web/
├── src/
│   ├── pages/          # Astro 页面
│   ├── layouts/        # 页面布局
│   ├── components/     # Topbar / Sidebar / TOC 等组件
│   ├── styles/         # 全局样式
│   └── content/        # sync-content 生成的知识库内容（gitignored）
├── public/             # sync-content 镜像的 docs/ 静态资源（gitignored）
├── scripts/
│   └── sync-content.mjs
├── astro.config.mjs
└── package.json
```
