// Instagram风格的语音消息界面JavaScript

document.addEventListener("DOMContentLoaded", function() {
    // 元素引用
    const messagesList = document.getElementById('messages-list');
    const recordBtn = document.getElementById('record-btn');
    const recordingIndicator = document.getElementById('recording-indicator');
    const characterName = document.getElementById('character-name');
    const settingsBtn = document.getElementById('settings-btn');
    const settingsPanel = document.getElementById('settings-panel');
    const closeSettings = document.getElementById('close-settings');
    const characterSelect = document.getElementById('character-select');
    const providerSelect = document.getElementById('provider-select');
    const textInput = document.getElementById('text-input');
    const sendBtn = document.getElementById('send-btn');
    
    // 检查元素是否存在
    if (!textInput || !sendBtn) {
        console.error('Text input or send button not found');
    }
    
    // 状态管理
    let isRecording = false;
    let mediaRecorder = null;
    let audioChunks = [];
    let websocket = null;
    let currentCharacter = 'wizard';
    let audioContext = null;
    let analyser = null;
    let dataArray = null;
    let lastUserMessage = ''; // 用于防止重复显示
    let isProcessingAudio = false; // 标记是否正在处理音频
    let isProcessing = false; // 标记系统是否正在处理消息（包括生成回复和播放语音）

    // 初始化WebSocket连接
    function initWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        websocket = new WebSocket(`${protocol}//${window.location.hostname}:8000/ws`);
        
        websocket.onopen = () => {
            console.log('WebSocket connected');
        };
        
        websocket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                handleWebSocketMessage(data);
            } catch (e) {
                // 处理文本消息
                if (event.data.startsWith('You:') || event.data.includes(':')) {
                    handleTextMessage(event.data);
                }
            }
        };
        
               websocket.onerror = (error) => {
                   console.error('WebSocket error:', error);
                   showError('连接错误，请刷新页面');
               };
        
               websocket.onclose = () => {
                   console.log('WebSocket closed');
                   setTimeout(initWebSocket, 3000);
               };
    }

    // 处理WebSocket消息
    function handleWebSocketMessage(data) {
        if (data.action === 'recording_started') {
            showRecordingIndicator();
        } else if (data.action === 'recording_stopped') {
            hideRecordingIndicator();
        } else if (data.action === 'ai_start_speaking') {
            // AI开始说话，保持禁用状态
            isProcessing = true;
            setInputEnabled(false);
            console.log('AI started speaking, input disabled');
        } else if (data.action === 'ai_stop_speaking') {
            // AI停止说话，重新启用输入
            isProcessing = false;
            setInputEnabled(true);
            console.log('AI stopped speaking, input enabled');
        } else if (data.action === 'ai_message') {
            addAIMessage(data.text);
        } else if (data.action === 'user_message') {
            addUserMessage(data.text);
        } else if (data.message) {
            addAIMessage(data.message);
        } else if (data.action === 'error') {
            showError(data.message || '发生错误');
            // 发生错误时也重新启用输入
            isProcessing = false;
            setInputEnabled(true);
        }
    }

    // 处理文本消息
    function handleTextMessage(text) {
        if (text.startsWith('You:')) {
            const userMessage = text.replace('You:', '').trim();
            addUserMessage(userMessage);
        } else {
            addAIMessage(text);
        }
    }

    // 启用/禁用输入功能
    function setInputEnabled(enabled) {
        if (textInput) {
            textInput.disabled = !enabled;
        }
        if (sendBtn) {
            sendBtn.disabled = !enabled;
        }
        if (recordBtn) {
            recordBtn.disabled = !enabled;
            if (!enabled) {
                recordBtn.style.opacity = '0.5';
                recordBtn.style.cursor = 'not-allowed';
            } else {
                recordBtn.style.opacity = '1';
                recordBtn.style.cursor = 'pointer';
            }
        }
    }

    // 文字输入功能
    async function sendTextMessage() {
        console.log('sendTextMessage called');
        
        if (!textInput || !sendBtn) {
            console.error('Text input or send button not found', { textInput, sendBtn });
            showError('界面元素未找到，请刷新页面');
            return;
        }
        
        // 检查是否正在处理
        if (isProcessing) {
            console.log('System is processing, please wait...');
            showError('系统正在处理中，请等待回复完成后再发送');
            return;
        }
        
        const text = textInput.value.trim();
        console.log('Text to send:', text);
        
        if (!text) {
            console.log('Text is empty, returning');
            return;
        }
        
        // 设置处理状态并禁用输入
        isProcessing = true;
        setInputEnabled(false);
        
        try {
            console.log('Sending request to /api/text/send', { text, character: currentCharacter });
            
            const response = await fetch('/api/text/send', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    text: text,
                    character: currentCharacter
                })
            });
            
            console.log('Response status:', response.status);
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ message: '未知错误' }));
                console.error('Error response:', errorData);
                throw new Error(errorData.message || '发送失败');
            }
            
            const result = await response.json();
            console.log('Success response:', result);
            
            // 清空输入框
            textInput.value = '';
            
            // 注意：不在这里重新启用输入，等待 ai_stop_speaking 事件
            
        } catch (error) {
            console.error('Error sending text message:', error);
            showError('发送消息失败：' + error.message);
            // 发生错误时重新启用输入
            isProcessing = false;
            setInputEnabled(true);
        }
        // 注意：正常情况下不在这里重新启用输入，等待 ai_stop_speaking 事件
    }
    
    // 发送按钮点击事件
    if (sendBtn) {
        sendBtn.addEventListener('click', sendTextMessage);
    }
    
    // Enter键发送消息
    if (textInput) {
        textInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendTextMessage();
            }
        });
    }
    
    // 录音功能
    recordBtn.addEventListener('click', async () => {
        // 检查是否正在处理（但允许停止正在进行的录音）
        if (isProcessing && !isRecording) {
            console.log('System is processing, cannot start recording...');
            showError('系统正在处理中，请等待回复完成后再录音');
            return;
        }
        
        if (!isRecording) {
            await startRecording();
        } else {
            stopRecording();
        }
    });


    // 开始录音
    async function startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                } 
            });
            
            // 创建音频上下文用于波形分析
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
            analyser = audioContext.createAnalyser();
            const source = audioContext.createMediaStreamSource(stream);
            source.connect(analyser);
            analyser.fftSize = 256;
            dataArray = new Uint8Array(analyser.frequencyBinCount);
            
            // 创建MediaRecorder
            mediaRecorder = new MediaRecorder(stream, {
                mimeType: 'audio/webm;codecs=opus'
            });
            
            audioChunks = [];
            
            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    audioChunks.push(event.data);
                }
            };
            
            mediaRecorder.onstop = () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                sendAudioToServer(audioBlob);
                
                // 停止音频流
                stream.getTracks().forEach(track => track.stop());
                if (audioContext) {
                    audioContext.close();
                    audioContext = null;
                }
            };
            
                   mediaRecorder.start();
                   isRecording = true;
                   recordBtn.classList.add('recording');
                   showRecordingIndicator();
            
            // 开始波形动画
            animateWaveform();
            
            // 通知服务器开始录音
            if (websocket && websocket.readyState === WebSocket.OPEN) {
                websocket.send(JSON.stringify({ action: 'start_recording' }));
            }
            
        } catch (error) {
            console.error('Error starting recording:', error);
            showError('无法访问麦克风，请检查权限设置');
        }
    }

    // 停止录音
    function stopRecording() {
        if (mediaRecorder && mediaRecorder.state !== 'inactive') {
            mediaRecorder.stop();
                   isRecording = false;
                   recordBtn.classList.remove('recording');
                   hideRecordingIndicator();
            
            // 通知服务器停止录音
            if (websocket && websocket.readyState === WebSocket.OPEN) {
                websocket.send(JSON.stringify({ action: 'stop_recording' }));
            }
        }
    }

    // 波形动画
    function animateWaveform() {
        if (!isRecording || !analyser) return;
        
        analyser.getByteFrequencyData(dataArray);
        
        // 更新录音指示器的波形
        const waveBars = recordingIndicator.querySelectorAll('.wave-bar');
        if (waveBars.length > 0) {
            const step = Math.floor(dataArray.length / waveBars.length);
            waveBars.forEach((bar, index) => {
                const value = dataArray[index * step] || 0;
                const height = Math.max(8, (value / 255) * 24);
                bar.style.height = `${height}px`;
            });
        }
        
        requestAnimationFrame(animateWaveform);
    }

    // 发送音频到服务器
    async function sendAudioToServer(audioBlob) {
        // 检查是否正在处理
        if (isProcessing) {
            console.log('System is processing, please wait...');
            showError('系统正在处理中，请等待回复完成后再发送');
            return;
        }
        
        if (isProcessingAudio) {
            console.log('Already processing audio, skipping...');
            return;
        }
        
        isProcessingAudio = true;
        // 设置处理状态并禁用输入
        isProcessing = true;
        setInputEnabled(false);
        try {
            const formData = new FormData();
            formData.append('audio', audioBlob, 'recording.webm');
            formData.append('character', currentCharacter);
            
            const response = await fetch('/api/voice/upload', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error('上传失败');
            }
            
            const result = await response.json();
            // 不在这里显示消息，等待WebSocket消息来显示
            // 这样可以避免重复显示
            if (result.transcription) {
                // 记录转录结果，用于去重
                lastUserMessage = result.transcription;
                // 消息会通过WebSocket从服务器接收并显示
                console.log('Audio uploaded, transcription:', result.transcription);
            }
            
        } catch (error) {
            console.error('Error sending audio:', error);
            showError('发送音频失败');
            isProcessingAudio = false;
            // 发生错误时重新启用输入
            isProcessing = false;
            setInputEnabled(true);
        }
        // 注意：正常情况下不在这里重新启用输入，等待 ai_stop_speaking 事件
    }

    // 添加用户消息
    function addUserMessage(text) {
        // 防止重复显示相同的消息
        if (text === lastUserMessage && messagesList.lastElementChild) {
            const lastMsg = messagesList.lastElementChild;
            const lastMsgText = lastMsg.querySelector('.text-message')?.textContent;
            if (lastMsgText === text && lastMsg.classList.contains('user')) {
                console.log('Duplicate message detected, skipping:', text);
                isProcessingAudio = false;
                return;
            }
        }
        
        lastUserMessage = text;
        isProcessingAudio = false;
        const message = createMessageElement('user', text, 'text');
        messagesList.appendChild(message);
        scrollToBottom();
    }

    // 添加AI消息
    function addAIMessage(text) {
        const message = createMessageElement('ai', text, 'text');
        messagesList.appendChild(message);
        scrollToBottom();
        
        // 自动播放AI语音（如果需要）
        // playAIVoice(text);
    }

    // 创建消息元素
    function createMessageElement(sender, content, type = 'text') {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        
        // 头像
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = sender === 'user' ? '我' : 'AI';
        messageDiv.appendChild(avatar);
        
        // 消息内容包装器
        const contentWrapper = document.createElement('div');
        contentWrapper.className = 'message-content-wrapper';
        
        // 消息内容
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        if (type === 'voice') {
            // 语音消息
            const voiceMessage = document.createElement('div');
            voiceMessage.className = 'voice-message';
            
            const playBtn = document.createElement('button');
            playBtn.className = 'play-button';
            playBtn.innerHTML = `
                <svg class="play-icon" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M8 5v14l11-7z"/>
                </svg>
            `;
            
            const waveform = document.createElement('div');
            waveform.className = 'voice-waveform';
            for (let i = 0; i < 5; i++) {
                const bar = document.createElement('div');
                bar.className = 'wave-bar';
                waveform.appendChild(bar);
            }
            
            voiceMessage.appendChild(playBtn);
            voiceMessage.appendChild(waveform);
            messageContent.appendChild(voiceMessage);
        } else {
            // 文本消息
            const textDiv = document.createElement('div');
            textDiv.className = 'text-message';
            textDiv.textContent = content;
            messageContent.appendChild(textDiv);
        }
        
        contentWrapper.appendChild(messageContent);
        
        // 时间戳
        const timestamp = document.createElement('div');
        timestamp.className = 'message-timestamp';
        timestamp.textContent = getCurrentTime();
        contentWrapper.appendChild(timestamp);
        
        messageDiv.appendChild(contentWrapper);
        
        return messageDiv;
    }

    // 获取当前时间
    function getCurrentTime() {
        const now = new Date();
        const hours = now.getHours().toString().padStart(2, '0');
        const minutes = now.getMinutes().toString().padStart(2, '0');
        return `${hours}:${minutes}`;
    }

    // 显示录音指示器
    function showRecordingIndicator() {
        recordingIndicator.classList.add('active');
    }

    // 隐藏录音指示器
    function hideRecordingIndicator() {
        recordingIndicator.classList.remove('active');
    }

    // 滚动到底部
    function scrollToBottom() {
        const container = document.querySelector('.messages-container');
        container.scrollTop = container.scrollHeight;
    }

    // 显示错误
    function showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = message;
        errorDiv.style.cssText = `
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: #ff4444;
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            z-index: 10000;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        `;
        document.body.appendChild(errorDiv);
        
        setTimeout(() => {
            errorDiv.remove();
        }, 3000);
    }

    // 设置面板
    settingsBtn.addEventListener('click', () => {
        settingsPanel.classList.add('active');
    });

    closeSettings.addEventListener('click', () => {
        settingsPanel.classList.remove('active');
    });

    // 加载角色列表
    async function loadCharacters() {
        try {
            const response = await fetch('/characters');
            const data = await response.json();
            
            characterSelect.innerHTML = '';
            data.characters.forEach(char => {
                const option = document.createElement('option');
                option.value = char;
                option.textContent = char.charAt(0).toUpperCase() + char.slice(1);
                characterSelect.appendChild(option);
            });
            
            characterSelect.value = currentCharacter;
        } catch (error) {
            console.error('Error loading characters:', error);
        }
    }

    // 角色选择变化
    characterSelect.addEventListener('change', (e) => {
        currentCharacter = e.target.value;
        characterName.textContent = currentCharacter.charAt(0).toUpperCase() + currentCharacter.slice(1);
        
        if (websocket && websocket.readyState === WebSocket.OPEN) {
            websocket.send(JSON.stringify({
                action: 'set_character',
                character: currentCharacter
            }));
        }
    });

    // 提供商选择变化
    providerSelect.addEventListener('change', (e) => {
        if (websocket && websocket.readyState === WebSocket.OPEN) {
            websocket.send(JSON.stringify({
                action: 'set_provider',
                provider: e.target.value
            }));
        }
    });

    // 初始化检查
    console.log('Initializing voice chat interface...');
    console.log('Elements check:', {
        textInput: !!textInput,
        sendBtn: !!sendBtn,
        recordBtn: !!recordBtn,
        messagesList: !!messagesList
    });
    
    // 初始化
    initWebSocket();
    loadCharacters();
    
    // 添加欢迎消息
    setTimeout(() => {
        addAIMessage('你好！我是你的AI助手，可以输入文字或点击麦克风开始对话！');
    }, 1000);
});

