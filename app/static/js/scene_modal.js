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
    hideScenePracticeOverlay();
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

  // SVG 锁图标（避免 emoji 在某些环境下不显示）
  const lockIconSVG = '<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>';

  function showSceneToast(msg) {
    const el = document.createElement('div');
    el.className = 'scene-toast';
    el.textContent = msg;
    el.style.cssText = 'position:fixed;bottom:24px;left:50%;transform:translateX(-50%);background:rgba(0,0,0,0.85);color:#fff;padding:12px 20px;border-radius:8px;font-size:14px;z-index:10002;max-width:90%;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;';
    document.body.appendChild(el);
    setTimeout(() => { if (el.parentNode) el.parentNode.removeChild(el); }, 2500);
  }

  function renderSmallScenesList(scenes, bigSceneName) {
    const container = q('#scenesList');
    container.innerHTML = '';
    if (!scenes || scenes.length === 0) {
      container.innerHTML = `<div style="padding:24px;text-align:center;color:#666;"><p>该类目暂无可体验的小场景</p></div>`;
      return;
    }
    scenes.forEach(s => {
      const canEnter = s.can_enter === true;
      const card = document.createElement('div');
      card.className = 'scene-card' + (canEnter ? '' : ' scene-card-locked');
      card.innerHTML = canEnter
        ? `
        <img src="${s.image}" alt="${s.title}" />
        <h3>${s.title}</h3>
        <button class="enter-btn small" data-id="${s.id}" data-small="${s.small_scene_id}">进入</button>
      `
        : `
        <div class="scene-card-img-wrap">
          <img src="${s.image}" alt="${s.title}" />
          <span class="scene-card-lock-overlay"><span class="scene-card-lock-svg">${lockIconSVG}</span> 未解锁</span>
        </div>
        <h3>${s.title}</h3>
        <span class="scene-card-enter-disabled">需完成学习后进入</span>
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
      const learned = npc.learned === true;
      const el = document.createElement('div');
      el.className = 'npc' + (learned ? '' : ' npc-locked');
      el.dataset.character = npc.character;
      el.dataset.smallSceneId = smallSceneId;
      el.dataset.npcId = npc.id;
      el.dataset.learned = learned ? '1' : '0';
      el.innerHTML = learned
        ? `
        <span class="npc-badge npc-badge-unlocked">可对话</span>
        <div class="npc-avatar"></div>
        <div class="npc-label">${npc.label}</div>
        <div class="npc-hint">${npc.hint}</div>
      `
        : `
        <span class="npc-badge npc-badge-locked">未解锁</span>
        <div class="npc-avatar npc-avatar-locked"><span class="npc-lock-icon">${lockIconSVG}</span></div>
        <div class="npc-label">${npc.label}</div>
        <div class="npc-hint npc-hint-locked">完成学习页对话后解锁</div>
      `;
      el.addEventListener('click', () => {
        if (el.dataset.learned !== '1') return;
        openScenePractice(npc.label, smallSceneId, npc.id);
      });
      npcLayer.appendChild(el);
    });
    container.appendChild(npcLayer);
    view.appendChild(container);
  }

  // 从场景 NPC 进入练习模式（与英语练习相同体验：TTS 播放 + 用户语音输入）
  // 练习 UI 显示在场景内叠加层，保持沉浸式体验
  async function openScenePractice(label, smallSceneId, npcId) {
    const sceneChatModal = q('#sceneChatModal');
    if (sceneChatModal) sceneChatModal.style.display = 'none';
    const overlay = q('#scene-practice-overlay');
    const container = q('#scene-practice-container');
    if (!overlay || !container) {
      alert('场景练习容器未就绪，请刷新页面');
      return;
    }
    try {
      const res = await fetch(`/api/scene-npc/dialogue/immersive?small_scene_id=${encodeURIComponent(smallSceneId)}&npc_id=${encodeURIComponent(npcId)}`);
      const data = await res.json().catch(() => ({}));
      if (res.status === 403) {
        showSceneToast(data.message || data.error || '该角色未解锁，请先在学习页完成该NPC的对话学习');
        return;
      }
      if (!data.dialogue || !data.dialogue.content || !Array.isArray(data.dialogue.content)) {
        alert('暂无对话内容');
        return;
      }
      const content = data.dialogue.content;
      const dialogueLines = content.map(item => ({
        speaker: item.role === 'A' ? 'A' : 'B',
        text: item.content || '',
        hint: item.hint || undefined,
        audio_url: null
      }));
      const dialogue = dialogueLines.map(l => `${l.speaker}: ${l.text}`).join('\n');
      const dialogueId = data.dialogue.dialogue_id || `scene-${smallSceneId}-${npcId}`;
      // 显示练习叠加层，先展示载入提示（此时不允许发消息）
      overlay.style.display = 'flex';
      container.innerHTML = '<div class="scene-practice-loading">正在载入对话，请稍候...</div>';
      // 暂不添加 scene-practice-active，输入区保持不可用
      if (typeof window.startScenePractice === 'function') {
        await window.startScenePractice({
          dialogue,
          dialogue_lines: dialogueLines,
          dialogue_id: dialogueId,
          small_scene_id: smallSceneId,
          npc_id: npcId,
          targetContainer: container,
          onReady: () => {
            // 输入框已嵌入练习界面，无需提升主页面输入区
          }
        });
        // 若练习未成功启动（如参数无效），清理载入状态
        if (!container.querySelector('#practice-mode-ui')) {
          hideScenePracticeOverlay();
        }
      } else {
        overlay.style.display = 'none';
        alert('练习功能未加载，请刷新页面');
      }
    } catch (e) {
      console.error('启动场景练习失败:', e);
      hideScenePracticeOverlay();
      alert('加载失败：' + (e.message || '请稍后重试'));
    }
  }

  // 练习结束后隐藏叠加层，恢复场景视图
  function hideScenePracticeOverlay() {
    const overlay = q('#scene-practice-overlay');
    const container = q('#scene-practice-container');
    if (overlay) overlay.style.display = 'none';
    if (container) container.innerHTML = '';
    document.body.classList.remove('scene-practice-active');
  }
  window.hideScenePracticeOverlay = hideScenePracticeOverlay;
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
      hideScenePracticeOverlay();
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

