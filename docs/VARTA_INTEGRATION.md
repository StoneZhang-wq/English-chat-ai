# Varta 真人 1v1 视频通话集成说明

Varta 已克隆到项目内 `varta/`，用于实现「解锁同一小场景/NPC 的两人匹配后真人一对一视频通话」。

## 一、本地运行 Varta（先跑通再对接）

### 1. 服务端（Node）

```bash
cd varta/server
# 若无 config.env，复制示例：copy config.env.example config.env（Windows）或 cp config.env.example config.env（Mac/Linux）
npm install
npm start
```

- 默认端口：5001（避免与主项目占用的 5000 冲突）  
- 不配置 `MONGO_URI` 也可运行（仅不持久化用户记录）。

### 2. 前端（React）

```bash
cd varta/client
npm install
npm start
```

- 默认：http://localhost:3000  
- 点击 "Start Chatting" → "Join" 授权摄像头/麦克风后进入大厅，两人同时在线即自动匹配并建立视频通话。

### 3. 验证

- 用两个浏览器（或一个正常 + 一个无痕）各开 http://localhost:3000 ，都点 Join，应能互相看到画面并通话。
- **仅文字验证（不启用摄像头/麦克风）**：在聊天页点击 **「仅文字（验证用）」**，两个标签页都点后会自动匹配，仅通过右侧文字框发消息验证匹配与 Data Channel 是否正常。验证完成后可按下方「恢复原版」还原。

### 4. 仅文字验证后恢复原版

当前为方便单机验证，在 Varta 前端加了「仅文字（验证用）」入口。若验证成功、需恢复为仅支持音视频的原始行为，可做以下还原：

| 文件 | 还原内容 |
|------|----------|
| `varta/client/src/pages/ChatPage.tsx` | 删除 `textOnlyMode` 状态及相关说明文案；删除 `joinTextOnlyHandler` 与「仅文字（验证用）」按钮；将 Room 的渲染条件改回 `localAudioTrack?.enabled && localVideoTrack?.enabled`，去掉对 `textOnlyMode` 的判断与传参。 |
| `varta/client/src/components/Room.tsx` | 去掉 `textOnlyMode` 的 props 与类型；去掉「仅文字模式」的 UI 分支（保留原来的 Local Video 一块即可）。 |

## 二、与主项目的集成规划（按场景/NPC 匹配）

- **当前 Varta**：随机匹配（队列中任意两人配对）。  
- **目标**：仅当两人都解锁了同一小场景或同一 NPC 对话时，才可匹配进同一房间。

计划改动方向：

1. **主项目 FastAPI**  
   - 提供接口：根据当前登录用户 + 选择的「小场景」或「NPC」，返回该用户是否已解锁、以及可用的「匹配键」（如 `scene_id` / `small_scene + npc`）。  
   - 可选：提供「匹配请求」接口，由主项目维护「按场景的等待队列」，并返回 room_id 与对方信息，再由 Varta 仅负责该 room 内的 WebRTC 信令。

2. **Varta 服务端**  
   - 当前：`UserManager` 的 `tryToPairUsers()` 从队列中任意取两人配对。  
   - 修改为：按「匹配键」（如 `scene_id`）维护多队列，只对同一 key 下的用户两两配对；或接收主项目下发的「已配对 room_id + 两个 socket/用户」，仅做建房与信令。

3. **Varta 前端**  
   - 从主应用跳转或嵌入时，携带「当前用户」与「选择的小场景/NPC」；  
   - 连接 Varta 后发送 `user-info` 时增加 `sceneId`（或 `unlockedSceneKey`），服务端用其做匹配。

当前仓库内已做的修改：

- `varta/server/db/db.js`：未配置 `MONGO_URI` 时不连接 MongoDB，不退出进程。  
- `varta/server/managers/UserManager.js`：仅当 MongoDB 已连接时才写入 User 记录。  
- `varta/server/config.env.example`：示例配置，复制为 `config.env` 即可运行。

下一步可做：在主项目中新增「真人匹配」相关 API，并在 Varta 中实现按 `sceneId` 的队列与配对逻辑。
