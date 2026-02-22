import React, { useEffect, useState } from 'react';
import config from "../config";

export const UserCount: React.FC = () => {
  const [userCount, setUserCount] = useState<number | null>(null);
  const [fetchError, setFetchError] = useState<string | null>(null);

  const fetchUserCount = async () => {
    try {
      const url = `${config.backendUrl}/user-count`;
      const response = await fetch(url);
      if (response.ok) {
        const data = await response.json();
        setUserCount(data.userCount);
        setFetchError(null);
      } else {
        setFetchError(`HTTP ${response.status}`);
        console.error("Failed to fetch user count", response.status);
      }
    } catch (error) {
      const msg = error instanceof Error ? error.message : "请求失败";
      setFetchError(msg);
      console.error("Error fetching user count:", error);
    }
  };

  useEffect(() => {
    fetchUserCount();
    const interval = setInterval(fetchUserCount, 1000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex flex-col items-end gap-0.5">
      {/* 调试：显示当前请求的后端地址，便于排查匹配不到、active 为 0 的问题 */}
      <span className="text-gray-400 text-xs truncate max-w-[180px]" title={config.backendUrl}>
        后端: {config.backendUrl.replace(/^https?:\/\//, "").split("/")[0]}
      </span>
      <span className="text-gray-700 text-sm font-medium">
        Active User -{" "}
        <span className="text-pink-500 font-bold">
          {userCount !== null ? userCount : "0"}
        </span>
        {fetchError && (
          <span className="text-red-500 text-xs ml-1" title={fetchError}>
            连接失败
          </span>
        )}
      </span>
    </div>
  );
};
