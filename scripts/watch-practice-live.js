#!/usr/bin/env node
/**
 * 监听 varta/client 源码与资源，变更后自动执行 build:practice-live，
 * 使 1v1 练习页修改后无需手动构建即可同步到 app/static/practice-live/
 * 用法：npm run watch:practice-live（需先 npm install）
 */
const path = require("path");
const { spawn } = require("child_process");

const projectRoot = path.resolve(__dirname, "..");
const clientDir = path.join(projectRoot, "varta", "client");

function runBuild() {
  console.log("[watch] 检测到变更，执行 build:practice-live ...");
  const child = spawn("npm", ["run", "build:practice-live"], {
    cwd: projectRoot,
    stdio: "inherit",
    shell: true,
  });
  child.on("close", (code) => {
    if (code === 0) console.log("[watch] 构建完成，已同步到 app/static/practice-live/");
    else console.error("[watch] 构建失败，退出码 " + code);
  });
}

let chokidar;
try {
  chokidar = require("chokidar");
} catch (e) {
  console.error("请先安装 chokidar：npm install --save-dev chokidar");
  process.exit(1);
}

if (!require("fs").existsSync(path.join(clientDir, "package.json"))) {
  console.error("varta/client 不存在，无法监听。");
  process.exit(1);
}

const watcher = chokidar.watch(
  [
    path.join(clientDir, "src"),
    path.join(clientDir, "public"),
  ],
  { ignored: /(^|[/\\])(node_modules|build)[/\\]/, ignoreInitial: true }
);

watcher.on("ready", () => {
  console.log("监听 varta/client 中（修改 src 或 public 后会自动构建并同步）...");
});

watcher.on("change", () => runBuild());
watcher.on("add", () => runBuild());
watcher.on("unlink", () => runBuild());
