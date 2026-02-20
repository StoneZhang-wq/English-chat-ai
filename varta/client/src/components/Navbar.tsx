import React from 'react';
import { Link } from "react-router-dom";
import { UserCount } from './UserCount';

export const Navbar: React.FC = () => {
  return (
    <nav className="fixed top-0 left-0 w-full z-50 h-16 border-b border-gray-300 flex items-center justify-between px-6 bg-white overflow-hidden">
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

      <div>
        <UserCount />
      </div>
    </nav>
  );
};
