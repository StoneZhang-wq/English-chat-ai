(() => {
  const wsScheme = (location.protocol === "https:") ? "wss" : "ws";
  const wsUrl = `${wsScheme}://${location.host}/ws`;
  let socket = null;

  function connectWS() {
    socket = new WebSocket(wsUrl);
    socket.addEventListener("open", () => {
      console.log("Scene: WebSocket connected");
    });
    socket.addEventListener("message", (ev) => {
      let data = ev.data;
      try {
        const parsed = JSON.parse(data);
        // Handle structured messages
        if (parsed.action === "user_message" && parsed.text) {
          appendMessage("user", parsed.text);
        } else if (parsed.action === "ai_message" && parsed.text) {
          appendMessage("ai", parsed.text);
        } else if (parsed.message) {
          appendMessage("ai", parsed.message);
        } else {
          // fallback: stringify
          appendMessage("ai", JSON.stringify(parsed));
        }
      } catch (e) {
        // Not JSON - plain text
        appendMessage("ai", data);
      }
    });
    socket.addEventListener("close", () => {
      console.log("Scene: WebSocket closed, will retry in 2s");
      setTimeout(connectWS, 2000);
    });
    socket.addEventListener("error", (e) => {
      console.warn("Scene: websocket error", e);
    });
  }

  function appendMessage(who, text) {
    const chatBody = document.getElementById("chatBody");
    if (!chatBody) return;
    const div = document.createElement("div");
    div.className = `message ${who}`;
    div.textContent = text;
    chatBody.appendChild(div);
    chatBody.scrollTop = chatBody.scrollHeight;
  }

  function openChat(characterLabel, characterName) {
    const modal = document.getElementById("chatModal");
    const title = document.getElementById("chatTitle");
    title.textContent = `${characterLabel}`;
    modal.setAttribute("aria-hidden", "false");
    // Clear previous messages
    document.getElementById("chatBody").innerHTML = "";
    // Store selected character on modal for sending
    modal.dataset.character = characterName || "";
  }

  function closeChat() {
    const modal = document.getElementById("chatModal");
    modal.setAttribute("aria-hidden", "true");
    modal.dataset.character = "";
  }

  function sendChatText() {
    const input = document.getElementById("chatInput");
    const text = input.value && input.value.trim();
    if (!text) return;
    const modal = document.getElementById("chatModal");
    const character = modal.dataset.character || "";
    // append user message locally
    appendMessage("user", text);
    input.value = "";
    // POST to existing text API (it will set character server-side and trigger AI through websocket)
    fetch("/api/text/send", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: text, character: character || "english_tutor" })
    }).then(res => res.json()).then(resp => {
      if (resp.status !== "success") {
        appendMessage("ai", `Error: ${resp.message || JSON.stringify(resp)}`);
      }
    }).catch(err => {
      appendMessage("ai", `Network error: ${err}`);
    });
  }

  // Attach event listeners
  window.addEventListener("load", () => {
    connectWS();
    // NPC click handlers
    document.querySelectorAll(".npc").forEach(el => {
      el.addEventListener("click", () => {
        const label = el.querySelector(".npc-label")?.textContent || "NPC";
        const character = el.dataset.character || "";
        openChat(label, character);
      });
    });
    document.getElementById("closeChat").addEventListener("click", closeChat);
    document.getElementById("sendBtn").addEventListener("click", sendChatText);
    document.getElementById("chatInput").addEventListener("keydown", (e) => {
      if (e.key === "Enter") sendChatText();
    });
  });
})();

