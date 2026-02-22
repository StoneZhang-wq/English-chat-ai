(() => {
  console.log('[scene_modal] 脚本已加载');
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
    if (typeof hideImmersiveOverlay === 'function') hideImmersiveOverlay();
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
        <div class="npc-actions">
          <button type="button" class="npc-btn npc-btn-immersive">自由对话</button>
        </div>
      `
        : `
        <span class="npc-badge npc-badge-locked">未解锁</span>
        <div class="npc-avatar npc-avatar-locked"><img src="${npcImg}" alt="${npc.label}" /><span class="npc-lock-icon">${lockIconSVG}</span></div>
        <div class="npc-label">${npc.label}</div>
        <div class="npc-hint npc-hint-locked">完成学习页对话后解锁</div>
      `;
      el.addEventListener('click', (e) => {
        if (el.dataset.learned !== '1') return;
        if (e.target.closest('.npc-actions')) return;
        openImmersiveChat(npc.label, smallSceneId, npc.id);
      });
      if (learned) {
        const btnImmersive = el.querySelector('.npc-btn-immersive');
        if (btnImmersive) btnImmersive.addEventListener('click', (e) => { e.stopPropagation(); openImmersiveChat(npc.label, smallSceneId, npc.id); });
      }
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

  // 剧本练习已移除，仅保留自由对话。此处保留 no-op 供其它处调用不报错。
  function hideScenePracticeOverlay() {
    document.body.classList.remove('scene-practice-active');
    if (typeof window.clearPracticeStateWhenLeavingScene === 'function') {
      window.clearPracticeStateWhenLeavingScene();
    }
  }
  window.hideScenePracticeOverlay = hideScenePracticeOverlay;

  // ---------- 沉浸式自由对话：按剧本流程与 AI 对话，可角色互换，结束后生成纠错报告 ----------
  let immersiveState = { smallSceneId: '', npcId: '', label: '', npcName: '', sceneName: '', history: [], roleSwapped: false, userGoal: '', userGoalA: '', bLines: [], aLines: [] };

  function updateImmersiveTaskText() {
    var taskEl = document.getElementById('sceneImmersiveTask');
    var hintEl = document.getElementById('sceneImmersiveHint');
    if (!taskEl) return;
    var s = immersiveState;
    var swapped = s.roleSwapped;
    var prefix = '你的任务：';
    if (swapped) {
      taskEl.textContent = s.userGoalA ? (prefix + s.userGoalA) : (prefix + '你扮演 ' + (s.npcName || s.label) + '，AI 扮演学习者。请按剧本流程完成对话。');
    } else if (s.userGoal) {
      taskEl.textContent = prefix + s.userGoal;
    } else {
      taskEl.textContent = prefix + '扮演 ' + (s.npcName || s.label) + '，在「' + (s.sceneName || s.smallSceneId) + '」中完成剧本中的对话流程。';
    }
    if (hintEl) {
      var refLines = swapped ? (s.aLines || []) : (s.bLines || []);
      if (refLines.length) {
        hintEl.textContent = '参考（你可以这样说）：' + refLines.join(' → ');
        hintEl.style.display = '';
      } else {
        hintEl.textContent = '';
        hintEl.style.display = 'none';
      }
    }
  }

  var immersiveCurrentAudio = null;
  function appendImmersiveMsg(role, text, audioUrl) {
    const chat = q('#sceneImmersiveChat');
    if (!chat) return;
    const div = document.createElement('div');
    div.className = 'msg ' + role;
    if (audioUrl) {
      var wrap = document.createElement('div');
      wrap.className = 'msg-immersive-with-audio';
      var textSpan = document.createElement('span');
      textSpan.className = 'msg-text';
      textSpan.textContent = text;
      var playBtn = document.createElement('button');
      playBtn.type = 'button';
      playBtn.className = 'msg-play-btn';
      playBtn.title = '播放';
      playBtn.setAttribute('aria-label', '播放');
      playBtn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><polygon points="8 5 8 19 19 12 8 5"></polygon></svg>';
      var audio = new Audio();
      audio.preload = 'auto';
      audio.src = audioUrl;
      playBtn.addEventListener('click', function () {
        if (audio.paused) {
          if (immersiveCurrentAudio && immersiveCurrentAudio !== audio) {
            immersiveCurrentAudio.pause();
            immersiveCurrentAudio.currentTime = 0;
            chat.querySelectorAll('.msg-play-btn.playing').forEach(function (b) { b.classList.remove('playing'); });
          }
          immersiveCurrentAudio = audio;
          playBtn.classList.add('playing');
          if (audio.readyState < 3) {
            playBtn.disabled = true;
            playBtn.title = '加载中…';
            var onReady = function () {
              playBtn.disabled = false;
              playBtn.title = '播放';
              audio.removeEventListener('canplaythrough', onReady);
              audio.removeEventListener('error', onError);
              audio.play().catch(function () { playBtn.classList.remove('playing'); });
            };
            var onError = function () {
              playBtn.disabled = false;
              playBtn.title = '播放';
              audio.removeEventListener('canplaythrough', onReady);
              audio.removeEventListener('error', onError);
              playBtn.classList.remove('playing');
            };
            audio.addEventListener('canplaythrough', onReady);
            audio.addEventListener('error', onError);
            if (audio.readyState >= 3) onReady();
          } else {
            audio.play().catch(function () { playBtn.classList.remove('playing'); });
          }
        } else {
          audio.pause();
          audio.currentTime = 0;
          playBtn.classList.remove('playing');
          if (immersiveCurrentAudio === audio) immersiveCurrentAudio = null;
        }
      });
      audio.addEventListener('ended', function () {
        playBtn.classList.remove('playing');
        if (immersiveCurrentAudio === audio) immersiveCurrentAudio = null;
      });
      wrap.appendChild(textSpan);
      wrap.appendChild(playBtn);
      div.appendChild(wrap);
    } else {
      div.textContent = text;
    }
    chat.appendChild(div);
    chat.scrollTop = chat.scrollHeight;
  }

  async function sendImmersiveMessage() {
    const input = q('#sceneImmersiveInput');
    const sendBtn = q('#sceneImmersiveSend');
    const text = (input && input.value && input.value.trim()) || '';
    if (!text || !immersiveState.smallSceneId || !immersiveState.npcId) return;
    if (sendBtn) sendBtn.disabled = true;
    input.value = '';
    appendImmersiveMsg('user', text);
    appendImmersiveMsg('assistant', '思考中…');
    const history = immersiveState.history.slice(-20).map(h => ({ role: h.role, content: h.content }));
    const acc = getSceneAccount();
    try {
      const res = await fetch('/api/scene-npc/immersive-chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          small_scene_id: immersiveState.smallSceneId,
          npc_id: immersiveState.npcId,
          message: text,
          history,
          role_swapped: immersiveState.roleSwapped,
          account_name: acc || undefined
        })
      });
      const data = await res.json().catch(() => ({}));
      if (sendBtn) sendBtn.disabled = false;
      removeLastImmersiveMsg('assistant');
      if (!res.ok) {
        appendImmersiveMsg('assistant', 'Error: ' + (data.message || data.error || res.status), null);
        return;
      }
      const reply = (data.reply || '').trim();
      const taskCompleted = data.task_completed === true;
      const audioUrl = data.audio_url || null;
      immersiveState.history.push({ role: 'user', content: text });
      immersiveState.history.push({ role: 'assistant', content: reply });
      appendImmersiveMsg('assistant', reply, audioUrl);
      if (taskCompleted) {
        requestImmersiveReport();
      }
    } catch (e) {
      if (sendBtn) sendBtn.disabled = false;
      removeLastImmersiveMsg('assistant');
      appendImmersiveMsg('assistant', 'Network error: ' + (e.message || '请稍后重试'), null);
    }
  }

  async function sendImmersiveMessageWithText(text, userAudioUrl) {
    if (!text || !text.trim() || !immersiveState.smallSceneId || !immersiveState.npcId) return;
    var sendBtn = q('#sceneImmersiveSend');
    var input = q('#sceneImmersiveInput');
    if (input) input.value = '';
    appendImmersiveMsg('user', text.trim(), userAudioUrl || null);
    appendImmersiveMsg('assistant', '思考中…');
    var history = immersiveState.history.slice(-20).map(function (h) { return { role: h.role, content: h.content }; });
    var acc = getSceneAccount();
    if (sendBtn) sendBtn.disabled = true;
    try {
      var res = await fetch('/api/scene-npc/immersive-chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          small_scene_id: immersiveState.smallSceneId,
          npc_id: immersiveState.npcId,
          message: text.trim(),
          history: history,
          role_swapped: immersiveState.roleSwapped,
          account_name: acc || undefined
        })
      });
      var data = await res.json().catch(function () { return {}; });
      if (sendBtn) sendBtn.disabled = false;
      removeLastImmersiveMsg('assistant');
      if (!res.ok) {
        appendImmersiveMsg('assistant', 'Error: ' + (data.message || data.error || res.status), null);
        return;
      }
      var reply = (data.reply || '').trim();
      var taskCompleted = data.task_completed === true;
      var audioUrl = data.audio_url || null;
      immersiveState.history.push({ role: 'user', content: text.trim() });
      immersiveState.history.push({ role: 'assistant', content: reply });
      appendImmersiveMsg('assistant', reply, audioUrl);
      if (taskCompleted) requestImmersiveReport();
    } catch (e) {
      if (sendBtn) sendBtn.disabled = false;
      removeLastImmersiveMsg('assistant');
      appendImmersiveMsg('assistant', 'Network error: ' + (e.message || '请稍后重试'), null);
    }
  }

  function simpleMarkdownToHtml(text) {
    if (!text || !String(text).trim()) return '';
    var s = String(text)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
    s = s
      .replace(/^纠错与改进\s*$/gm, '## 纠错与改进')
      .replace(/^本场景参考\s*$/gm, '## 本场景参考')
      .replace(/^##\s+(.+)$/gm, '<h2 class="report-heading">$1</h2>')
      .replace(/^###\s+(.+)$/gm, '<h3 class="report-heading">$1</h3>')
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n/g, '<br>');
    return s;
  }

  async function requestImmersiveReport() {
    const reportEl = q('#sceneImmersiveReport');
    const bodyEl = q('#sceneImmersiveReportBody');
    if (!reportEl || !bodyEl) return;
    bodyEl.innerHTML = '<span class="report-loading">正在生成报告…</span>';
    reportEl.style.display = 'block';
    const closeCountdown = typeof window.showCountdownOverlay === 'function'
      ? window.showCountdownOverlay('正在生成复习资料', 10)
      : function noop() {};
    const overlayShownAt = Date.now();
    const MIN_OVERLAY_MS = 2000;
    const transcript = immersiveState.history.filter(h => h.role === 'user').map(h => ({ role: 'user', content: h.content }));
    const acc = getSceneAccount();
    try {
      const res = await fetch('/api/scene-npc/immersive-chat/report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          small_scene_id: immersiveState.smallSceneId,
          npc_id: immersiveState.npcId,
          transcript,
          account_name: acc || undefined
        })
      });
      const data = await res.json().catch(() => ({}));
      var elapsed = Date.now() - overlayShownAt;
      var delayClose = Math.max(0, MIN_OVERLAY_MS - elapsed);
      function closeAndUpdate() {
        closeCountdown();
        if (res.ok && data.report_markdown) {
          bodyEl.innerHTML = simpleMarkdownToHtml(data.report_markdown);
          bodyEl.scrollTop = 0;
          reportEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
        } else {
          bodyEl.textContent = data.message || data.error || '生成报告失败';
        }
      }
      if (delayClose > 0) setTimeout(closeAndUpdate, delayClose);
      else closeAndUpdate();
    } catch (e) {
      closeCountdown();
      bodyEl.textContent = '请求失败：' + (e.message || '');
    }
  }

  function hideImmersiveOverlay() {
    const overlay = q('#scene-immersive-overlay');
    const report = q('#sceneImmersiveReport');
    const chat = q('#sceneImmersiveChat');
    const input = q('#sceneImmersiveInput');
    if (overlay) overlay.style.display = 'none';
    if (report) report.style.display = 'none';
    if (chat) chat.innerHTML = '';
    if (input) input.value = '';
    immersiveState = { smallSceneId: '', npcId: '', label: '', npcName: '', sceneName: '', history: [], roleSwapped: false, userGoal: '', userGoalA: '', bLines: [], aLines: [] };
  }

  async function openImmersiveChat(label, smallSceneId, npcId) {
    const sceneChatModal = q('#sceneChatModal');
    if (sceneChatModal) sceneChatModal.style.display = 'none';
    const overlay = q('#scene-immersive-overlay');
    if (!overlay) return;
    const closeCountdown = typeof window.showCountdownOverlay === 'function'
      ? window.showCountdownOverlay('正在准备自由对话', 10)
      : function noop() {};
    const acc = getSceneAccount();
    const url = urlWithAccount(
      '/api/scene-npc/dialogue/immersive?small_scene_id=' + encodeURIComponent(smallSceneId) + '&npc_id=' + encodeURIComponent(npcId),
      acc
    );
    try {
      const data = await fetchJSON(url);
      closeCountdown();
      if (!data.dialogue) {
        showSceneToast(data.message || data.error || '未找到该场景对话');
        return;
      }
      const d = data.dialogue;
      const content = d.content || [];
      const bLines = content.filter(function (item) { return item.role === 'B'; }).map(function (item) { return (item.content || item.hint || '').trim(); }).filter(Boolean);
      const aLines = content.filter(function (item) { return item.role === 'A'; }).map(function (item) { return (item.content || item.hint || '').trim(); }).filter(Boolean);
      var userGoal = (d.user_goal != null && d.user_goal !== '') ? String(d.user_goal) : (d.userGoal != null && d.userGoal !== '') ? String(d.userGoal) : '';
      var userGoalA = (d.user_goal_a != null && d.user_goal_a !== '') ? String(d.user_goal_a) : (d.userGoalA != null && d.userGoalA !== '') ? String(d.userGoalA) : '';
      immersiveState = {
        smallSceneId,
        npcId,
        label: label || d.npc_name || npcId,
        npcName: d.npc_name || label || npcId,
        sceneName: d.small_scene_name || smallSceneId,
        history: [],
        roleSwapped: false,
        userGoal: userGoal,
        userGoalA: userGoalA,
        bLines: bLines,
        aLines: aLines
      };
      console.log('[自由对话] 加载完成 d.user_goal_a=', d.user_goal_a, 'state.userGoalA=', immersiveState.userGoalA);
      q('#sceneImmersiveTitle').textContent = '自由对话 · ' + (immersiveState.npcName || immersiveState.label);
      updateImmersiveTaskText();
      q('#sceneImmersiveChat').innerHTML = '';
      q('#sceneImmersiveInput').value = '';
      q('#sceneImmersiveReport').style.display = 'none';
      q('#sceneImmersiveReportBody').textContent = '';
      overlay.style.display = 'flex';
      q('#sceneImmersiveInput').focus();
    } catch (e) {
      closeCountdown();
      console.error('打开沉浸式对话失败:', e);
      if (e.message && e.message.indexOf('403') >= 0) {
        showSceneToast('该角色未解锁，请先完成学习');
      } else {
        showSceneToast('加载失败，请稍后重试');
      }
    }
  }

  var immersiveRecorder = { stream: null, recorder: null, chunks: [] };

  function removeLastImmersiveMsg(role) {
    var chat = q('#sceneImmersiveChat');
    if (!chat || !chat.lastElementChild) return;
    var last = chat.lastElementChild;
    if (role && !last.classList.contains(role)) return;
    last.remove();
  }

  function stopImmersiveRecordAndSend() {
    if (!immersiveRecorder.recorder || immersiveRecorder.recorder.state === 'inactive') return;
    immersiveRecorder.recorder.stop();
    immersiveRecorder.recorder.onstop = function () {
      var blob = new Blob(immersiveRecorder.chunks, { type: 'audio/webm' });
      immersiveRecorder.chunks = [];
          if (immersiveRecorder.stream) {
            immersiveRecorder.stream.getTracks().forEach(function (t) { t.stop(); });
            immersiveRecorder.stream = null;
          }
          var btn = q('#sceneImmersiveRecord');
          if (btn) { btn.classList.remove('recording'); btn.textContent = '🎤'; }
          appendImmersiveMsg('user', '转写中…');
          var formData = new FormData();
          formData.append('audio', blob, 'recording.webm');
          fetch('/api/practice/transcribe', { method: 'POST', body: formData })
            .then(function (r) { return r.json(); })
            .then(function (result) {
              if (result.status === 'success' && result.transcription && result.transcription.trim()) {
                removeLastImmersiveMsg('user');
                sendImmersiveMessageWithText(result.transcription.trim(), result.audio_url || null);
              } else {
                removeLastImmersiveMsg('user');
                showSceneToast(result.message || '未识别到语音，请重试');
              }
            })
            .catch(function (e) {
              removeLastImmersiveMsg('user');
              showSceneToast('录音上传失败：' + (e.message || ''));
            });
        };
  }

  function bindImmersiveOverlay() {
    const closeBtn = q('#sceneImmersiveClose');
    const sendBtn = q('#sceneImmersiveSend');
    const input = q('#sceneImmersiveInput');
    const recordBtn = q('#sceneImmersiveRecord');
    const roleSwapBtn = q('#sceneImmersiveRoleSwap');
    const endBtn = q('#sceneImmersiveEnd');
    const reportCloseBtn = q('#sceneImmersiveReportClose');
    if (closeBtn) closeBtn.addEventListener('click', hideImmersiveOverlay);
    if (sendBtn) sendBtn.addEventListener('click', sendImmersiveMessage);
    if (input) input.addEventListener('keydown', (e) => { if (e.key === 'Enter') sendImmersiveMessage(); });
    if (recordBtn) {
      recordBtn.addEventListener('pointerdown', function (e) {
        e.preventDefault();
        if (immersiveRecorder.recorder && immersiveRecorder.recorder.state === 'recording') return;
        navigator.mediaDevices.getUserMedia({ audio: true }).then(function (stream) {
          immersiveRecorder.stream = stream;
          immersiveRecorder.chunks = [];
          var recorder = new MediaRecorder(stream);
          immersiveRecorder.recorder = recorder;
          recorder.ondataavailable = function (ev) { if (ev.data.size) immersiveRecorder.chunks.push(ev.data); };
          recorder.start();
          recordBtn.classList.add('recording');
          recordBtn.textContent = '录音中';
        }).catch(function () { showSceneToast('无法使用麦克风'); });
      });
      recordBtn.addEventListener('pointerup', stopImmersiveRecordAndSend);
      recordBtn.addEventListener('pointerleave', stopImmersiveRecordAndSend);
    }
    if (roleSwapBtn) roleSwapBtn.addEventListener('click', function () {
      immersiveState.roleSwapped = !immersiveState.roleSwapped;
      immersiveState.history = [];
      var chatEl = q('#sceneImmersiveChat');
      if (chatEl) chatEl.innerHTML = '';
      var reportEl = q('#sceneImmersiveReport');
      var reportBody = q('#sceneImmersiveReportBody');
      if (reportEl) reportEl.style.display = 'none';
      if (reportBody) reportBody.textContent = '';
      var s = immersiveState;
      var taskEl = document.getElementById('sceneImmersiveTask');
      var hintEl = document.getElementById('sceneImmersiveHint');
      console.log('[角色互换] taskEl=', taskEl, 'roleSwapped=', s.roleSwapped, 'userGoalA=', s.userGoalA);
      if (!taskEl) console.warn('[角色互换] sceneImmersiveTask 未找到');
      if (taskEl) {
        var prefix = '你的任务：';
        if (s.roleSwapped) {
          taskEl.textContent = s.userGoalA ? (prefix + s.userGoalA) : (prefix + '你扮演 ' + (s.npcName || s.label) + '，AI 扮演学习者。请按剧本流程完成对话。');
        } else {
          taskEl.textContent = s.userGoal ? (prefix + s.userGoal) : (prefix + '扮演 ' + (s.npcName || s.label) + '，在「' + (s.sceneName || s.smallSceneId) + '」中完成剧本中的对话流程。');
        }
        console.log('[角色互换] 已设置 textContent=', taskEl.textContent);
      }
      if (hintEl) {
        var refLines = s.roleSwapped ? (s.aLines || []) : (s.bLines || []);
        if (refLines.length) {
          hintEl.textContent = '参考（你可以这样说）：' + refLines.join(' → ');
          hintEl.style.display = '';
        } else {
          hintEl.textContent = '';
          hintEl.style.display = 'none';
        }
      }
      showSceneToast(s.roleSwapped ? '已切换：你演 NPC，AI 演学习者；对话已清空' : '已切换：你演学习者，AI 演 NPC；对话已清空');
    });
    if (endBtn) endBtn.addEventListener('click', requestImmersiveReport);
    if (reportCloseBtn) reportCloseBtn.addEventListener('click', () => {
      const report = q('#sceneImmersiveReport');
      if (report) report.style.display = 'none';
    });
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

  // Init handlers（若 DOM 已就绪则立即执行，避免 DOMContentLoaded 已触发导致未绑定）
  function runSceneModalInit() {
    console.log('[scene_modal] runSceneModalInit 执行');
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
      if (typeof hideImmersiveOverlay === 'function') hideImmersiveOverlay();
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
    console.log('[scene_modal] 即将 bindImmersiveOverlay, roleSwapBtn=', q('#sceneImmersiveRoleSwap'));
    bindImmersiveOverlay();
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', runSceneModalInit);
  } else {
    runSceneModalInit();
  }
})();

