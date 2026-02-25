# 1v1 真人练习功能自检清单

用于确认匹配、Active User、任务/角色内容、互换角色、场景分配等功能是否正常。

---

## 一、功能列表与验证方式

| 功能 | 说明 | 验证方式 |
|------|------|----------|
| **匹配** | 两人进入 /practice/live/chat 点 Join 后进入同一队列，先到先配 | 两台设备或两个浏览器同时点 Join，应进入同一房间、看到对方视频与名字 |
| **Active User 数** | 导航栏显示当前连上 Varta 后端的用户数 | 打开 1v1 页，点 Join 后看右上角「Active User - N」应 ≥1；多人 Join 时 N 增加 |
| **后端地址显示** | 导航栏显示「后端: xxx」便于排查 | 应为你的 Varta 公网域名（主站配置 VARTA_BACKEND_URL 后由 /api/practice-live/config 下发） |
| **匹配成功后的界面** | 右侧显示本局主题、你的角色、任务、可说的内容 | 匹配成功后右侧出现「本局主题」「第1轮·你扮演」「你的任务」「你可说的内容」列表 |
| **分配场景** | 按两人已解锁场景交集（无则并集）选主题；无解锁则随机 | 双方都解锁某场景时，本局主题应为该场景下一条对话；否则随机一条 immersive |
| **互换角色** | 第一轮结束后可点「互换角色」，双方同意后切换角色与任务再练一轮 | 点「互换角色」→ 对方也点「互换角色」→ 右侧角色/任务/可说的内容更新为对方原角色，进入第2轮 |
| **Exit 与重匹配** | 点 Exit 退出房间后可再次匹配 | 点 Exit 后回到「正在匹配…」，可再次与其他人匹配 |

---

## 二、依赖与配置

- **主站**：配置 `VARTA_BACKEND_URL`（Varta 公网地址），并部署 `app/static/practice-live/`（或使用 Dockerfile.railway 每次构建打进镜像）。
- **Varta 服务**：配置 `FRONTEND_URL` 为主站 origin（多个用逗号分隔），保证 CORS 允许主站访问。
- **账号与解锁**：1v1 页带 `account`（URL 参数或主站 postMessage）时，主站 `/api/practice-live/unlocked-scenes?account_name=xxx` 返回该账号已解锁的 small_scene_id 列表，用于分配场景。

---

## 三、本次检查中的修正（摘要）

1. **国旗/国家显示**：Varta 服务端使用 ipapi.co 的 `country_code`（两字母）作为 `remoteCountry` 下发，前端用其请求 flagcdn 国旗图，避免此前用 `country` 字段导致无图或 Unknown。
2. **add-ice-candidate 携带 roomId**：服务端转发 ICE 时一并下发 `roomId`，与前端参数一致，便于后续扩展。
3. **无主题时的兜底**：当 dialogue 接口 404 或无数据时，右侧仍显示「本局无主题数据，可自由对话；完成后可点击 Exit 退出。」，避免空白困惑。

---

## 四、常见问题速查

- **Active User 一直为 0**：主站未配 `VARTA_BACKEND_URL` 或 Varta 未启动；或前端未连上 Varta（看「后端:」是否为正确域名）。
- **匹配不到**：两人未连到同一 Varta 实例；或 CORS 阻止（检查 Varta 的 `FRONTEND_URL` 是否包含主站 origin）。
- **任务/角色不显示**：主站 `/api/practice-live/dialogue` 或 `/dialogue/random` 返回 404 时会出现「本局无主题数据」；检查 `data/dialogues.json` 中是否有 `usage: "immersive"` 的对话。
- **互换角色不生效**：需双方都点击「互换角色」；若仅一方点击，会显示「已点击互换，等待对方」。
