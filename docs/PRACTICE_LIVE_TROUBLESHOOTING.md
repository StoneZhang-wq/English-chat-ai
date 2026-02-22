# 真人 1v1：Active User 为 0、匹配不上 — 排查清单

按顺序逐项检查，每项确认后再看下一项。

---

## 一、前端实际连的是哪个后端（最容易出问题）

- [ ] **1.1** 打开 1v1 页面（要点进真人练习并点一次 Join 之前就能看）
  - 看页面**右上角/导航栏**「后端: xxx」显示的是什么域名。
  - **应该是**：你 Railway 上 Varta 的公网域名（如 `xxx.up.railway.app` 或你的自定义域名）。
  - 若是 `varta-server.onrender.com` 或 `localhost` → 说明当前用的前端是**用错地址构建的**，浏览器根本没连到你现在的 Varta。

- [ ] **1.2** 若 1.1 不对：用**正确的 Varta 公网 URL** 设置 `REACT_APP_VARTA_BACKEND_URL`，重新执行：
  ```bash
  # 把下面的 URL 换成你 Railway 上 Varta 的真实地址
  set REACT_APP_VARTA_BACKEND_URL=https://你的varta.up.railway.app
  npm run build:practice-live
  ```
  再把新的 `app/static/practice-live/` 部署到主站（或重新部署主站）。

---

## 二、主站代理是否指到同一台 Varta

- [ ] **2.1** 主站 Service（Railway）环境变量里是否有 **VARTA_BACKEND_URL**，且值 = **和 1.1 里显示一致**的 Varta 地址（https，无末尾斜杠）。
  - 没配或配错 → `/api/practice-live/user-count` 会直接返回 0 或请求失败返回 0。

- [ ] **2.2** 主站部署后，在服务器日志里看是否有 `practice-live user-count proxy failed: ...`。
  - 有 → 主站连不上 Varta（网络/超时/地址错），需要根据报错修。

---

## 三、Varta 的 CORS 是否放行主站

- [ ] **3.1** Varta Service 环境变量 **FRONTEND_URL** 是否包含**用户打开 1v1 时浏览器地址栏的 origin**（协议+域名，如 `https://englishchatcommunity.com`）。
  - 多域名用英文逗号分隔，不要有多余空格（或按代码 trim 后正确）。
  - 若用户用 `https://主站.up.railway.app` 访问，这里也要包含该 origin。

- [ ] **3.2** 浏览器开发者工具 → **Console**：打开 1v1 页并点 Join，看是否有 CORS 相关报错（例如 `blocked by CORS policy`、`Access-Control-Allow-Origin`）。
  - 有 → 多半是 3.1 的 origin 没写对或没包含当前访问域名。

---

## 四、Socket 是否真的连上（关键）

- [ ] **4.1** 浏览器开发者工具 → **Network**：筛选 WS 或 XHR，点 Join 后是否出现对 **Varta 域名**的请求（如 `wss://xxx.up.railway.app/...`）。
  - 没有或失败 → 连接没建立，Active User 一定是 0，也不会匹配。

- [ ] **4.2** Varta 服务（Railway）**运行日志**里，当用户点 Join 后是否出现 `User connected: xxx`（socket.id）。
  - 没有 → 浏览器没连上这台 Varta（回到一、三或网络问题）。

---

## 五、用户是否点了 Join、Room 是否渲染

- [ ] **5.1** 只有**点击「Join（视频+语音）」**后，前端才会挂载 Room 并建立 Socket。没点 Join 不会连上，也不会被计入 Active User。
  - 确认测试时已经点了 Join。

- [ ] **5.2** 若 1v1 是嵌在主站 iframe 里：主站是否通过 URL 或 postMessage 传了 **account**；若一直拿不到 account，页面会显示「正在获取账号…」且可能不渲染 Room（视当前逻辑而定）。  
  - 之前能匹配说明当时 account 是有的；若你改过主站嵌入方式或域名，需确认 postMessage / URL 仍会带 account。

---

## 六、Varta 服务与网络

- [ ] **6.1** Railway 上 Varta Service 是否**正在运行**、无频繁重启/崩溃。
  - 在 Railway 面板看该 Service 的 Deploy 状态和日志。

- [ ] **6.2** 主站和 Varta 是否在**同一 Railway 项目**或网络互通；若 Varta 有 IP/域名访问限制，主站服务器要能访问到 VARTA_BACKEND_URL。

- [ ] **6.3** 若 Varta 用了自定义域名或反向代理，确认 **WebSocket** 被正确转发（不少代理默认不转发 WS，需单独配置）。

---

## 七、匹配逻辑本身（一般在前几项修好后才看）

- [ ] **7.1** 匹配需要**至少两人**都：连上 Socket → 发过 **user-info**（在 Room 的 `connect` 回调里自动发）。  
  - 用两个不同设备或两个浏览器（或隐身窗口）各打开 1v1、各点 Join，再看 Varta 日志是否有两个 `User connected` 和后续的 `Match: ...`。

- [ ] **7.2** Varta 日志里若一直只有 `User connected` 没有 `Match: ...`，说明只有一人进队列或 user-info 没被处理；若两人都连上且都发了 user-info，应有 `Match` 日志。

---

## 快速对照表

| 现象 | 优先查 |
|------|--------|
| 页面「后端:」不是 Railway Varta 地址 | 1.1、1.2（重新用正确 URL 构建） |
| Active User 一直是 0 | 1、2、4、5（连错后端 / 代理错 / 没连上 / 没点 Join） |
| 点 Join 后 Network 里没有对 Varta 的 WS | 1、3（地址或 CORS） |
| Varta 日志没有 `User connected` | 1、3、6（地址、CORS、服务/网络） |
| 有 `User connected` 但没有 `Match` | 7（需两人都连上并发 user-info） |

按上面顺序一项项确认，通常能在 一～四 里找到原因。
