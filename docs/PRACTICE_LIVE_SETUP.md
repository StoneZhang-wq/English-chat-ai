# 真人 1v1 练习：你需要做的步骤

本文说明在「英语学习 + 真人对话」集成完成后，**你需要自己完成的步骤**（构建、部署、环境变量）。

---

## 一、已实现的功能（无需再改代码）

- **小场景里的 1v1 按钮**：进入沉浸式场景 → 选大场景 → 选小场景（如银行）→ 该小场景页下方有「真人 1v1 练习」按钮，点击跳转到同站 `/practice/live/chat?scene=xxx`。
- **同场景匹配**：只有选择同一小场景（如同一 `scene` 参数）的用户会互相匹配。
- **同源访问**：真人练习页由主站 FastAPI 提供，地址为 `你的主站/practice/live` 或 `/practice/live/chat?scene=xxx`，用户只看到一个网址。
- **去品牌化**：前端标题、导航、页脚等已改为「真人练习」等，无 Varta 字样。
- **返回主界面**：真人练习页导航栏有「返回主界面」按钮，嵌入主站 iframe 时点击会切回英语学习主界面（主站需监听 `practice-live-go-back` 并切换 hash，已内置）。
- **匹配与主题**：服务端根据房间内两人的**已解锁场景**选主题：先取**交集**随机一个，无交集则取**并集**随机一个；用户身份通过主站传入的 account 获取解锁列表并随 `user-info` 发送 `unlockedScenes`。

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

真人通话与匹配由 **Varta 的 Node 服务** 提供（Socket.io），和 FastAPI 是分开的。

- **运行时配置（推荐）**：1v1 前端会在打开时请求主站 `GET /api/practice-live/config` 获取 Varta 地址。只需在**主站**环境变量中配置 **VARTA_BACKEND_URL**（指向你的 Varta 公网地址），部署主站后刷新 1v1 页即可生效，**无需重构建** 1v1 前端。
- **本地开发**：前端默认连 `http://localhost:5001`，主站未配或接口未返回时使用该默认；在项目里启动 `varta/server` 后直接执行 `npm run build:practice-live` 即可。
- **构建时兜底**：若希望构建产物自带默认地址，可在执行 `npm run build:practice-live` 前设置 `REACT_APP_VARTA_BACKEND_URL`；部署后仍以主站下发的为准。

### 3. 部署到 Railway（或其它平台）时的分工

- **主站（一个 Service）**：部署 FastAPI + 静态资源（包含 `app/static/practice-live/`）。用户只访问这一个域名，例如 `https://你的英语学习站.up.railway.app`。英语练习和真人 1v1 都在这个域名下（真人 1v1 路径为 `/practice/live`、`/practice/live/chat`）。
- **真人练习后端（另一个 Service）**：单独部署 `varta/server`（Node + Socket.io），并生成公网域名（如 `https://你的varta后端.up.railway.app`）。在构建真人练习前端时，将 `REACT_APP_VARTA_BACKEND_URL` 设为该地址。

这样用户始终只用一个网址（主站），真人 1v1 的页面和接口请求会由前端自动连到你配置的 Socket.io 后端。

**避免 CORS（推荐）**：前端已改为通过主站同源接口 `/api/practice-live/user-count` 获取在线人数，不再直连 Varta 的 `/user-count`。请在**主站**环境变量中配置 `VARTA_BACKEND_URL`（指向你的 Varta 公网地址，如 Railway 上的 Varta Service URL），主站会代理请求到该地址并返回人数，从而避免跨域报错与「连接失败」。

**Varta 服务 CORS**：Varta 的 `FRONTEND_URL` 可为**多个来源**（逗号分隔），例如 `https://englishchatcommunity.com,https://你的主站.up.railway.app`，便于主站自定义域名与 Railway 预览域名同时使用。

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

---

## 四、常见问题：两人都进了真人练习但匹配不到、Active User 一直为 0

**Active User 统计的是什么**：  
统计的是**已点击 Join 并成功连上 Varta 后端的 Socket 用户数**（不是「打开 1v1 页面」的人数）。只有进入匹配/房间后才会建立 Socket 连接并被计入。页面通过主站同源接口 `/api/practice-live/user-count` 请求，主站再代理到 `VARTA_BACKEND_URL/user-count`，因此**主站必须配置环境变量 VARTA_BACKEND_URL**，否则代理会直接返回 0。

**原因说明**：  
若你已点击 Join 且页面无「连接失败」但人数仍为 0，或两人互相匹配不到，说明**前端没有成功连上你部署的 Varta 后端**（要么连错地址，要么被 CORS/网络拦截）。

**按下面顺序排查：**

1. **看 1v1 页面上显示的「后端」地址**  
   - 真人练习页右上角会显示一行小字：`后端: xxx`（仅显示主机名）。  
   - 确认这里的 `xxx` 就是你**实际部署的 Varta 后端域名**（例如 `varta-xxx.up.railway.app`）。  
   - 若显示的是 `localhost:5001` 或别的错误地址，说明构建时没有正确设置 `REACT_APP_VARTA_BACKEND_URL`，需要重新设置该变量后再执行 `npm run build:practice-live`，并重新部署主站静态资源。

2. **是否出现「连接失败」**  
   - 若在「Active User」旁出现红色「连接失败」，说明对 `/user-count` 的请求失败（跨域、网络或后端未启动）。  
   - 在浏览器中直接打开 `https://你的varta后端域名/user-count`，应看到 JSON：`{"userCount":0}`。若打不开或报错，说明 Varta 服务未部署/未运行或地址错误。  
   - 若该 URL 能打开但页面里仍「连接失败」，多半是 **CORS**：Varta 的 `FRONTEND_URL` 必须设成**主站页面的来源**（例如 `https://你的主站.up.railway.app`），不能是 `http://localhost:3000`。

3. **确认 Varta 后端已单独部署且运行**  
   - 两个 Service 架构下，Varta 必须单独一个 Service（如单独一个 Railway Service 跑 `varta/server`），并生成公网 URL。  
   - 该 URL 要在构建 1v1 前端时写入 `REACT_APP_VARTA_BACKEND_URL`，且 Varta 的 `FRONTEND_URL` 要设为主站域名。

4. **浏览器开发者工具辅助排查**  
   - 打开真人练习页 → F12 → Network：筛选 WS 或 XHR，看是否有对「后端: xxx」那个域名的请求（如 `wss://xxx/socket.io`、`https://xxx/user-count`）。  
   - 若完全没有对 Varta 域名的请求，说明前端用的后端地址不对（见第 1 步）。  
   - 若有请求但标红失败，看控制台是否有 CORS 或 mixed content 报错，并对照第 2、3 步检查 URL 与 `FRONTEND_URL`。

**总结**：  
- Active User 为 0 = 当前没有用户连上该 Varta 实例（或前端根本没连上它）。  
- 两人都进真人练习但匹配不到 = 两人的 Socket 没有连到**同一个** Varta 后端，或后端 CORS 阻止了连接。  
- 务必保证：构建时 `REACT_APP_VARTA_BACKEND_URL` = Varta 公网地址；Varta 的 `FRONTEND_URL` = 主站域名；两个用户访问的是同一个主站、同一套构建产物。
