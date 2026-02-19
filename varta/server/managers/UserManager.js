import mongoose from "mongoose";
import { RoomManager } from "./RoomManager.js";
import { fetchIpDetails } from '../utils/IpService.js';
import { User } from '../models/UserData.js';

// Defining the user structure. 按 sceneId 分队列，同场景用户互相匹配。
export class UserManager {
  constructor() {
    this.users = [];
    /** @type {Record<string, Array<{ name, socket, country, languages, sceneId? }>>} 场景 ID -> 排队用户列表 */
    this.queuesByScene = {};
    this.roomManager = new RoomManager(this);
  }

  _queueKey(sceneId) {
    return sceneId && String(sceneId).trim() ? String(sceneId).trim() : "default";
  }

  _getQueue(sceneId) {
    const key = this._queueKey(sceneId);
    if (!this.queuesByScene[key]) this.queuesByScene[key] = [];
    return this.queuesByScene[key];
  }


  async addUser(name, socket, languages = []) {

    // Fetching  IP details
    const forwarded = socket.handshake.headers['x-forwarded-for'];
    const clientIp = forwarded ? forwarded.split(/, /)[0] : socket.handshake.address;
    const ipDetails = await fetchIpDetails(clientIp);
    const country = ipDetails?.country || 'Unknown';

    // Saving to database (only when MongoDB is connected)
    if (mongoose.connection.readyState === 1) {
      const user_data = new User({
        socketId: socket.id,
        ip: clientIp,
        country,
        otherDetails: ipDetails,
      });
      await user_data.save();
    }

    const user = { name, socket, country, languages };
    this.users.push(user);

    console.log(`User added: ${name}, ID: ${socket.id}, Country: ${country}`);

    socket.emit("lobby", { country });
    this.initHandlers(socket);
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
      const key = user.sceneId != null ? this._queueKey(user.sceneId) : "default";
      const q = this.queuesByScene[key];
      if (q) this.queuesByScene[key] = q.filter((u) => u.socket.id !== socketId);
      const remainingUser = await this.roomManager.getRemainingUser(socketId);
      if (remainingUser) {
        this.reQueueUser(remainingUser);
      }
    }
  }

  // requeue users to get a next match（按场景队列）
  reQueueUser(user) {
    const queue = this._getQueue(user.sceneId);
    if (!queue.some((u) => u.socket.id === user.socket.id)) {
      queue.push(user);
      console.log(`[Requeue] User ${user.socket.id} scene=${user.sceneId || "default"}`);
      this.tryToPairUsers(user.sceneId);
    }
  }

  tryToPairUsers(sceneId) {
    const queue = this._getQueue(sceneId);
    while (queue.length >= 2) {
      const user1 = queue.pop();
      const user2 = queue.pop();
      if (!user1 || !user2 || user1 === user2) {
        console.log("Insufficient users to pair.");
        return;
      }
      this.roomManager.createRoom(user1, user2);
    }
    if (queue.length === 1) {
      console.log(`[Match] scene=${sceneId || "default"} waiting, 1 user in queue`);
    }
  }

  initHandlers(socket) {
    socket.on("user-info", ({ name, languages, sceneId }) => {
      const user = this.users.find(u => u.socket.id === socket.id);
      if (user) {
        user.name = name;
        user.languages = languages;
        user.sceneId = sceneId != null ? String(sceneId).trim() || undefined : undefined;
        const queue = this._getQueue(user.sceneId);
        if (!queue.some(u => u.socket.id === user.socket.id)) {
          queue.push(user);
          this.tryToPairUsers(user.sceneId);
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
