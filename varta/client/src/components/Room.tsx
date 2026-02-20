import { useEffect, useCallback, useRef, useState,useMemo } from "react";
import { Socket, io } from "socket.io-client";
import { HashLoader } from "react-spinners";
import config from "../config";
import ChatSection from "./ChatSection";

const URL = `${config.backendUrl}`;

interface OfferPayload {
  sdp: RTCSessionDescriptionInit;
  roomId: string;
}

interface AnswerPayload {
  sdp: RTCSessionDescriptionInit;
}

interface IceCandidatePayload {
  candidate: RTCIceCandidateInit;
  type: string;
  roomId: string;
}

interface Message {
  sender: "self" | "remote";
  content: string;
}

const getApiBase = () => (typeof window !== "undefined" ? window.location.origin : "");

export interface DialoguePayload {
  roleLabelA: string;
  taskA: string;
  linesA: { content?: string; hint?: string }[];
  roleLabelB: string;
  taskB: string;
  linesB: { content?: string; hint?: string }[];
  smallSceneName?: string;
}

export const Room = ({
  name,
  account,
  learningLanguages = [],
  sceneId,
  localAudioTrack,
  localVideoTrack,
  chatInput,
  setChatInput,
  joinExitHandler,
  joinExitLabel,
  textOnlyMode = false,
}: {
  name: string;
  account?: string;
  learningLanguages?: string[];
  sceneId?: string;
  localAudioTrack: MediaStreamTrack | null;
  localVideoTrack: MediaStreamTrack | null;
  chatInput: string;
  setChatInput: (value: string) => void;
  joinExitHandler: () => void;
  joinExitLabel: string;
  textOnlyMode?: boolean;
}) => {
  const [lobby, setLobby] = useState(true);
  const [isMatching, setIsMatching] = useState(false);
  const [queueCount, setQueueCount] = useState(0);
  const [remoteName, setRemoteName] = useState<string | null>(null);
  const [remoteUserCountry, setRemoteUserCountry] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [myRole, setMyRole] = useState<"A" | "B" | null>(null);
  const [dialoguePayload, setDialoguePayload] = useState<DialoguePayload | null>(null);
  const [round, setRound] = useState<1 | 2>(1);
  const [wantSwapSelf, setWantSwapSelf] = useState(false);
  const [remoteWantSwap, setRemoteWantSwap] = useState(false);
  const socketRef = useRef<Socket | null>(null);
  const sendingPcRef = useRef<RTCPeerConnection | null>(null);
  const receivingPcRef = useRef<RTCPeerConnection | null>(null);
  const remoteVideoRef = useRef<HTMLVideoElement | null>(null);
  const localVideoRef = useRef<HTMLVideoElement | null>(null);
  const remoteStreamRef = useRef(new MediaStream());

  const dataChannelRef = useRef<RTCDataChannel | null>(null);

  const initializePeerConnection = (
    type: "sender" | "receiver",
    roomId: string
  ): RTCPeerConnection => {
    const pc = new RTCPeerConnection({
      iceServers: [{ urls: "stun:stun.l.google.com:19302" }],
    });

    pc.onicecandidate = (e) => {
      if (e.candidate) {
        console.log(`Sending ICE candidate from ${type} PC...`);
        socketRef.current?.emit("add-ice-candidate", {
          candidate: e.candidate,
          type,
          roomId,
        });
      }
    };

    pc.ontrack = (e) => {
      console.log("Received remote track:", e.track);
      if (!remoteStreamRef.current.getTrackById(e.track.id)) {
        remoteStreamRef.current.addTrack(e.track);
      }

      if (remoteVideoRef.current) {
        remoteVideoRef.current.srcObject = remoteStreamRef.current;
        remoteVideoRef.current.onloadedmetadata = () => {
          console.log(
            "Remote video metadata loaded, attempting to play video."
          );
          if (remoteVideoRef.current?.paused) {
            remoteVideoRef.current
              .play()
              .catch((err) => console.error("Video playback error:", err));
          }
        };
      }
    };

    pc.ondatachannel = (event) => {
      const channel = event.channel;
      channel.onmessage = (e) => {
        try {
          const parsed = JSON.parse(e.data);
          if (parsed?.type === "want-swap") {
            setRemoteWantSwap(true);
            return;
          }
        } catch (_) {}
        setMessages((prev: Message[]) => [
          ...prev,
          { sender: "remote", content: e.data },
        ]);
      };
    };

    return pc;
  };

  const handleOffer = useCallback(
    async ({ sdp, roomId }: OfferPayload) => {
      console.log("Received offer. Creating answer... RoomId:", roomId);
      setLobby(false);
      // setRoomId(roomId); // Store roomId in state

      const receivingPc = initializePeerConnection("receiver", roomId);
      receivingPcRef.current = receivingPc;

      try {
        await receivingPc.setRemoteDescription(new RTCSessionDescription(sdp));
        console.log("Remote offer set successfully on receiving PC.");

        if (localAudioTrack) {
          receivingPc.addTrack(
            localAudioTrack,
            new MediaStream([localAudioTrack])
          );
          console.log("Added local audio track to receiving PC.");
        }
        if (localVideoTrack) {
          receivingPc.addTrack(
            localVideoTrack,
            new MediaStream([localVideoTrack])
          );
          console.log("Added local video track to receiving PC.");
        }

        const answer = await receivingPc.createAnswer();
        await receivingPc.setLocalDescription(answer);
        console.log("Sending answer SDP...");
        socketRef.current?.emit("answer", { sdp: answer, roomId });
      } catch (error) {
        console.error("Error handling offer:", error);
      }
    },
  [localAudioTrack, localVideoTrack]);

  const handleAnswer = async ({ sdp }: AnswerPayload) => {
    console.log("Received answer. Setting remote description...");
    const sendingPc = sendingPcRef.current;

    if (!sendingPc) {
      console.error("Sending PeerConnection not found.");
      return;
    }

    try {
      await sendingPc.setRemoteDescription(new RTCSessionDescription(sdp));
      console.log("Remote answer description set successfully on sending PC.");
    } catch (error) {
      console.error("Error setting remote answer SDP:", error);
    }
  };

  const handleAddIceCandidate = async ({
    candidate,
    type,
    roomId,
  }: IceCandidatePayload) => {
    console.log(
      "Received ICE candidate from remote:",
      candidate,
      "Type:",
      type
    );
    const pc =
      type === "sender" ? receivingPcRef.current : sendingPcRef.current;

    if (pc) {
      try {
        await pc.addIceCandidate(new RTCIceCandidate(candidate));
        console.log(`Added ICE candidate to ${type} PC.`);
      } catch (error) {
        console.error(
          `Error adding received ICE candidate to ${type} PC:`,
          error
        );
      }
    } else {
      console.warn(`PeerConnection for type ${type} not found.`);
    }
  };

  const handleSendMessage = () => {
    if (dataChannelRef.current && chatInput.trim()) {
      dataChannelRef.current.send(chatInput);
      setMessages((prev: Message[]) => [
        ...prev,
        { sender: "self", content: chatInput },
      ]);
      setChatInput("");
    }
  };

  const handleWantSwap = () => {
    setWantSwapSelf(true);
    if (dataChannelRef.current) {
      dataChannelRef.current.send(JSON.stringify({ type: "want-swap" }));
    }
  };

  const currentRoleLabel =
    dialoguePayload && myRole
      ? myRole === "A"
        ? dialoguePayload.roleLabelA
        : dialoguePayload.roleLabelB
      : "";
  const currentTask =
    dialoguePayload && myRole
      ? myRole === "A"
        ? dialoguePayload.taskA
        : dialoguePayload.taskB
      : "";
  const currentLines =
    dialoguePayload && myRole
      ? myRole === "A"
        ? dialoguePayload.linesA
        : dialoguePayload.linesB
      : [];

  useEffect(() => {
    if (!wantSwapSelf || !remoteWantSwap || !dialoguePayload) return;
    setMyRole((r) => (r === "A" ? "B" : "A"));
    setRound(2);
    setWantSwapSelf(false);
    setRemoteWantSwap(false);
  }, [wantSwapSelf, remoteWantSwap, dialoguePayload]);

  const handleExit = () => {
    console.log("Exit button pressed. Cleaning up connections.");
    setDialoguePayload(null);
    setMyRole(null);
    setRound(1);
    setWantSwapSelf(false);
    setRemoteWantSwap(false);
    setIsMatching(true);
    sendingPcRef.current?.close();
    receivingPcRef.current?.close();
    sendingPcRef.current = null;
    receivingPcRef.current = null;
    setMessages([]);
    setRemoteUserCountry(null);
    
    // Clear states after an interval(must be less than removeRoom() in server.)
    setTimeout(() => {
      setLobby(true);
      setIsMatching(false);
    }, 1800); // 1.8-second delay
  
    // Notify the server to requeue the user
    socketRef.current?.emit("user-exit", { name });
  
    // Reset remote video
    if (remoteStreamRef.current) {
      remoteStreamRef.current.getTracks().forEach((track) => track.stop());
      // remoteStreamRef.current = new MediaStream(); // Create fresh stream
    }
  
    if (remoteVideoRef.current) {
      remoteVideoRef.current.srcObject = null;
    }
  };
  
  useEffect(() => {
    const socket = io(URL, {
      transports: ["websocket"],
      withCredentials: true,
    });
    socketRef.current = socket;

    socket.on("connect", async () => {
      let unlockedScenes: string[] = [];
      if (account) {
        try {
          const r = await fetch(
            `${getApiBase()}/api/practice-live/unlocked-scenes?account_name=${encodeURIComponent(account)}`
          );
          if (r.ok) {
            const data = await r.json();
            unlockedScenes = data.small_scene_ids || [];
          }
        } catch (e) {
          console.warn("Failed to fetch unlocked scenes", e);
        }
      }
      socket.emit("user-info", {
        name,
        languages: learningLanguages,
        sceneId: sceneId || undefined,
        unlockedScenes,
      });
    });

    socket.on("queue-count", ({ count }: { count: number }) => {
      setQueueCount(count);
    });

    socket.on("send-offer", async ({ roomId, remoteCountry, name: remoteNameVal, smallSceneId, myRole: role }) => {
      console.log("Received offer. RoomId:", roomId, "smallSceneId:", smallSceneId, "myRole:", role);
      setLobby(false);
      setMessages([]);
      setRemoteUserCountry(remoteCountry && remoteCountry !== "Unknown" ? remoteCountry : null);
      setRemoteName(remoteNameVal || null);
      setMyRole(role || null);
      setRound(1);
      setWantSwapSelf(false);
      setRemoteWantSwap(false);

      if (smallSceneId) {
        try {
          const r = await fetch(
            `${getApiBase()}/api/practice-live/dialogue?small_scene_id=${encodeURIComponent(smallSceneId)}`
          );
          if (r.ok) {
            const data = await r.json();
            setDialoguePayload({
              roleLabelA: data.role_label_a || "角色A",
              taskA: data.task_a || "",
              linesA: data.lines_a || [],
              roleLabelB: data.role_label_b || "学习者",
              taskB: data.task_b || "",
              linesB: data.lines_b || [],
              smallSceneName: data.small_scene_name,
            });
          } else {
            setDialoguePayload(null);
          }
        } catch (e) {
          console.warn("Failed to fetch dialogue", e);
          setDialoguePayload(null);
        }
      } else {
        setDialoguePayload(null);
      }

      const sendingPc = initializePeerConnection("sender", roomId);
      sendingPcRef.current = sendingPc;

      const dataChannel = sendingPc.createDataChannel("chat");
      dataChannelRef.current = dataChannel;

      dataChannel.onmessage = (e) => {
        try {
          const parsed = JSON.parse(e.data);
          if (parsed?.type === "want-swap") {
            setRemoteWantSwap(true);
            return;
          }
        } catch (_) {}
        setMessages((prev) => [...prev, { sender: "remote", content: e.data }]);
      };

      if (localVideoTrack) {
        sendingPc.addTrack(localVideoTrack, new MediaStream([localVideoTrack]));
        console.log("Added local video track to sending PC.");
      }
      if (localAudioTrack) {
        sendingPc.addTrack(localAudioTrack, new MediaStream([localAudioTrack]));
        console.log("Added local audio track to sending PC.");
      }

      try {
        const offer = await sendingPc.createOffer();
        await sendingPc.setLocalDescription(offer);
        console.log("Offer sent.");
        socket.emit("offer", { sdp: offer, roomId });
      } catch (error) {
        console.error("Error creating or sending offer:", error);
      }
    });

    socket.on("offer", handleOffer);
    socket.on("answer", handleAnswer);
    socket.on("add-ice-candidate", handleAddIceCandidate);
    socket.on("room-removed", () => {
      console.log("Room removed. Resetting state...");
      setDialoguePayload(null);
      setMyRole(null);
      setRound(1);
      setWantSwapSelf(false);
      setRemoteWantSwap(false);
      setIsMatching(true);
      sendingPcRef.current?.close();
      receivingPcRef.current?.close();
      sendingPcRef.current = null;
      receivingPcRef.current = null;
      setMessages([]);
      setRemoteUserCountry(null);

      setTimeout(() => {
        setLobby(true);
        setIsMatching(false);
      }, 1800);

      // Reset remote video
      if (remoteStreamRef.current) {
        remoteStreamRef.current.getTracks().forEach((track) => track.stop());
        remoteStreamRef.current = new MediaStream();
      }
      if (remoteVideoRef.current) {
        remoteVideoRef.current.srcObject = null;
      }
    });
    socket.on("disconnect", () => {
      console.log("Socket disconnected. Closing peer connections.");
      sendingPcRef.current?.close();
      receivingPcRef.current?.close();
    });

    return () => {
      // 避免在 React Strict Mode 下对“尚未连接”的 socket 调用 disconnect，否则会报：
      // "WebSocket is closed before the connection is established"
      if (socket.connected) {
        socket.disconnect();
      } else {
        socket.once("connect", () => socket.disconnect());
      }
      sendingPcRef.current?.close();
      receivingPcRef.current?.close();
    };
  }, [localAudioTrack, localVideoTrack, handleOffer, name, learningLanguages, account, sceneId]);

  // Local video rendering effect
  useEffect(() => {
    const videoElement = localVideoRef.current;
    if (videoElement && localVideoTrack) {
      const stream = new MediaStream([localVideoTrack]);
      videoElement.srcObject = stream;
      videoElement.muted = true;

      const handleCanPlay = () => {
        console.log("Local video is ready to play.");
        videoElement.play().catch((err) => console.error("Play error:", err));
      };

      videoElement.addEventListener("canplay", handleCanPlay);

      return () => {
        videoElement.removeEventListener("canplay", handleCanPlay);
      };
    }
  }, [localVideoTrack]);

  // Add useMemo to prevent unnecessary re-renders of video elements
  const videoConstraints = useMemo(
    () => ({
      className: "w-full h-full object-cover",
    }),
    []
  );

  useEffect(() => {
    const currentRemoteVideo = remoteVideoRef.current;
    return () => {
      // Cleanup only when component unmounts
      if (currentRemoteVideo) {
        currentRemoteVideo.srcObject = null;
      }
    };
  }, []);

  return (
    <div className="relative w-full h-full flex flex-col min-h-[26rem] md:h-[29rem] lg:h-[31rem] 2xl:h-[41rem] justify-center md:flex-row ">
      <div className="relative flex-1">
        <div className="relative m-4 flex-1 h-[24rem] md:h-[27rem] lg:h-[29rem] 2xl:h-[39rem] flex items-center justify-center bg-white bg-opacity-50 rounded-lg overflow-hidden shadow-lg">
          {/* Username Label */}
          {!lobby && (
            <div className="absolute top-2 left-4 flex items-center bg-white rounded shadow-lg p-1">
              {remoteUserCountry && (
                <img
                  src={`https://flagcdn.com/16x12/${remoteUserCountry.toLowerCase()}.png`}
                  alt="Country Flag"
                  className="rounded-full size-[1.5rem] mr-2"
                />
              )}
              <span className="text-gray-700 font-semibold">{remoteName}</span>
            </div>
          )}

          {/* Remote Video */}
          <video
            ref={remoteVideoRef}
            autoPlay
            playsInline
            className={videoConstraints.className}
            onContextMenu={(e) => e.preventDefault()}
            key="remote-video" // Static key
          />

          {/* Loading Indicator */}
          {(lobby || isMatching) && (
            <div className="absolute inset-0 flex flex-col items-center justify-center bg-white bg-opacity-50">
              <HashLoader color="#6366f1" />
              <div className="mt-3 text-lg font-medium text-gray-700">
                正在匹配...
              </div>
              <div className="mt-1 text-sm text-gray-500">
                当前正在匹配中：{queueCount} 人
              </div>
            </div>
          )}

          {/* Local Video（仅文字模式不显示） */}
          {!textOnlyMode && (
            <div className="absolute bottom-4 left-4 border border-gray-300 rounded-lg overflow-hidden shadow-lg">
              <video
                ref={localVideoRef}
                autoPlay
                muted
                className="w-20 h-20 md:w-24 md:h-24 object-cover"
              />
            </div>
          )}
          {textOnlyMode && !lobby && !isMatching && (
            <div className="absolute bottom-4 left-4 bg-white/90 rounded-lg px-3 py-2 text-sm text-gray-600">
              仅文字模式（验证匹配）
            </div>
          )}
        </div>
      </div>

      {/* Chat Section + 角色/任务/台词 + 互换与结束 */}
      <div className="h-full lg:w-1/3 flex flex-col border-l border-gray-300 bg-white">
        {dialoguePayload && (
          <div className="p-3 border-b border-gray-200 bg-gray-50 text-sm overflow-y-auto max-h-40">
            <div className="font-semibold text-indigo-600">
              第{round}轮 · 你扮演：{currentRoleLabel}
            </div>
            {currentTask && (
              <div className="mt-1 text-gray-700">
                <span className="font-medium">任务：</span>
                {currentTask}
              </div>
            )}
            {currentLines.length > 0 && (
              <div className="mt-2">
                <span className="font-medium text-gray-700">你可说的内容：</span>
                <ul className="list-disc list-inside mt-0.5 text-gray-600">
                  {currentLines.map((line, i) => (
                    <li key={i}>
                      {line.content || line.hint || ""}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
        <div className="flex-1 min-h-0">
          <ChatSection
            chatInput={chatInput}
            setChatInput={setChatInput}
            messages={messages}
            sendMessage={handleSendMessage}
            joinExitHandler={handleExit}
            joinExitLabel={joinExitLabel}
          />
        </div>
        {!lobby && !isMatching && (
          <div className="p-2 border-t border-gray-200 flex flex-wrap gap-2">
            {round === 1 && dialoguePayload && (
              <button
                type="button"
                onClick={handleWantSwap}
                disabled={wantSwapSelf && remoteWantSwap}
                className="px-3 py-1.5 text-sm rounded-lg border border-indigo-500 text-indigo-600 hover:bg-indigo-50 disabled:opacity-70"
              >
                {wantSwapSelf && remoteWantSwap
                  ? "正在互换…"
                  : wantSwapSelf
                  ? "已点击互换，等待对方"
                  : remoteWantSwap
                  ? "对方已同意，点击互换"
                  : "互换角色"}
              </button>
            )}
            {round === 2 && (
              <span className="text-sm text-gray-500 py-1.5">第二轮对话结束可点击上方 Exit 结束练习</span>
            )}
          </div>
        )}
      </div>
    </div>
  );
};