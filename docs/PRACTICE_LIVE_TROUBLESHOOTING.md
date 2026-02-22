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
| 手机与电脑匹配无画面/无声音 | 八（配置 TURN / REACT_APP_ICE_SERVERS） |
| 第一局总是同一场景（如外卖员） | 九（已改为 UUID 房间 ID；确认账号与 unlockedScenes） |
| 想确认主题是按账号还是随机 | 十（看控制台 + Varta 日志 + 可选 Network） |

按上面顺序一项项确认，通常能在 一～四 里找到原因。

---

## 八、手机与电脑匹配：看不到对方视频 / 听不到声音

- **原因**：WebRTC 默认只用 STUN（公网发现），手机和电脑若在不同网络/NAT 后，有时无法直连，需要 **TURN 中继** 才能互通。
- **已做**：前端已支持双 STUN（Google）并支持通过 `REACT_APP_ICE_SERVERS` 自定义 ICE（可含 TURN）。构建时设置该变量为 JSON 数组，例如：
  ```bash
  # 仅 STUN（默认已有）
  set REACT_APP_ICE_SERVERS=[{"urls":"stun:stun.l.google.com:19302"}]
  # 若使用 TURN 服务（需自行申请，如 Twilio、xirsys、自建 coturn）：
  set REACT_APP_ICE_SERVERS=[{"urls":"stun:stun.l.google.com:19302"},{"urls":"turn:your-turn.com:443","username":"xx","credential":"yy"}]
  ```
  然后重新执行 `npm run build:practice-live` 并部署。
- **排查**：浏览器 F12 → Console 看是否有 ICE/WebRTC 相关报错；若两边都显示“已连接”但无画面无声音，多半是 NAT 穿透失败，需配置 TURN。

---

## 九、第一局总是同一场景（如外卖员）

- **原因**：此前房间 ID 为自增数字（1、2、3…），服务重启后第一间房固定为 `room_id=1`。后端用 `room_id` 做随机种子取一条沉浸对话，种子相同则结果相同，故第一局总是同一条（若该条是外卖员则总是外卖员）。
- **已做**：房间 ID 已改为 **UUID**，每局种子不同，随机到的场景/对话会分散，不再固定“第一局一定是外卖员”。
- **主题是否按账号**：是。匹配时用两人 `unlockedScenes` 的交集（无则并集）选出 **small_scene_id**；只有双方都未传或都为空时才用“随机一条”。若你经常看到随机场景，可查：1）嵌入主站时是否传了 account；2）主站 `/api/practice-live/unlocked-scenes` 是否按账号返回了列表；3）Varta 日志里 `Match: ... -> theme xxx` 是否有 `theme` 或 `random`。

---

## 十、检验：主题到底是按账号（交集/并集）还是随机？

按下面步骤可自己验证当前是否真的在用账号分配主题。

### 1. 看浏览器控制台（1v1 页面 F12 → Console）

- **连上并点 Join 后**应看到其一：
  - `[1v1] 已按账号获取解锁场景数: N account: xxx` → 说明**有账号且主站返回了 N 个解锁场景**，匹配会用交集/并集。
  - `[1v1] 无 account，未请求解锁场景，匹配将使用随机主题` → 说明**没有账号**，本局一定是随机主题。
  - `[1v1] unlocked-scenes 请求非 200` → 主站接口失败，unlockedScenes 为空，会走随机。
- **匹配成功、收到 send-offer 后**应看到其一：
  - `[1v1] 本局主题来源: 按账号交集/并集 -> smallSceneId` → 本局主题**来自两人解锁场景的交集或并集**。
  - `[1v1] 本局主题来源: 随机（双方均无解锁场景或未传账号）` → 本局主题是**随机**，说明双方都没传到有效解锁列表（或未传账号）。

### 2. 看 Varta 服务端日志（Railway 上该 Service 的 Deploy Logs）

每次匹配会打一行类似：

```text
Match: 用户名 (account或no-account) [N unlocks] + 用户名 (account或no-account) [M unlocks] -> theme smallSceneId或random (intersection|union|random)
```

- **theme 后面是具体 smallSceneId** 且 **括号里是 intersection 或 union**：说明用的是**两人账号的解锁场景**（先交集，无则并集）。
- **theme 后面是 random** 且 **括号里是 random**：说明两人 **unlockedScenes 都为空**（没账号、接口失败或账号下确实无解锁），本局是随机一条对话。
- **`[N unlocks]` / `[M unlocks]` 为 0**：该用户没有解锁场景，若两人都是 0 则必为 random。

### 3. 看主站接口（可选）

浏览器 F12 → Network，筛选 `unlocked-scenes`：

- 若 1v1 页**有 account**（URL 带 `?account=xxx` 或 postMessage 拿到），应有一条请求：  
  `GET /api/practice-live/unlocked-scenes?account_name=xxx`
- 点开看 Response：`small_scene_ids` 应为字符串数组；**若为空数组 `[]`**，说明该账号在主站侧没有解锁任何场景（或接口按账号查出来是空），匹配时仍会走并集/随机。

### 小结

| 你看到的情况 | 含义 |
|--------------|------|
| 控制台有「已按账号获取解锁场景数: N」且 N≥1，且收到「本局主题来源: 按账号交集/并集」 | 主题**是**按账号的交集/并集选的。 |
| 控制台有「无 account」或「本局主题来源: 随机」 | 本局主题**是**随机的，未用账号。 |
| 服务端日志 `theme random (random)` 或 `[0 unlocks]` | 双方都没有解锁场景或没传账号，系统走了随机。 |
| 服务端日志 `theme xxx (intersection)` 或 `(union)` | 主题**是**按两人解锁场景的交集或并集选的。 |
