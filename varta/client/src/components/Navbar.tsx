import React from 'react';
import { Link } from "react-router-dom";
import { UserCount } from './UserCount';

/** 从 1v1 返回主站英语学习主界面（嵌入 iframe 时改父页 hash，否则回本站首页） */
function goBackToMain() {
  try {
    if (typeof window !== 'undefined' && window.self !== window.top && window.parent) {
      window.parent.postMessage({ type: 'practice-live-go-back' }, '*');
      (window.parent as Window).location.hash = '#/';
    } else {
      window.location.href = '/';
    }
  } catch {
    window.location.href = '/';
  }
}

export const Navbar: React.FC = () => {
  return (
    <nav className="fixed top-0 left-0 w-full z-50 h-16 border-b border-gray-300 flex items-center justify-between px-6 bg-white overflow-hidden">
      <div className="flex items-center gap-4">
        <Link to="/" className="flex items-center">
          <span
            className="text-3xl font-bold"
            style={{
              fontFamily: "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
              color: "#6366f1",
            }}
          >
            真人练习
          </span>
        </Link>
        <button
          type="button"
          onClick={goBackToMain}
          className="text-sm text-gray-600 hover:text-gray-900 underline"
        >
          返回主界面
        </button>
      </div>

      <div>
        <UserCount />
      </div>
    </nav>
  );
};
