#!/usr/bin/env node
/**
 * 一键构建真人 1v1 练习前端并复制到 app/static/practice-live/
 * 用法：node scripts/build-practice-live.js
 * 可选环境变量：REACT_APP_VARTA_BACKEND_URL 生产环境 Socket.io 后端地址（在运行前设置后再执行本脚本）
 */
const path = require("path");
const fs = require("fs");
const { spawnSync } = require("child_process");

const projectRoot = path.resolve(__dirname, "..");
const clientDir = path.join(projectRoot, "varta", "client");
const buildDir = path.join(clientDir, "build");
const targetDir = path.join(projectRoot, "app", "static", "practice-live");

function run(cmd, args, cwd) {
  console.log("[run] " + cmd + " " + (args || []).join(" "));
  const r = spawnSync(cmd, args || [], {
    cwd: cwd || projectRoot,
    stdio: "inherit",
    shell: true,
  });
  if (r.status !== 0) {
    console.error("Command failed with status " + r.status);
    process.exit(r.status);
  }
}

function copyRecursive(src, dest) {
  if (!fs.existsSync(src)) {
    console.error("Source does not exist: " + src);
    process.exit(1);
  }
  if (!fs.statSync(src).isDirectory()) {
    fs.copyFileSync(src, dest);
    return;
  }
  if (!fs.existsSync(dest)) fs.mkdirSync(dest, { recursive: true });
  for (const name of fs.readdirSync(src)) {
    const s = path.join(src, name);
    const d = path.join(dest, name);
    if (fs.statSync(s).isDirectory()) {
      copyRecursive(s, d);
    } else {
      fs.copyFileSync(s, d);
    }
  }
}

console.log("Project root:", projectRoot);
console.log("Target dir: ", targetDir);

if (!fs.existsSync(path.join(clientDir, "package.json"))) {
  console.error("varta/client/package.json not found. Aborting.");
  process.exit(1);
}

console.log("\n--- Step 1: npm install in varta/client ---");
run("npm", ["install"], clientDir);

console.log("\n--- Step 2: npm run build in varta/client ---");
run("npm", ["run", "build"], clientDir);

if (!fs.existsSync(buildDir)) {
  console.error("Build output not found at " + buildDir);
  process.exit(1);
}

if (!fs.existsSync(targetDir)) {
  fs.mkdirSync(targetDir, { recursive: true });
  console.log("Created " + targetDir);
}

console.log("\n--- Step 3: Copy build to app/static/practice-live ---");
// 清空目标后复制，避免旧文件残留
for (const name of fs.readdirSync(targetDir)) {
  const p = path.join(targetDir, name);
  if (fs.statSync(p).isDirectory()) fs.rmSync(p, { recursive: true });
  else fs.unlinkSync(p);
}
copyRecursive(buildDir, targetDir);

console.log("\nDone. 真人练习前端已输出到 app/static/practice-live/");
console.log("启动主站后访问 /practice/live 或 /practice/live/chat 即可。");
