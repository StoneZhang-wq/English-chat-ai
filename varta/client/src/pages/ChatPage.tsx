import React, { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { Room } from "../components/Room";
import { Navbar } from "../components/Navbar";
import UserPermission from "../components/media_permission/UserPermission";
import getBrowserType from "../utils/getBrowser";
import { SendHorizontal } from "lucide-react";
import {
  checkPermissions,
  handleUserPermission,
} from "../components/media_permission/mediaPermissions";

const ChatPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const sceneIdFromUrl = searchParams.get("scene") || undefined;
  const accountFromUrl = searchParams.get("account") || undefined;
  /** 账号：来自 URL，或从父窗口 postMessage 获取（嵌入主站时 URL 可能无 account） */
  const [account, setAccount] = useState<string | null>(() => (accountFromUrl || null));

  const [chatInput, setChatInput] = useState("");
  const [isChatActive, setIsChatActive] = useState(false);
  /** 仅文字模式：用于验证匹配功能，不请求摄像头/麦克风，可恢复原版时移除 */
  const [textOnlyMode, setTextOnlyMode] = useState(false);
  const [isPopoverOpen, setIsPopoverOpen] = useState(false);
  const [localAudioTrack, setLocalAudioTrack] = useState<MediaStreamTrack | null>(null);
  const [localVideoTrack, setLocalVideoTrack] = useState<MediaStreamTrack | null>(null);
  const [userName, setUserName] = useState(() => {
    return localStorage.getItem("username") || "";
  });
  const [learningLanguages, setLearningLanguages] = useState<string[]>(() => {
    const storedLangs = localStorage.getItem("selectedLanguages");
    return storedLangs ? JSON.parse(storedLangs) : [];
  });
  const [error, setError] = useState({ isError: false, errorMsg: "" });
  const browser = getBrowserType();

  const getMediaTracks = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: true,
      });
      setLocalAudioTrack(stream.getAudioTracks()[0]);
      setLocalVideoTrack(stream.getVideoTracks()[0]);
    } catch (error: any) {
      setError({ isError: true, errorMsg: error.message });
    }
  };

  useEffect(() => {
    if (textOnlyMode && isChatActive) return; // 仅文字验证：不请求媒体权限
    if (browser === "Chrome" || "Edge") {
      handleUserPermission(
        isChatActive,
        setIsPopoverOpen,
        getMediaTracks,
        setError
      );
    } else if (isChatActive) {
      getMediaTracks();
    }
  }, [isChatActive, browser, textOnlyMode]);

  useEffect(() => {
    if (browser === "Chrome" || "Edge") {
      checkPermissions(setError);
    }
  }, [isChatActive, browser]);

  // 嵌入主站时若 URL 无 account，向父窗口请求（主站会 postMessage 回复）
  useEffect(() => {
    if (account !== null) return;
    if (typeof window === "undefined" || window.parent === window) {
      setAccount("");
      return;
    }
    const onMessage = (e: MessageEvent) => {
      if (e.data?.type === "practice-live-account") {
        setAccount(e.data.account != null ? String(e.data.account) : "");
        window.removeEventListener("message", onMessage);
      }
    };
    window.addEventListener("message", onMessage);
    window.parent.postMessage({ type: "practice-live-get-account" }, "*");
    const t = setTimeout(() => {
      window.removeEventListener("message", onMessage);
      setAccount((prev) => (prev === null ? "" : prev));
    }, 800);
    return () => {
      clearTimeout(t);
      window.removeEventListener("message", onMessage);
    };
  }, [account]);

  if (error.isError) {
    console.log(error.errorMsg);
  }


  const joinExitHandler = () => {
    setIsChatActive((prev) => {
      if (prev) setTextOnlyMode(false);
      return !prev;
    });
  };

  const joinTextOnlyHandler = () => {
    setTextOnlyMode(true);
    setIsChatActive(true);
  };

  return (
    <>
      <Navbar />
      <div className="bg-gray-100 flex flex-col items-center p-4 pt-20 mt-0 min-h-screen overflow-hidden ">
        {/*backdrop blur when popover is open */}
        {isPopoverOpen && (
          <div className="fixed inset-0 bg-gray-900/30 backdrop-blur-sm z-40"></div>
        )}

        <div
          className={`w-full max-w-6xl min-w-0 bg-gray-200 shadow-lg rounded-lg flex flex-col md:flex-row overflow-hidden ${
            isPopoverOpen ? "blur-sm" : ""
          }`}
        >
          {/* 真人练习 Room：需占满宽度，内部左右分栏由 Room 自己 grid 控制 */}

          {!isPopoverOpen &&
          isChatActive &&
          (textOnlyMode || (localAudioTrack?.enabled && localVideoTrack?.enabled)) ? (
            account === null ? (
              <div className="flex-1 flex items-center justify-center text-gray-500 p-4">
                正在获取账号，请稍候…
              </div>
            ) : (
              <div className="w-full min-w-0 flex-1 flex flex-col md:flex-row">
                <Room
                  name={userName || "Anonymous"}
                  account={account ?? undefined}
                  learningLanguages={learningLanguages}
                  sceneId={sceneIdFromUrl}
                  localAudioTrack={textOnlyMode ? null : localAudioTrack}
                  localVideoTrack={textOnlyMode ? null : localVideoTrack}
                  chatInput={chatInput}
                  setChatInput={setChatInput}
                  joinExitHandler={joinExitHandler}
                  joinExitLabel="Exit"
                  textOnlyMode={textOnlyMode}
                />
              </div>
            )
          ) : (
            <>
              <div className="flex-1 relative bg-gray-200 p-4 flex flex-col items-center justify-center min-h-[26rem] md:h-[29rem] lg:h-[31rem] 2xl:h-[41rem]">
                <p className="text-gray-500 mt-8 mx-auto">
                  点击 Join 开始匹配同场景的练习伙伴
                </p>
                <p className="text-green-700 text-sm mt-2 font-medium">使用视频+语音：点「Join（视频+语音）」并允许摄像头与麦克风</p>
                <p className="text-gray-400 text-sm mt-1">仅文字聊天：点「仅文字（验证用）」</p>
              </div>
              {/* Chat Section */}
              <div className="lg:w-1/3 bg-white border-l border-gray-300 lg:pl-4">
                <div className="flex flex-col h-full">
                  <div className="flex-grow overflow-y-auto p-4 min-h-[7rem]">
                    <p className="text-gray-700">Chat messages...</p>
                  </div>

                  <div className="flex items-center border-t p-2 flex-wrap gap-2">
                    <button
                      className="text-white bg-[#6366f1] py-2 px-4 rounded-lg"
                      onClick={() => setIsChatActive((prev) => !prev)}
                    >
                      {isChatActive ? "Exit" : "Join（视频+语音）"}
                    </button>
                    <button
                      className="text-[#6366f1] border border-[#6366f1] bg-white py-2 px-4 rounded-lg"
                      onClick={joinTextOnlyHandler}
                    >
                      仅文字（验证用）
                    </button>

                    <div className="relative w-full">
                      <input
                        type="text"
                        className="w-full p-2 pr-10 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-400"
                        placeholder="Type a message..."
                        disabled={true}
                      />
                      <button
                        className="absolute inset-y-0 right-0 flex items-center pr-3 text-indigo-400"
                        disabled={true}
                      >
                        <SendHorizontal />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>

        {isPopoverOpen && (
          <UserPermission
            setIsPopoverOpen={setIsPopoverOpen}
            isPopoverOpen={isPopoverOpen}
            setLocalAudioTrack={setLocalAudioTrack}
            setLocalVideoTrack={setLocalVideoTrack}
            setError={setError}
            setName={setUserName}
            setSelectedLanguages={setLearningLanguages}
          />
        )}
      </div>
    </>
  );
};

export default ChatPage;