(() => {
  function q(sel, root=document) { return root.querySelector(sel); }
  function qa(sel, root=document) { return Array.from(root.querySelectorAll(sel)); }

  async function fetchJSON(url) {
    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    return await res.json();
  }

  // 注意：不使用前端硬编码回退，所有场景由后端 dialogues.json 驱动

  function openModal() {
    const modal = q('#scenesModal');
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
    document.body.classList.add('scenes-modal-open');
  }
  function closeModal() {
    const modal = q('#scenesModal');
    modal.style.display = 'none';
    document.body.style.overflow = '';
    document.body.classList.remove('scenes-modal-open');
    // Reset to list view
    q('#sceneViewPane').style.display = 'none';
    q('#scenesListPane').style.display = 'block';
    q('#scenesBackBtn').style.display = 'none';
  }

  function renderBigScenesList(scenes) {
    const container = q('#scenesList');
    container.innerHTML = '';
    scenes.forEach(s => {
      const card = document.createElement('div');
      card.className = 'scene-card';
      card.innerHTML = `
        <img src="${s.image}" alt="${s.name || s.title}" />
        <h3>${s.name || s.title}</h3>
        <button class="enter-btn big" data-id="${s.id}" data-name="${s.name || s.title}">进入</button>
      `;
      container.appendChild(card);
    });
    qa('.enter-btn.big', container).forEach(btn => {
      btn.addEventListener('click', (e) => {
        const id = e.currentTarget.dataset.id;
        const name = e.currentTarget.dataset.name;
        loadSmallScenes(id, name);
      });
    });
  }

  function renderSmallScenesList(scenes, bigSceneName) {
    const container = q('#scenesList');
    container.innerHTML = '';
    if (!scenes || scenes.length === 0) {
      container.innerHTML = `<div style="padding:24px;text-align:center;color:#666;"><p>该类目暂无可体验的小场景</p></div>`;
      return;
    }
    scenes.forEach(s => {
      const card = document.createElement('div');
      card.className = 'scene-card';
      card.innerHTML = `
        <img src="${s.image}" alt="${s.title}" />
        <h3>${s.title}</h3>
        <button class="enter-btn small" data-id="${s.id}" data-small="${s.small_scene_id}">进入</button>
      `;
      container.appendChild(card);
    });
    qa('.enter-btn.small', container).forEach(btn => {
      btn.addEventListener('click', (e) => {
        const id = e.currentTarget.dataset.id;
        loadScene(id);
      });
    });
  }

  async function loadSmallScenes(bigSceneId, bigSceneName) {
    try {
      const res = await fetchJSON('/api/scene-npc/immersive-small-scenes?big_scene_id=' + encodeURIComponent(bigSceneId));
      const scenes = res.scenes || [];
      renderSmallScenesList(scenes, bigSceneName);
      // 显示回退到大场景的按钮
      const backBtn = q('#scenesBackBtn');
      if (backBtn) {
        backBtn.style.display = 'inline-block';
        backBtn.dataset.level = 'big';
      }
      q('#scenesModalTitle').textContent = bigSceneName || '小场景';
    } catch (e) {
      console.error('无法加载小场景：', e);
      q('#scenesList').innerHTML = '<div style="padding:24px;text-align:center;color:#666;"><p>无法加载小场景，请稍后重试</p></div>';
    }
  }

  function renderSceneView(scene) {
    const view = q('#sceneView');
    view.innerHTML = '';
    const container = document.createElement('div');
    container.className = 'scene-container';
    container.style.backgroundImage = `url('${scene.image}')`;
    const header = document.createElement('div');
    header.className = 'scene-header';
    header.innerHTML = `<h2 style="color:#fff;margin:0;">${scene.title}</h2>`;
    container.appendChild(header);
    const npcLayer = document.createElement('div');
    npcLayer.className = 'npc-layer';
    const smallSceneId = scene.small_scene_id || scene.id;
    scene.npcs.forEach(npc => {
      const el = document.createElement('div');
      el.className = 'npc';
      el.dataset.character = npc.character;
      el.dataset.smallSceneId = smallSceneId;
      el.dataset.npcId = npc.id;
      el.innerHTML = `<div class="npc-avatar"></div><div class="npc-label">${npc.label}</div><div class="npc-hint">${npc.hint}</div>`;
      el.addEventListener('click', () => {
        openPrefabDialogue(npc.label, smallSceneId, npc.id);
      });
      npcLayer.appendChild(el);
    });
    container.appendChild(npcLayer);
    view.appendChild(container);
  }

  async function openPrefabDialogue(label, smallSceneId, npcId) {
    const chatModal = q('#sceneChatModal');
    chatModal.style.display = 'block';
    q('#sceneChatTitle').textContent = label;
    const body = q('#sceneChatBody');
    const inputRow = document.querySelector('.scene-chat-input-row');
    if (inputRow) inputRow.style.display = 'none';
    body.innerHTML = '<div class="prefab-loading">加载对话中...</div>';
    try {
      const res = await fetch(`/api/scene-npc/dialogue/immersive?small_scene_id=${encodeURIComponent(smallSceneId)}&npc_id=${encodeURIComponent(npcId)}`);
      const data = await res.json();
      if (!data.dialogue || !data.dialogue.content) {
        body.innerHTML = '<div class="prefab-error">暂无对话内容</div>';
        return;
      }
      body.innerHTML = '';
      const content = data.dialogue.content;
      let idx = 0;
      const msgWrap = document.createElement('div');
      msgWrap.className = 'prefab-messages';
      body.appendChild(msgWrap);
      function showNext() {
        if (idx >= content.length) {
          msgWrap.innerHTML += '<div class="prefab-done" style="padding:12px;color:#4caf50;font-weight:600;">✓ 对话完成</div>';
          if (nextBtn) nextBtn.style.display = 'none';
          return;
        }
        const item = content[idx++];
        const who = item.role === 'A' ? 'user' : 'ai';
        const name = item.role === 'A' ? '我' : label;
        const div = document.createElement('div');
        div.className = `message ${who}`;
        div.innerHTML = `<span class="prefab-name">${name}:</span> ${item.content}`;
        if (item.hint) div.title = item.hint;
        msgWrap.appendChild(div);
        body.scrollTop = body.scrollHeight;
        if (idx >= content.length && nextBtn) nextBtn.style.display = 'none';
      }
      const nextBtn = document.createElement('button');
      nextBtn.className = 'prefab-next-btn';
      nextBtn.textContent = '下一句';
      nextBtn.style.cssText = 'margin-top:12px;padding:8px 16px;background:#007bff;color:white;border:none;border-radius:6px;cursor:pointer;';
      nextBtn.addEventListener('click', showNext);
      body.appendChild(nextBtn);
      showNext();
    } catch (e) {
      body.innerHTML = '<div class="prefab-error">加载失败：' + e.message + '</div>';
    }
  }
  function closeSceneChat() {
    const chatModal = q('#sceneChatModal');
    chatModal.style.display = 'none';
    chatModal.dataset.character = '';
    const inputRow = document.querySelector('.scene-chat-input-row');
    if (inputRow) inputRow.style.display = '';
  }

  function appendSceneChat(who, text) {
    const body = q('#sceneChatBody');
    if (!body) return;
    const div = document.createElement('div');
    div.className = `message ${who}`;
    div.textContent = text;
    body.appendChild(div);
    body.scrollTop = body.scrollHeight;
  }

  async function loadScene(id) {
    try {
      let scene;
      try {
        const data = await fetchJSON(`/api/scenes/${id}`);
        scene = data.scene;
      } catch (e) {
        // 不使用前端硬编码回退，严格依赖后端数据
        console.error('加载场景失败：', e);
        alert('无法加载场景（后端未返回该场景或网络错误）');
        return;
      }
      if (!scene) {
        alert('未知场景：' + id);
        return;
      }
      renderSceneView(scene);
      q('#scenesListPane').style.display = 'none';
      q('#sceneViewPane').style.display = 'block';
      q('#scenesBackBtn').style.display = 'inline-block';
      q('#scenesModalTitle').textContent = scene.title;
      // 标记返回按钮行为：从场景视图返回到小场景列表
      const backBtn = q('#scenesBackBtn');
      if (backBtn) backBtn.dataset.level = 'scene';
    } catch (e) {
      console.error(e);
      alert('加载场景失败：' + e.message);
    }
  }

  async function initModal() {
    // 加载后端推导出的大场景（仅包含下有 immersive 小场景的类目）
    try {
      const data = await fetchJSON('/api/scene-npc/big-scenes');
      const scenes = data.big_scenes || [];
      if (scenes && scenes.length) {
        renderBigScenesList(scenes);
      } else {
        q('#scenesList').innerHTML = '<div style="padding:24px;text-align:center;color:#666;"><p>暂无可体验的大场景</p></div>';
      }
    } catch (e) {
      console.error('无法加载大场景：', e);
      q('#scenesList').innerHTML = '<div style="padding:24px;text-align:center;color:#666;"><p>无法加载场景列表，请稍后重试</p></div>';
    }
  }

  // Send chat text from scene chat
  function sendSceneChatText() {
    const input = q('#sceneChatInput');
    const text = input.value && input.value.trim();
    if (!text) return;
    const chatModal = q('#sceneChatModal');
    const character = chatModal.dataset.character;
    appendSceneChat('user', text);
    input.value = '';
    fetch('/api/text/send', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ text: text, character: character || 'english_tutor' })
    }).then(r => r.json()).then(resp => {
      if (resp.status && resp.status !== 'success') {
        appendSceneChat('ai', `Error: ${resp.message || JSON.stringify(resp)}`);
      }
    }).catch(err => {
      appendSceneChat('ai', `Network error: ${err}`);
    });
  }

  // 当场景聊天窗打开时，接收所有 AI 回复（因为场景 NPC 使用 english_tutor 作为后端角色）
  window.addEventListener('ai_message_broadcast', (ev) => {
    const data = ev.detail || {};
    const activeChat = q('#sceneChatModal');
    if (!activeChat || activeChat.style.display !== 'block') return;
    if (data.text) appendSceneChat('ai', data.text);
  });

  // Init handlers
  document.addEventListener('DOMContentLoaded', () => {
    const openBtn = q('#enter-scenes-btn');
    if (openBtn) {
      openBtn.addEventListener('click', (e) => {
        e.preventDefault();
        const modal = q('#scenesModal');
        if (!modal) return;
        openModal();
        initModal();
      });
    }
    const closeBtn = q('#scenesCloseBtn');
    if (closeBtn) closeBtn.addEventListener('click', closeModal);
    const backBtn = q('#scenesBackBtn');
    if (backBtn) backBtn.addEventListener('click', () => {
      const lvl = backBtn.dataset.level || 'big';
      if (lvl === 'scene') {
        // 从场景视图返回到小场景列表
        q('#sceneViewPane').style.display = 'none';
        q('#scenesListPane').style.display = 'block';
        backBtn.dataset.level = 'big';
        q('#scenesModalTitle').textContent = '场景体验';
        backBtn.style.display = 'none';
      } else {
        // 从小场景列表返回到大场景列表
        q('#sceneViewPane').style.display = 'none';
        q('#scenesListPane').style.display = 'block';
        q('#scenesModalTitle').textContent = '场景体验';
        backBtn.style.display = 'none';
      }
    });
    // Scene chat controls
    const sceneSend = q('#sceneChatSend');
    if (sceneSend) sceneSend.addEventListener('click', sendSceneChatText);
    const sceneInput = q('#sceneChatInput');
    if (sceneInput) sceneInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') sendSceneChatText(); });
    const sceneClose = q('#sceneChatClose');
    if (sceneClose) sceneClose.addEventListener('click', closeSceneChat);
  });
})();

