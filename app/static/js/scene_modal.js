(() => {
  function q(sel, root=document) { return root.querySelector(sel); }
  function qa(sel, root=document) { return Array.from(root.querySelectorAll(sel)); }

  async function fetchJSON(url) {
    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    return await res.json();
  }

  /** 当前账户名（与 voice_chat 一致），用于场景解锁状态从 Supabase/后端正确按用户拉取 */
  function getSceneAccount() {
    if (typeof window.currentAccountName !== 'undefined' && window.currentAccountName) return window.currentAccountName;
    try {
      if (typeof localStorage !== 'undefined') return localStorage.getItem('current_account') || '';
    } catch (_) {}
    return '';
  }

  function urlWithAccount(path, account) {
    if (!account) return path;
    const sep = path.indexOf('?') >= 0 ? '&' : '?';
    return path + sep + 'account_name=' + encodeURIComponent(account);
  }

  // 缓存：避免切换大/小场景与回退时重复请求，减轻延时
  let cacheBigScenes = null;
  const cacheSmallByBig = {};
  const cacheSceneDetail = {};
  /** 当前所在大场景（从大场景点进小场景后设置），回退时用于恢复小场景列表 */
  let currentBigSceneId = null;
  let currentBigSceneName = null;

  function showListLoading(msg) {
    const container = q('#scenesList');
    if (!container) return;
    container.innerHTML = '<div class="scene-list-loading"><span class="scene-list-spinner"></span><p>' + (msg || '加载中…') + '</p></div>';
  }

  // 注意：不使用前端硬编码回退，所有场景由后端 dialogues.json 驱动

  function openModal() {
    const modal = q('#scenesModal');
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
    document.body.classList.add('scenes-modal-open');
    // 每次打开弹窗清空场景列表缓存，确保拿到最新图片 URL（避免后端换图后仍显示旧图）
    cacheBigScenes = null;
    Object.keys(cacheSmallByBig).forEach(function (k) { delete cacheSmallByBig[k]; });
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
    currentBigSceneId = bigSceneId;
    currentBigSceneName = bigSceneName || '小场景';
    const cached = cacheSmallByBig[bigSceneId];
    if (Array.isArray(cached)) {
      renderSmallScenesList(cached, currentBigSceneName);
      const backBtn = q('#scenesBackBtn');
      if (backBtn) {
        backBtn.style.display = 'inline-block';
        backBtn.dataset.level = 'big';
      }
      q('#scenesModalTitle').textContent = currentBigSceneName;
      return;
    }
    showListLoading('加载小场景…');
    try {
      const acc = getSceneAccount();
      const url = urlWithAccount('/api/scene-npc/immersive-small-scenes?big_scene_id=' + encodeURIComponent(bigSceneId), acc);
      const res = await fetchJSON(url);
      const scenes = res.scenes || [];
      cacheSmallByBig[bigSceneId] = scenes;
      renderSmallScenesList(scenes, currentBigSceneName);
      const backBtn = q('#scenesBackBtn');
      if (backBtn) {
        backBtn.style.display = 'inline-block';
        backBtn.dataset.level = 'big';
      }
      q('#scenesModalTitle').textContent = currentBigSceneName;
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
      const npcImg = npc.image || '';
      const el = document.createElement('div');
      el.className = 'npc' + (learned ? '' : ' npc-locked');
      el.dataset.character = npc.character;
      el.dataset.smallSceneId = smallSceneId;
      el.dataset.npcId = npc.id;
      el.dataset.learned = learned ? '1' : '0';
      el.dataset.npcImage = npcImg;
      el.dataset.npcLabel = npc.label || '';
      el.innerHTML = learned
        ? `
        <span class="npc-badge npc-badge-unlocked">可对话</span>
        <div class="npc-avatar"><img src="${npcImg}" alt="${npc.label}" /></div>
        <div class="npc-label">${npc.label}</div>
        <div class="npc-hint">${npc.hint}</div>
      `
        : `
        <span class="npc-badge npc-badge-locked">未解锁</span>
        <div class="npc-avatar npc-avatar-locked"><img src="${npcImg}" alt="${npc.label}" /><span class="npc-lock-icon">${lockIconSVG}</span></div>
        <div class="npc-label">${npc.label}</div>
        <div class="npc-hint npc-hint-locked">完成学习页对话后解锁</div>
      `;
      el.addEventListener('click', () => {
        if (el.dataset.learned !== '1') return;
        openScenePractice(npc.label, smallSceneId, npc.id, npcImg);
      });
      npcLayer.appendChild(el);
    });
    container.appendChild(npcLayer);
    // 真人 1v1 练习入口（同场景用户互相匹配）
    const acc = getSceneAccount();
    const liveUrl = '/practice/live/chat?scene=' + encodeURIComponent(smallSceneId) + (acc ? '&account=' + encodeURIComponent(acc) : '');
    const liveBar = document.createElement('div');
    liveBar.className = 'scene-1v1-bar';
    liveBar.innerHTML = '<a href="' + liveUrl + '" class="scene-1v1-btn" target="_self">真人 1v1 练习</a>';
    container.appendChild(liveBar);
    view.appendChild(container);
  }

  // 从场景 NPC 进入练习模式（与英语练习相同体验：TTS 播放 + 用户语音输入）
  // 练习 UI 显示在场景内叠加层；对话未准备好前统一显示倒计时，准备好后关闭倒计时并展示练习界面
  async function openScenePractice(label, smallSceneId, npcId, npcImage) {
    const sceneChatModal = q('#sceneChatModal');
    if (sceneChatModal) sceneChatModal.style.display = 'none';
    const overlay = q('#scene-practice-overlay');
    const container = q('#scene-practice-container');
    if (!overlay || !container) {
      alert('场景练习容器未就绪，请刷新页面');
      return;
    }
    const closeCountdown = typeof window.showCountdownOverlay === 'function'
      ? window.showCountdownOverlay('正在准备场景对话', 10)
      : function noop() {};
    try {
      const res = await fetch(`/api/scene-npc/dialogue/immersive?small_scene_id=${encodeURIComponent(smallSceneId)}&npc_id=${encodeURIComponent(npcId)}`);
      const data = await res.json().catch(() => ({}));
      if (res.status === 403) {
        closeCountdown();
        showSceneToast(data.message || data.error || '该角色未解锁，请先在学习页完成该NPC的对话学习');
        return;
      }
      if (!data.dialogue || !data.dialogue.content || !Array.isArray(data.dialogue.content)) {
        closeCountdown();
        alert('暂无对话内容');
        return;
      }

      const content = data.dialogue.content;
      const dialogueLines = content.map(item => ({
        speaker: item.role === 'A' ? 'A' : 'B',
        text: item.content || '',
        hint: item.hint != null ? item.hint : '',  // 始终带上 hint，避免后端收不到
        audio_url: null
      }));
      const dialogue = dialogueLines.map(l => `${l.speaker}: ${l.text}`).join('\n');
      const dialogueId = data.dialogue.dialogue_id || `scene-${smallSceneId}-${npcId}`;
      overlay.style.display = 'flex';
      container.innerHTML = '';
      if (typeof window.startScenePractice === 'function') {
        await window.startScenePractice({
          dialogue,
          dialogue_lines: dialogueLines,
          dialogue_id: dialogueId,
          small_scene_id: smallSceneId,
          npc_id: npcId,
          npc_label: label || '',
          npc_image: npcImage || '',
          targetContainer: container,
          onReady: function () {}
        });
        closeCountdown();
        if (!container.querySelector('#practice-mode-ui')) {
          hideScenePracticeOverlay();
        }
      } else {
        closeCountdown();
        overlay.style.display = 'none';
        alert('练习功能未加载，请刷新页面');
      }
    } catch (e) {
      console.error('启动场景练习失败:', e);
      closeCountdown();
      hideScenePracticeOverlay();
      alert('加载失败：' + (e.message || '请稍后重试'));
    }
  }

  // 练习结束后隐藏叠加层，恢复场景视图；同时清除练习状态，避免主界面输入仍被当作练习回复
  function hideScenePracticeOverlay() {
    const overlay = q('#scene-practice-overlay');
    const container = q('#scene-practice-container');
    if (overlay) overlay.style.display = 'none';
    if (container) container.innerHTML = '';
    document.body.classList.remove('scene-practice-active');
    if (typeof window.clearPracticeStateWhenLeavingScene === 'function') {
      window.clearPracticeStateWhenLeavingScene();
    }
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
    const cached = cacheSceneDetail[id];
    if (cached) {
      renderSceneView(cached);
      q('#scenesListPane').style.display = 'none';
      q('#sceneViewPane').style.display = 'block';
      q('#scenesBackBtn').style.display = 'inline-block';
      q('#scenesModalTitle').textContent = cached.title;
      const backBtn = q('#scenesBackBtn');
      if (backBtn) backBtn.dataset.level = 'scene';
      return;
    }
    // 进入详情时在场景视图区显示 loading，不覆盖 #scenesList，以便回退时能恢复小场景列表
    q('#scenesListPane').style.display = 'none';
    q('#sceneViewPane').style.display = 'block';
    q('#scenesBackBtn').style.display = 'inline-block';
    const backBtn = q('#scenesBackBtn');
    if (backBtn) backBtn.dataset.level = 'scene';
    const view = q('#sceneView');
    view.innerHTML = '<div class="scene-list-loading"><span class="scene-list-spinner"></span><p>进入场景…</p></div>';
    try {
      let scene;
      try {
        const acc = getSceneAccount();
        const url = urlWithAccount('/api/scenes/' + encodeURIComponent(id), acc);
        const data = await fetchJSON(url);
        scene = data.scene;
      } catch (e) {
        console.error('加载场景失败：', e);
        q('#scenesListPane').style.display = 'block';
        q('#sceneViewPane').style.display = 'none';
        alert('无法加载场景（后端未返回该场景或网络错误）');
        return;
      }
      if (!scene) {
        q('#scenesListPane').style.display = 'block';
        q('#sceneViewPane').style.display = 'none';
        alert('未知场景：' + id);
        return;
      }
      cacheSceneDetail[id] = scene;
      renderSceneView(scene);
      q('#scenesModalTitle').textContent = scene.title;
    } catch (e) {
      console.error(e);
      q('#scenesListPane').style.display = 'block';
      q('#sceneViewPane').style.display = 'none';
      alert('加载场景失败：' + e.message);
    }
  }

  async function initModal() {
    if (cacheBigScenes && cacheBigScenes.length > 0) {
      renderBigScenesList(cacheBigScenes);
      return;
    }
    showListLoading('加载场景列表…');
    try {
      const data = await fetchJSON('/api/scene-npc/big-scenes');
      const scenes = data.big_scenes || [];
      cacheBigScenes = scenes;
      if (scenes && scenes.length) {
        renderBigScenesList(scenes);
        // 预取第一个大场景的小场景列表，用户点进时即可秒出
        const firstId = scenes[0].id;
        if (firstId && !cacheSmallByBig[firstId]) {
          const acc = getSceneAccount();
          const url = urlWithAccount('/api/scene-npc/immersive-small-scenes?big_scene_id=' + encodeURIComponent(firstId), acc);
          fetch(url, { cache: 'no-store' }).then(function (r) { return r.json(); }).then(function (res) {
            if (res.scenes && Array.isArray(res.scenes)) cacheSmallByBig[firstId] = res.scenes;
          }).catch(function () {});
        }
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
        // 从场景视图返回到小场景列表：用缓存重新渲染小场景列表，避免空白/loading
        q('#sceneViewPane').style.display = 'none';
        q('#scenesListPane').style.display = 'block';
        backBtn.dataset.level = 'big';
        if (currentBigSceneId && Array.isArray(cacheSmallByBig[currentBigSceneId])) {
          renderSmallScenesList(cacheSmallByBig[currentBigSceneId], currentBigSceneName || '小场景');
        }
        q('#scenesModalTitle').textContent = currentBigSceneName || '场景体验';
        backBtn.style.display = 'inline-block';
      } else {
        // 从小场景列表返回到大场景列表：用缓存重新渲染大场景列表
        q('#sceneViewPane').style.display = 'none';
        q('#scenesListPane').style.display = 'block';
        q('#scenesModalTitle').textContent = '场景体验';
        backBtn.style.display = 'none';
        if (cacheBigScenes && cacheBigScenes.length > 0) {
          renderBigScenesList(cacheBigScenes);
        }
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

