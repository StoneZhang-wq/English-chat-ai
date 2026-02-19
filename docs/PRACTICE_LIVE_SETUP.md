# 真人 1v1 练习：你需要做的步骤

本文说明在「英语学习 + 真人对话」集成完成后，**你需要自己完成的步骤**（构建、部署、环境变量）。

---

## 一、已实现的功能（无需再改代码）

- **小场景里的 1v1 按钮**：进入沉浸式场景 → 选大场景 → 选小场景（如银行）→ 该小场景页下方有「真人 1v1 练习」按钮，点击跳转到同站 `/practice/live/chat?scene=xxx`。
- **同场景匹配**：只有选择同一小场景（如同一 `scene` 参数）的用户会互相匹配。
- **同源访问**：真人练习页由主站 FastAPI 提供，地址为 `你的主站/practice/live` 或 `/practice/live/chat?scene=xxx`，用户只看到一个网址。
- **去品牌化**：前端标题、导航、页脚等已改为「真人练习」等，无 Varta 字样。

---

## 二、你必须做的步骤

### 1. 构建真人练习前端并放入主站

真人练习页面是 React 应用，需要先构建，再把构建产物交给 FastAPI 提供。

**推荐：一键完成（在项目根目录执行）**

```bash
npm run build:practice-live
```

该脚本会自动在 `varta/client` 下执行 `npm install`、`npm run build`，并把 `build/` 内容复制到 `app/static/practice-live/`。

**生产环境**：若需指定 Socket.io 后端地址，请先设置环境变量再执行：

```bash
# Windows (PowerShell)
$env:REACT_APP_VARTA_BACKEND_URL="https://你的varta后端地址"
npm run build:practice-live

# Linux/macOS
REACT_APP_VARTA_BACKEND_URL=https://你的varta后端地址 npm run build:practice-live
```

**手动构建**（可选）：在项目根目录执行 `cd varta/client` → `npm install` → `npm run build`，再将 `varta/client/build/*` 复制到 `app/static/practice-live/`。

完成后，启动主站（FastAPI），访问 `http://localhost:8000/practice/live` 或 `http://localhost:8000/practice/live/chat` 应能看到真人练习页。若未构建/复制，会看到「真人练习未就绪」的提示。

### 2. 配置真人练习的后端地址（Socket.io）

真人通话与匹配由 **Varta 的 Node 服务** 提供（Socket.io），和 FastAPI 是分开的。前端在**构建时**会读环境变量并写死后端地址，所以：

- **本地开发**：前端默认连 `http://localhost:5001`，只需在项目里启动 `varta/server`（`cd varta/server && npm install && npm start`）。直接执行 `npm run build:practice-live` 即可。
- **生产/部署**：在执行 `npm run build:practice-live` **之前**，设置环境变量：
  - 变量名：`REACT_APP_VARTA_BACKEND_URL`
  - 值：你的 Varta 后端公网地址，例如 `https://你的varta后端.up.railway.app`（不要末尾斜杠）

然后执行 `npm run build:practice-live`（脚本会完成构建并复制）。

### 3. 部署到 Railway（或其它平台）时的分工

- **主站（一个 Service）**：部署 FastAPI + 静态资源（包含 `app/static/practice-live/`）。用户只访问这一个域名，例如 `https://你的英语学习站.up.railway.app`。英语练习和真人 1v1 都在这个域名下（真人 1v1 路径为 `/practice/live`、`/practice/live/chat`）。
- **真人练习后端（另一个 Service）**：单独部署 `varta/server`（Node + Socket.io），并生成公网域名（如 `https://你的varta后端.up.railway.app`）。在构建真人练习前端时，将 `REACT_APP_VARTA_BACKEND_URL` 设为该地址。

这样用户始终只用一个网址（主站），真人 1v1 的页面和接口请求会由前端自动连到你配置的 Socket.io 后端。

### 4. 可选：替换图标与文案

- 若希望真人练习页使用你自己的图标，可替换 `varta/client/public/` 下的 `apple-icon-*.png`、`android-icon-192x192.png` 等，然后重新 `npm run build` 并再复制到 `app/static/practice-live/`。
- 文案（如「真人练习」「为什么选择真人练习？」等）已在代码中改为中文，如需进一步定制可改 `varta/client/src` 下对应组件后重新构建。

---

## 三、简要检查清单

| 步骤 | 说明 |
|------|------|
| 1 | 在项目根目录执行 `npm run build:practice-live`（生产环境先设 `REACT_APP_VARTA_BACKEND_URL` 再执行） |
| 2 | 脚本会自动完成构建并复制到 `app/static/practice-live/`，无需手动复制 |
| 3 | 主站能访问 `/practice/live`、`/practice/live/chat`，且真人练习页能正常打开 |
| 4 | 真人练习后端（varta/server）已单独部署并配置 CORS/FRONTEND_URL 为主站域名 |
| 5 | 从场景页点「真人 1v1 练习」能跳转到 `/practice/live/chat?scene=xxx` 并参与同场景匹配 |

完成以上步骤后，用户即可在**同一网址**下使用英语练习和真人 1v1 对话，且不会看到 Varta 品牌。
