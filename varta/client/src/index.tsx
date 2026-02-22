import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

declare global {
  interface Window {
    __VARTA_BACKEND_URL__?: string;
  }
}

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

// 运行时从主站拉取 Varta 地址，避免构建时写死；部署主站后改 VARTA_BACKEND_URL 即可生效，无需重构建 1v1
async function initRuntimeConfig() {
  try {
    const origin = typeof window !== 'undefined' ? window.location.origin : '';
    if (!origin) return;
    const r = await fetch(`${origin}/api/practice-live/config`);
    if (r.ok) {
      const data = await r.json();
      const url = (data?.backendUrl || '').trim().replace(/\/+$/, '');
      if (url) window.__VARTA_BACKEND_URL__ = url;
    }
  } catch (_) {}
}

initRuntimeConfig().then(() => {
  root.render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
});

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals

