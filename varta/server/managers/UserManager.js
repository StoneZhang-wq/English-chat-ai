import mongoose from "mongoose";
import { RoomManager } from "./RoomManager.js";
import { fetchIpDetails } from '../utils/IpService.js';
import { User } from '../models/UserData.js';

// 真人 1v1：单队列，有人就配对；主题从两人已解锁场景的交集（无则并集）随机选一。
const GLOBAL_QUEUE_KEY = "default";

export class UserManager {
  constructor() {
    this.users = [];
    /** 单队列：所有等待匹配的用户 */
    this.queuesByScene = { [GLOBAL_QUEUE_KEY]: [] };
    this.roomManager = new RoomManager(this);
  }

  _getQueue() {
    if (!this.queuesByScene[GLOBAL_QUEUE_KEY]) this.queuesByScene[GLOBAL_QUEUE_KEY] = [];
    return this.queuesByScene[GLOBAL_QUEUE_KEY];
  }

  _emitQueueCount() {
    const queue = this._getQueue();
    const count = queue.length;
    queue.forEach(u => u.socket.emit("queue-count", { count }));
  }


  addUser(name, socket, languages = []) {
    // 先立即把用户加入列表并注册 user-info 等处理器，否则客户端连接后马上发的 user-info 会因尚未注册而丢失，导致「当前正在匹配中：0人」
    const user = { name, socket, country: 'Unknown', languages, account: undefined };
    this.users.push(user);
    this.initHandlers(socket);

    console.log(`User added: ${name}, ID: ${socket.id} (country resolving in background)`);

    socket.emit("lobby", { country: 'Unknown' });

    // IP/国家在后台解析，解析完后更新 user.country，不影响入队与 queue-count
    const forwarded = socket.handshake.headers['x-forwarded-for'];
    const clientIp = forwarded ? forwarded.split(/, /)[0] : socket.handshake.address;
    fetchIpDetails(clientIp).then((ipDetails) => {
      const country = ipDetails?.country_code || ipDetails?.country || 'Unknown';
      user.country = country;
      socket.emit("lobby", { country });
      if (mongoose.connection.readyState === 1) {
        const user_data = new User({
          socketId: socket.id,
          ip: clientIp,
          country,
          otherDetails: ipDetails,
        });
        user_data.save().catch((err) => console.error("User save error:", err.message));
      }
      console.log(`User ${socket.id} country resolved: ${country}`);
    }).catch((err) => {
      console.warn("fetchIpDetails failed:", err?.message || err);
    });
  }

  // handels case when user disconnects/ pressed exit to get next match.
  async removeUser(socketId, isIntentionalExit = false) {
    const user = this.users.find((u) => u.socket.id === socketId);
    if (!user) return;

    // Intentional exit: requeue, else full cleanup
    if (isIntentionalExit) {
      this.roomManager.removeUserFromRooms(socketId);
    } else {
      this.users = this.users.filter((u) => u.socket.id !== socketId);
      const q = this._getQueue();
      this.queuesByScene[GLOBAL_QUEUE_KEY] = q.filter((u) => u.socket.id !== socketId);
      this._emitQueueCount();
      const remainingUser = await this.roomManager.getRemainingUser(socketId);
      if (remainingUser) {
        this.reQueueUser(remainingUser);
      }
    }
  }

  reQueueUser(user) {
    const queue = this._getQueue();
    if (!queue.some((u) => u.socket.id === user.socket.id)) {
      queue.push(user);
      this._emitQueueCount();
      this.tryToPairUsers();
    }
  }

  _pickTheme(user1, user2) {
    const a = new Set(Array.isArray(user1.unlockedScenes) ? user1.unlockedScenes : []);
    const b = new Set(Array.isArray(user2.unlockedScenes) ? user2.unlockedScenes : []);
    let pool = [...a].filter(x => b.has(x));
    let source = 'intersection';
    if (pool.length === 0) {
      pool = [...new Set([...a, ...b])];
      source = 'union';
    }
    if (pool.length === 0) return { smallSceneId: null, source: 'random' };
    return { smallSceneId: pool[Math.floor(Math.random() * pool.length)], source };
  }

  tryToPairUsers() {
    const queue = this._getQueue();
    while (queue.length >= 2) {
      const user1 = queue.pop();
      const user2 = queue.pop();
      if (!user1 || !user2 || user1 === user2) {
        if (user1 && !queue.some(u => u.socket.id === user1.socket.id)) queue.push(user1);
        if (user2 && user2 !== user1 && !queue.some(u => u.socket.id === user2.socket.id)) queue.push(user2);
        this._emitQueueCount();
        return;
      }
      const { smallSceneId, source } = this._pickTheme(user1, user2);
      const n1 = (user1.unlockedScenes || []).length;
      const n2 = (user2.unlockedScenes || []).length;
      console.log(`Match: ${user1.name} (${user1.account || 'no-account'}) [${n1} unlocks] + ${user2.name} (${user2.account || 'no-account'}) [${n2} unlocks] -> theme ${smallSceneId || 'random'} (${source})`);
      this.roomManager.createRoom(user1, user2, smallSceneId);
      this._emitQueueCount();
    }
    this._emitQueueCount();
  }

  initHandlers(socket) {
    socket.on("user-info", ({ name, account, languages, sceneId, unlockedScenes }) => {
      const user = this.users.find(u => u.socket.id === socket.id);
      if (user) {
        user.name = name || user.name;
        user.account = account != null ? String(account).trim() || undefined : undefined;
        user.languages = languages || user.languages;
        user.sceneId = sceneId != null ? String(sceneId).trim() || undefined : undefined;
        user.unlockedScenes = Array.isArray(unlockedScenes) ? unlockedScenes : [];
        const queue = this._getQueue();
        if (!queue.some(u => u.socket.id === user.socket.id)) {
          queue.push(user);
          this._emitQueueCount();
          this.tryToPairUsers();
        }
      }
    });

    socket.on("offer", ({ sdp, roomId }) => {
      console.log("check1- RoomId:", roomId);
      this.roomManager.onOffer(roomId, sdp, socket.id);
    });

    socket.on("answer", ({ sdp, roomId }) => {
      console.log("check2- RoomId:", roomId);
      this.roomManager.onAnswer(roomId, sdp, socket.id);
    });

    socket.on("add-ice-candidate", ({ candidate, roomId, type }) => {
      // console.log("check3- RoomId:", roomId);
      this.roomManager.onIceCandidates(roomId, socket.id, candidate, type);
    });

    // Handle user exit event
    socket.on("user-exit", ({ name }) => {
      console.log(`User ${name} exited. Re-queuing for matching...`);
      this.removeUser(socket.id, true);
    });

    socket.on("disconnect", () => {
      console.log(`User disconnected: ${socket.id}`);
      this.removeUser(socket.id);
    });
  }

  getUserCount() {
    return this.users.length; //  retrieve the number of connected users
  }
}
