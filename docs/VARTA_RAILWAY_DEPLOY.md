# Varta 方案 A：前后端都部署在 Railway

前后端两个 Service 都在同一 Railway 项目中，用两台电脑访问前端地址即可验证匹配。

---

## 一、代码与仓库

- 已做修改：
  - **前端** `varta/client/src/config.tsx`：生产环境优先使用环境变量 `REACT_APP_VARTA_BACKEND_URL`（未设置时退回原 Render 地址）。
  - **前端** `varta/client/package.json`：新增依赖 `serve`、脚本 `start:prod`，用于在 Railway 上提供构建后的静态文件。
- 将当前项目推送到 GitHub（若尚未推送）：
  ```bash
  git add .
  git commit -m "varta: Railway 方案 A 配置与部署说明"
  git push origin main
  ```

---

## 二、Railway 项目与两个 Service

1. 登录 [Railway](https://railway.app)，**New Project** → **Deploy from GitHub repo**，选择你的 `voice-chat-ai` 仓库。
2. 在项目中创建**两个 Service**（不要用同一个 Service 跑两个进程）：
   - **varta-backend**（后端）
   - **varta-frontend**（前端）

---

## 三、后端 Service（varta-backend）

1. 若从「从 GitHub 部署」时已经生成了一个 Service，可先改名为 `varta-backend`，或删掉后** Add Service → Empty Service**，再**从同一 GitHub 仓库添加**（选同一 repo，Root Directory 见下）。
2. **Settings → Root Directory**：设为 **`varta/server`**（只部署该目录）。
3. **Settings → Build**（若 Railway 未自动识别）：
   - Build Command：留空或 **`npm install`**
   - Output Directory：留空
4. **Settings → Deploy**：
   - Start Command：**`npm start`** 或 **`node index.js`**
   - Railway 会注入 **`PORT`**，后端已用 `process.env.PORT`，无需改代码。
5. **Settings → Variables** 添加：
   - **`FRONTEND_URL`** = 前端公网地址（下一步部署前端后再填，例如 `https://varta-frontend-xxxx.up.railway.app`）
6. **Settings → Networking → Generate Domain**：生成公网域名，例如  
   `https://varta-server-xxxx.up.railway.app`  
   记下该地址，后面给前端用。

---

## 四、前端 Service（varta-frontend）

1. **Add Service → 从同一 GitHub 仓库添加**，Root Directory 选 **`varta/client`**。
2. **Settings → Build**：
   - Build Command：**`npm run build`**
   - 如需安装依赖：Build Command 可设为 **`npm ci && npm run build`** 或保持 **`npm run build`**（Railway 一般会先自动 `npm install`）。
3. **Settings → Deploy**：
   - Start Command：**`npm run start:prod`**  
     （会执行 `serve -s build -l ${PORT:-3000}`，Railway 会注入 `PORT`。）
4. **Settings → Variables** 添加（重要，否则生产环境连不上后端）：
   - **`REACT_APP_VARTA_BACKEND_URL`** = 上一步得到的后端公网地址，例如  
     `https://varta-server-xxxx.up.railway.app`  
     （不要末尾斜杠；Create React App 在 **build 时** 注入该变量，所以改完后需**重新部署**一次前端。）
5. **Settings → Networking → Generate Domain**：生成前端公网地址，例如  
   `https://varta-frontend-xxxx.up.railway.app`  
   记下该地址。
6. 回到 **varta-backend** 的 **Variables**，把 **`FRONTEND_URL`** 设为上面这个前端地址（含 `https://`），保存后触发后端重新部署一次（保证 CORS / Socket.io 允许该来源）。

---

## 五、两台电脑验证匹配

1. 两台电脑的浏览器都打开**前端**公网地址（例如 `https://varta-frontend-xxxx.up.railway.app`）。
2. 都进入聊天页，都点 **「仅文字（验证用）」**（或正常 Join）。
3. 几秒内应匹配成功，可互发文字验证。

若一直匹配不上，可检查：

- 后端 Variables 里 **FRONTEND_URL** 是否与前端实际访问的域名一致（含 `https://`）。
- 前端 Variables 里 **REACT_APP_VARTA_BACKEND_URL** 是否与后端公网地址一致；修改后是否**重新部署**了前端（重新 Build + Deploy）。
- 浏览器控制台是否有 CORS / WebSocket 报错；Railway 后端日志是否有 `User connected`、`RoomId created`。

---

## 六、简要检查清单

| 项目 | 后端 varta-backend | 前端 varta-frontend |
|------|--------------------|----------------------|
| Root Directory | `varta/server` | `varta/client` |
| Build | 默认或 `npm install` | `npm run build` |
| Start | `npm start` | `npm run start:prod` |
| 环境变量 | `FRONTEND_URL` = 前端公网 URL | `REACT_APP_VARTA_BACKEND_URL` = 后端公网 URL |
| 公网访问 | Generate Domain，得到后端 URL | Generate Domain，得到前端 URL |

改完环境变量后，前端若已部署过，需再触发一次部署（或 Redeploy）以便用新变量重新 build。
