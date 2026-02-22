// 生产环境：Railway 部署时在「前端 Service」里设置 REACT_APP_VARTA_BACKEND_URL 为后端公网地址
// REACT_APP_ICE_SERVERS：可选，JSON 数组，如 [{"urls":"stun:..."},{"urls":"turn:...","username":"...","credential":"..."}]，用于手机与电脑互通时 TURN 中继
function getIceServers(): RTCIceServer[] {
  try {
    const raw = process.env.REACT_APP_ICE_SERVERS;
    if (raw && typeof raw === "string") {
      const parsed = JSON.parse(raw) as RTCIceServer[];
      if (Array.isArray(parsed) && parsed.length > 0) return parsed;
    }
  } catch (_) {}
  return [
    { urls: "stun:stun.l.google.com:19302" },
    { urls: "stun:stun1.l.google.com:19302" },
  ];
}

// 优先用主站运行时下发的地址（/api/practice-live/config），部署主站后改 VARTA_BACKEND_URL 即生效，无需重构建 1v1
function getBackendUrl(): string {
  if (typeof window !== "undefined" && window.__VARTA_BACKEND_URL__) {
    return window.__VARTA_BACKEND_URL__;
  }
  if (process.env.NODE_ENV === "production") {
    return process.env.REACT_APP_VARTA_BACKEND_URL || "https://varta-server.onrender.com";
  }
  return "http://localhost:5001";
}

const config = {
  get backendUrl() {
    return getBackendUrl();
  },
  iceServers: getIceServers(),
};

export default config;
  