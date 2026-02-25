# 1v1 真人练习页面布局问题说明（供其他 AI 参考）

## 一、问题描述

**场景**：React 真人练习页（1v1 视频对话），左侧是**视频区**（远端 + 本地摄像头），右侧是**任务/聊天区**（本局主题、你的任务、你可说的内容、聊天、互换角色按钮）。

**遇到的情况**：
1. 右侧任务文字很长时，会把整块右侧区域**横向撑宽**，从而**挤压左侧视频**，视频被挤成一条或几乎看不见。
2. 需求是：**右侧任务区固定宽度**，长内容在右侧内部**向下滚动**（overflow-y），不要横向撑开、不要挤压左侧视频；左右两部分都要能同时看到。

**技术栈**：React + TypeScript，Tailwind CSS，响应式（md/lg 断点）。

---

## 二、当前结构简述

- **ChatPage.tsx**：页面容器，有 `max-w-6xl` 的 div，内部在匹配成功后渲染 `<Room />`，已用 `<div className="w-full min-w-0 flex-1 ...">` 包裹 Room，保证 Room 占满可用宽度。
- **Room.tsx**：1v1 主区域。
  - **小屏**：`flex flex-col`，上视频、下任务。
  - **md 及以上**：`md:grid` 两列，左列视频、右列任务；左列 `minmax(360px,1fr)`（lg 为 `minmax(400px,2fr)`），右列固定 **22rem**；右侧区域设了 `overflow-x-hidden`、`overflow-y-auto`、`break-words`，任务块有 `max-h-48 overflow-y-auto`。

即便这样，在部分环境/分辨率下仍可能出现**右侧被内容撑宽、挤压左侧视频**的情况，希望得到更稳妥的布局方案或排查思路。

---

## 三、Room.tsx 中与布局相关的 return 片段

```tsx
  return (
    <div className="relative w-full h-full flex flex-col min-h-[26rem] md:min-h-[29rem] md:grid md:grid-cols-[minmax(360px,1fr)_22rem] lg:grid-cols-[minmax(400px,2fr)_22rem] md:h-[29rem] lg:h-[31rem] 2xl:h-[41rem]">
      {/* 左侧视频区 */}
      <div className="relative flex-1 min-h-[24rem] z-10 sticky top-0 md:relative md:min-w-[360px] bg-gray-50 md:bg-transparent flex flex-col">
        <div className="relative m-4 flex-1 min-h-[22rem] h-[24rem] md:h-[27rem] lg:h-[29rem] 2xl:h-[39rem] flex items-center justify-center bg-white bg-opacity-50 rounded-lg overflow-hidden shadow-lg shrink-0">
          {/* 远端视频 <video ref={remoteVideoRef} />、加载中、本地小窗等 */}
        </div>
      </div>

      {/* 右侧任务/聊天区：期望固定 22rem 宽，长内容向下滚动 */}
      <div className="h-full w-full flex flex-col border-l border-gray-300 bg-white z-0 min-w-0 max-w-full overflow-x-hidden overflow-y-auto">
        {dialoguePayload && (
          <div className="p-3 border-b border-gray-200 bg-gray-50 text-sm overflow-y-auto max-h-48 min-w-0 shrink-0 break-words">
            <div className="text-xs text-gray-500 mb-1.5 break-words">本局主题：…</div>
            <div className="font-semibold text-indigo-600 break-words">第{round}轮 · 你扮演：…</div>
            {currentTask && (
              <div className="mt-1 text-gray-700 break-words">
                <span className="font-medium">你的任务：</span>
                {currentTask}
              </div>
            )}
            {currentLines.length > 0 && (
              <div className="mt-2 min-w-0 break-words">
                <span className="font-medium text-gray-700">你可说的内容：</span>
                <ul className="list-disc list-inside mt-0.5 text-gray-600 break-words">
                  {currentLines.map((line, i) => (
                    <li key={i} className="break-words">{line.content || line.hint || ""}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
        <div className="flex-1 min-h-0 min-w-0 overflow-hidden flex flex-col">
          <ChatSection ... />
        </div>
        <div className="p-2 border-t border-gray-200 flex flex-wrap gap-2">
          {/* 互换角色按钮等 */}
        </div>
      </div>
    </div>
  );
```

---

## 四、ChatPage.tsx 中渲染 Room 的容器

