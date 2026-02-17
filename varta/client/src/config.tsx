// 生产环境：Railway 部署时在「前端 Service」里设置 REACT_APP_VARTA_BACKEND_URL 为后端公网地址
const config = {
  backendUrl:
    process.env.NODE_ENV === "production"
      ? process.env.REACT_APP_VARTA_BACKEND_URL || "https://varta-server.onrender.com"
      : "http://localhost:5001",
};

export default config;
  