```tsx
        <div className={`w-full max-w-6xl min-w-0 bg-gray-200 ... flex flex-col md:flex-row overflow-hidden ${...}`}>
          { ... ? (
            <div className="w-full min-w-0 flex-1 flex flex-col md:flex-row">
              <Room ... />
            </div>
          ) : (
            // 未匹配时的占位 + 右侧 Join 等
          )}
        </div>
```

---

## 五、已做过的尝试（简要）

1. 用 **flex** 左右分栏：右侧 `w-full` 在横排时占满，把视频挤没 → 改为限制右侧 `max-w-[22rem]` 等，仍出现过右侧撑开的情况。
2. 改为 **Grid**：`grid-cols-[minmax(360px,1fr)_22rem]`，左列保证最小宽，右列固定 22rem。
3. 右侧容器：`overflow-x-hidden`、`overflow-y-auto`、`min-w-0`、`max-w-full`；任务块 `break-words`、`max-h-48`、`overflow-y-auto`。
4. ChatPage 父级加 `min-w-0`，Room 外包一层 `w-full min-w-0 flex-1`，避免 flex 子项默认 min-width 把整行撑开。

---

## 六、期望与待确认

- **期望**：右侧任务区视觉上固定宽度（约 22rem），不随内容变宽；长任务在右侧内部换行 + 纵向滚动；左侧视频区宽度稳定，不被挤压。
- **若仍被挤压**：可能原因包括 Grid 列被内容撑开、某子元素有隐式 min-width、或 iframe/嵌入环境宽度较小等；希望得到更稳妥的 CSS（或 Tailwind）写法或排查步骤。

如需完整文件，可提供：`varta/client/src/components/Room.tsx`、`varta/client/src/pages/ChatPage.tsx`。

---

## 七、为什么修改没在浏览器里生效（必读）

**现象**：改动了 `varta/client/src/components/Room.tsx`（例如删掉 `lg:w-1/3`、加 `md:w-[350px]`），但浏览器里该元素仍显示 `lg:w-1/3`、宽度约 889px。

**原因**：你访问的是**主站（Flask）**提供的 1v1 页面，主站加载的是 **`app/static/practice-live/`** 下的**已构建好的 JS/CSS**，不是 `varta/client` 的源码。  
源码改完后若**没有重新构建并覆盖** `app/static/practice-live/`，浏览器会一直用旧 bundle（例如 `main.ca4c2ba1.js`），里面仍包含 `lg:w-1/3`。

**正确流程**：

1. **改源码**：只改 `varta/client/src/` 下的 `Room.tsx`、`ChatPage.tsx`、`index.css` 等。
2. **重新构建并部署到主站静态目录**：在项目根目录执行  
   `npm run build:practice-live`  
   脚本会在 `varta/client` 里执行 `npm run build`，并把 `varta/client/build/` 的内容**整体复制**到 `app/static/practice-live/`（会清空该目录再复制），这样主站会加载新的 `main.xxxxx.js`。
3. **浏览器硬刷新**：主站部署/重启后，在 1v1 页面按 **Ctrl+F5**（或 Cmd+Shift+R）强制刷新，避免用旧缓存。

**如何确认生效**：用开发者工具选中右侧任务区 div，看其 class 是否包含 `room-right-panel`、`md:w-[350px]`、`shrink-0`，且**不再**出现 `lg:w-1/3`；宽度应为约 350px 而非约 889px。

---

## 八、布局改完后「无法匹配」的说明

**结论**：仅改右侧宽度/父级 `overflow-hidden` 的布局修改**不会**影响匹配逻辑（Socket 连接、user-info、队列、匹配均在 Room 内独立运行）。若出现「无法匹配」，通常是环境或配置问题，与本次布局改动无关。

**前端已做**：在 Room 内增加了 Socket **连接失败**提示。若连不上匹配服务器，会显示红色错误文案（如「连接匹配服务器失败」），并提示检查主站 VARTA_BACKEND_URL、Varta 服务是否运行。

**请按顺序排查**（详见 `docs/PRACTICE_LIVE_TROUBLESHOOTING.md`）：
1. 看 1v1 页导航栏「后端: xxx」是否为你的 Varta 公网地址；若不对，需设 `REACT_APP_VARTA_BACKEND_URL` 后重新 `npm run build:practice-live` 并部署。
2. 主站环境变量 **VARTA_BACKEND_URL** 是否与上述地址一致。
3. 浏览器 Network：点 Join 后是否有到 Varta 的 WebSocket 请求；Console 是否有 CORS/连接报错。
4. 匹配需**至少两人**同时在线并点击 Join；可用两个浏览器或隐身窗口各点 Join 测试。
