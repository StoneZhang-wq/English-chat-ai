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
    const startEnglishBtn = document.getElementById('start-english-btn');
    
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
            // 在练习模式下，不显示AI的正常回复（因为AI应该按卡片内容回复）
            if (!practiceState || !practiceState.isActive) {
                addAIMessage(data.text);
            } else {
                console.log('Practice mode: ignoring AI message from normal flow');
            }
        } else if (data.action === 'user_message') {
            // 在练习模式下，用户消息已经在handlePracticeInput中显示
            if (!practiceState || !practiceState.isActive) {
                addUserMessage(data.text);
            } else {
                console.log('Practice mode: ignoring user message from normal flow');
            }
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
        
        // 检查是否在练习模式
        if (typeof handlePracticeInput === 'function' && practiceState && practiceState.isActive) {
            console.log('Practice mode active, intercepting input');
            const handled = await handlePracticeInput(text);
            if (handled) {
                textInput.value = '';
                return; // 已在练习模式中处理，不继续正常流程
            }
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
        // 检查是否在练习模式
        if (practiceState && practiceState.isActive) {
            console.log('Practice mode active: using practice transcribe API');
            // 在练习模式下，只转录音频，不生成AI回复
            try {
                isProcessingAudio = true;
                setInputEnabled(false);
                
                const formData = new FormData();
                formData.append('audio', audioBlob, 'recording.webm');
                
                const response = await fetch('/api/practice/transcribe', {
                    method: 'POST',
                    body: formData
                });
                
                if (!response.ok) {
                    throw new Error('转录失败');
                }
                
                const result = await response.json();
                console.log('Practice transcribe result:', result);
                
                if (result.status === 'success' && result.transcription) {
                    console.log('Practice mode: transcription received, handling input');
                    
                    // 如果返回了音频URL，显示为音频气泡
                    if (result.audio_url) {
                        createAudioBubble(result.transcription, result.audio_url, 'user');
                    }
                    
                    // 使用练习API处理转录结果
                    await handlePracticeInput(result.transcription);
                } else {
                    const errorMsg = result.message || '转录失败：未知错误';
                    console.error('Transcription failed:', result);
                    showError(errorMsg);
                }
                
                isProcessingAudio = false;
                setInputEnabled(true);
                return; // 已处理，不继续正常流程
            } catch (error) {
                console.error('Error in practice mode transcription:', error);
                showError('转录音频失败：' + error.message);
                isProcessingAudio = false;
                setInputEnabled(true);
                return;
            }
        }
        
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

    // 显示成功消息
    function showSuccess(message) {
        const successDiv = document.createElement('div');
        successDiv.className = 'success-message';
        successDiv.textContent = message;
        successDiv.style.cssText = `
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: #4caf50;
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            z-index: 10000;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        `;
        document.body.appendChild(successDiv);
        
        setTimeout(() => {
            successDiv.remove();
        }, 3000);
    }

    // 设置面板
    settingsBtn.addEventListener('click', () => {
        settingsPanel.classList.add('active');
    });

    closeSettings.addEventListener('click', () => {
        settingsPanel.classList.remove('active');
    });
    
    // 显示对话选项选择对话框（长度和难度）
    function showDialogueOptionsDialog() {
        return new Promise((resolve) => {
            const dialog = document.createElement('div');
            dialog.className = 'dialogue-options-dialog';
            dialog.style.cssText = `
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: white;
                padding: 24px;
                border-radius: 12px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.15);
                z-index: 10000;
                min-width: 500px;
                max-width: 90%;
                max-height: 90vh;
                overflow-y: auto;
            `;
            
            dialog.innerHTML = `
                <h3 style="margin: 0 0 20px 0; font-size: 18px; color: #333;">选择对话选项</h3>
                <div style="margin-bottom: 24px;">
                    <label style="display: block; margin-bottom: 10px; font-weight: 600; color: #333;">对话长度：</label>
                    <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                        <button class="option-btn" data-type="length" data-value="short" style="padding: 10px 16px; border: 2px solid #e0e0e0; border-radius: 8px; background: white; cursor: pointer; font-size: 14px;">短（8-12句）</button>
                        <button class="option-btn" data-type="length" data-value="medium" style="padding: 10px 16px; border: 2px solid #e0e0e0; border-radius: 8px; background: white; cursor: pointer; font-size: 14px;">中（12-18句）</button>
                        <button class="option-btn" data-type="length" data-value="long" style="padding: 10px 16px; border: 2px solid #e0e0e0; border-radius: 8px; background: white; cursor: pointer; font-size: 14px;">长（18-25句）</button>
                        <button class="option-btn" data-type="length" data-value="auto" style="padding: 10px 16px; border: 2px solid #e0e0e0; border-radius: 8px; background: white; cursor: pointer; font-size: 14px;">自动</button>
                    </div>
                </div>
                <div style="margin-bottom: 24px;">
                    <label style="display: block; margin-bottom: 10px; font-weight: 600; color: #333;">难度水平：</label>
                    <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                        <button class="option-btn" data-type="difficulty" data-value="beginner" style="padding: 10px 16px; border: 2px solid #e0e0e0; border-radius: 8px; background: white; cursor: pointer; font-size: 14px;">初级（A1）</button>
                        <button class="option-btn" data-type="difficulty" data-value="elementary" style="padding: 10px 16px; border: 2px solid #e0e0e0; border-radius: 8px; background: white; cursor: pointer; font-size: 14px;">基础（A2）</button>
                        <button class="option-btn" data-type="difficulty" data-value="pre_intermediate" style="padding: 10px 16px; border: 2px solid #e0e0e0; border-radius: 8px; background: white; cursor: pointer; font-size: 14px;">准中级（A2-B1）</button>
                        <button class="option-btn" data-type="difficulty" data-value="intermediate" style="padding: 10px 16px; border: 2px solid #e0e0e0; border-radius: 8px; background: white; cursor: pointer; font-size: 14px;">中级（B1-B2）</button>
                        <button class="option-btn" data-type="difficulty" data-value="upper_intermediate" style="padding: 10px 16px; border: 2px solid #e0e0e0; border-radius: 8px; background: white; cursor: pointer; font-size: 14px;">中高级（B2）</button>
                        <button class="option-btn" data-type="difficulty" data-value="advanced" style="padding: 10px 16px; border: 2px solid #e0e0e0; border-radius: 8px; background: white; cursor: pointer; font-size: 14px;">高级（B2-C1）</button>
                        <button class="option-btn" data-type="difficulty" data-value="auto" style="padding: 10px 16px; border: 2px solid #e0e0e0; border-radius: 8px; background: white; cursor: pointer; font-size: 14px;">使用我的水平</button>
                    </div>
                </div>
                <div style="display: flex; gap: 10px; justify-content: flex-end; margin-top: 20px;">
                    <button id="confirm-dialog" style="padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px;">确认</button>
                    <button id="cancel-dialog" style="padding: 10px 20px; background: #f0f0f0; border: none; border-radius: 6px; cursor: pointer; font-size: 14px;">取消</button>
                </div>
            `;
            
            let selectedLength = "auto";
            let selectedDifficulty = "auto";
            
            // 选项按钮点击事件
            dialog.querySelectorAll('.option-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    const type = btn.dataset.type;
                    const value = btn.dataset.value;
                    
                    // 移除同类型其他按钮的选中状态
                    dialog.querySelectorAll(`.option-btn[data-type="${type}"]`).forEach(b => {
                        b.style.background = 'white';
                        b.style.borderColor = '#e0e0e0';
                        b.style.color = '#333';
                    });
                    
                    // 设置当前按钮为选中状态
                    btn.style.background = '#007bff';
                    btn.style.color = 'white';
                    btn.style.borderColor = '#007bff';
                    
                    if (type === 'length') {
                        selectedLength = value;
                    } else if (type === 'difficulty') {
                        selectedDifficulty = value;
                    }
                });
                
                // 鼠标悬停效果
                btn.addEventListener('mouseenter', () => {
                    if (btn.style.background !== 'rgb(0, 123, 255)') {
                        btn.style.borderColor = '#007bff';
                        btn.style.background = '#f0f7ff';
                    }
                });
                
                btn.addEventListener('mouseleave', () => {
                    if (btn.style.background !== 'rgb(0, 123, 255)') {
                        btn.style.borderColor = '#e0e0e0';
                        btn.style.background = 'white';
                    }
                });
            });
            
            // 确认按钮
            dialog.querySelector('#confirm-dialog').addEventListener('click', () => {
                document.body.removeChild(dialog);
                resolve({
                    length: selectedLength,
                    difficulty: selectedDifficulty === "auto" ? null : selectedDifficulty
                });
            });
            
            // 取消按钮
            dialog.querySelector('#cancel-dialog').addEventListener('click', () => {
                document.body.removeChild(dialog);
                resolve(null);
            });
            
            document.body.appendChild(dialog);
        });
    }
    
    // 开始英语学习（保存记忆并切换到英文学习阶段）
    if (startEnglishBtn) {
        startEnglishBtn.addEventListener('click', async () => {
            if (isProcessing) {
                showError('系统正在处理中，请等待完成后再切换');
                return;
            }
            
            if (!confirm('确定要开始英语学习吗？\n\n注意：当前对话的记忆将被保存，然后切换到英文学习模式。')) {
                return;
            }
            
            let originalHTML = null;
            try {
                startEnglishBtn.disabled = true;
                originalHTML = startEnglishBtn.innerHTML;
                startEnglishBtn.innerHTML = '<span style="font-size: 12px;">保存中...</span>';
                
                // 第一步：保存当前对话记忆
                const response = await fetch('/api/conversation/end', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                
                const result = await response.json();
                
                if (result.status === 'success') {
                    // 显示记忆保存成功
                    if (result.summary) {
                        addAIMessage(`记忆已保存。\n\n摘要：${result.summary}`);
                    } else {
                        addAIMessage('记忆已保存');
                    }
                    
                    // 总是显示对话选项选择对话框（即使没有今天的摘要，也可以基于历史记忆生成）
                    const options = await showDialogueOptionsDialog();
                    if (options) {
                        // 生成英文对话
                        try {
                            addAIMessage('正在生成英文学习对话...');
                            
                            const englishResponse = await fetch('/api/english/generate', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json'
                                },
                                body: JSON.stringify({ 
                                    dialogue_length: options.length,
                                    difficulty_level: options.difficulty
                                })
                            });
                            
                            const englishResult = await englishResponse.json();
                            
                            if (englishResult.status === 'success' && englishResult.dialogue) {
                                // 使用卡片式展示英文对话
                                displayEnglishDialogue(
                                    englishResult.dialogue, 
                                    englishResult.dialogue_lines || [],
                                    englishResult.dialogue_id || ''
                                );
                                addAIMessage('已切换到英文学习模式！现在我会用英文和你交流。');
                                showSuccess('英文对话已生成，已切换到英文学习模式！');
                            } else {
                                // 即使生成失败，也切换到英文学习阶段
                                await switchToEnglishLearning();
                                showError(englishResult.message || '生成英文对话失败，但已切换到英文学习模式');
                            }
                        } catch (error) {
                            console.error('Error generating english dialogue:', error);
                            // 即使生成失败，也切换到英文学习阶段
                            await switchToEnglishLearning();
                            showError('生成英文对话失败，但已切换到英文学习模式：' + error.message);
                        }
                    } else {
                        // 用户取消了长度选择，但还是要切换到英文学习阶段
                        await switchToEnglishLearning();
                    }
                } else {
                    showError(result.message || '保存记忆失败');
                }
            } catch (error) {
                console.error('Error starting english learning:', error);
                showError('开始英语学习失败：' + error.message);
            } finally {
                if (startEnglishBtn) {
                    startEnglishBtn.disabled = false;
                    // 恢复按钮内容
                    const defaultHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12h18M3 6h18M3 18h18"></path><path d="M12 3v18"></path></svg><span style="margin-left: 4px; font-size: 12px;">EN</span>';
                    startEnglishBtn.innerHTML = defaultHTML;
                }
            }
        });
    }
    
    // 切换到英文学习阶段的辅助函数
    async function switchToEnglishLearning() {
        try {
            const response = await fetch('/api/learning/start_english', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const result = await response.json();
            
            if (result.status === 'success') {
                addAIMessage('已切换到英文学习模式！现在我会用英文和你交流。');
                showSuccess('已切换到英文学习模式');
            } else if (result.status === 'info') {
                // 已经处于英文学习阶段
                showSuccess('已经处于英文学习模式');
            } else {
                showError(result.message || '切换失败');
            }
        } catch (error) {
            console.error('Error switching to english learning:', error);
            showError('切换失败：' + error.message);
        }
    }
    
    // 提取纯对话内容（用于朗读，去掉A:和B:标签）
    function extractDialogueText(dialogue) {
        const lines = dialogue.split('\n').filter(line => line.trim());
        return lines.map(line => {
            const trimmedLine = line.trim();
            if (trimmedLine.startsWith('A:') || trimmedLine.startsWith('B:')) {
                return trimmedLine.replace(/^[AB]:\s*/, '').trim();
            }
            return trimmedLine;
        }).filter(line => line).join('. '); // 用句号连接，更自然
    }
    
    // 格式化对话，标签和内容分开，支持逐句播放
    function formatDialogue(dialogue, dialogueLines = []) {
        const lines = dialogue.split('\n').filter(line => line.trim());
        let lineIndex = 0;
        
        return lines.map((line, idx) => {
            const trimmedLine = line.trim();
            if (trimmedLine.startsWith('A:')) {
                const content = trimmedLine.replace(/^A:\s*/, '').trim();
                // 查找对应的音频URL
                const audioLine = dialogueLines.find(l => l.speaker === 'A' && l.text === content);
                const audioUrl = audioLine ? audioLine.audio_url : null;
                const lineId = `dialogue-line-${idx}`;
                
                return `<div class="dialogue-item speaker-a-item">
                    <div class="speaker-label speaker-a-label">A</div>
                    <div class="dialogue-bubble speaker-a-bubble ${audioUrl ? 'dialogue-line-clickable' : ''}" 
                         data-audio-url="${audioUrl || ''}" 
                         data-line-id="${lineId}"
                         ${audioUrl ? 'style="cursor: pointer;"' : ''}>
                        <div class="bubble-content">${content}</div>
                        ${audioUrl ? '<div class="play-icon" style="display: none;">▶</div>' : ''}
                        <div class="bubble-tail bubble-tail-left"></div>
                    </div>
                </div>`;
            } else if (trimmedLine.startsWith('B:')) {
                const content = trimmedLine.replace(/^B:\s*/, '').trim();
                // 查找对应的音频URL
                const audioLine = dialogueLines.find(l => l.speaker === 'B' && l.text === content);
                const audioUrl = audioLine ? audioLine.audio_url : null;
                const lineId = `dialogue-line-${idx}`;
                
                return `<div class="dialogue-item speaker-b-item">
                    <div class="speaker-label speaker-b-label">B</div>
                    <div class="dialogue-bubble speaker-b-bubble ${audioUrl ? 'dialogue-line-clickable' : ''}" 
                         data-audio-url="${audioUrl || ''}" 
                         data-line-id="${lineId}"
                         ${audioUrl ? 'style="cursor: pointer;"' : ''}>
                        <div class="bubble-content">${content}</div>
                        ${audioUrl ? '<div class="play-icon" style="display: none;">▶</div>' : ''}
                        <div class="bubble-tail bubble-tail-right"></div>
                    </div>
                </div>`;
            } else if (trimmedLine) {
                return `<div class="dialogue-item"><div class="dialogue-bubble neutral-bubble"><div class="bubble-content">${trimmedLine}</div></div></div>`;
            }
            return '';
        }).join('');
    }
    
    // 创建英文学习卡片
    function displayEnglishDialogue(dialogue, dialogueLines = [], dialogueId = '') {
        const card = document.createElement('div');
        card.className = 'english-dialogue-card';
        card.dataset.dialogueId = dialogueId;
        card.dataset.dialogueLines = JSON.stringify(dialogueLines);
        
        let isCollapsed = false;
        let currentPlayingAudio = null;
        let currentPlayingElement = null;
        
        card.innerHTML = `
            <div class="dialogue-header">
                <div class="dialogue-title">
                    <span class="dialogue-icon">📚</span>
                    <h3>英文学习对话</h3>
                </div>
                <button class="collapse-btn" title="展开/折叠">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="6 9 12 15 18 9"></polyline>
                    </svg>
                </button>
            </div>
            <div class="dialogue-content">
                ${formatDialogue(dialogue, dialogueLines)}
            </div>
            <div class="dialogue-actions">
                <button class="action-btn copy-btn" title="复制对话">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                    </svg>
                    <span>复制</span>
                </button>
                <button class="action-btn read-btn" title="朗读对话">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
                        <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path>
                    </svg>
                    <span>朗读</span>
                </button>
                <button class="action-btn practice-btn" title="开始练习" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; font-weight: 600;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polygon points="5 3 19 12 5 21 5 3"></polygon>
                    </svg>
                    <span>开始练习</span>
                </button>
            </div>
        `;
        
        // 展开/折叠功能
        const collapseBtn = card.querySelector('.collapse-btn');
        const content = card.querySelector('.dialogue-content');
        
        collapseBtn.addEventListener('click', () => {
            isCollapsed = !isCollapsed;
            if (isCollapsed) {
                content.style.display = 'none';
                collapseBtn.querySelector('svg').style.transform = 'rotate(-90deg)';
            } else {
                content.style.display = 'block';
                collapseBtn.querySelector('svg').style.transform = 'rotate(0deg)';
            }
        });
        
        // 逐句播放功能
        const clickableBubbles = card.querySelectorAll('.dialogue-line-clickable');
        clickableBubbles.forEach(bubble => {
            const audioUrl = bubble.dataset.audioUrl;
            if (!audioUrl) return;
            
            const playIcon = bubble.querySelector('.play-icon');
            
            // 鼠标悬停显示播放图标
            bubble.addEventListener('mouseenter', () => {
                if (playIcon && currentPlayingElement !== bubble) {
                    playIcon.style.display = 'block';
                }
            });
            
            bubble.addEventListener('mouseleave', () => {
                if (playIcon && currentPlayingElement !== bubble) {
                    playIcon.style.display = 'none';
                }
            });
            
            // 点击播放
            bubble.addEventListener('click', (e) => {
                e.stopPropagation();
                
                // 如果正在播放其他音频，先停止
                if (currentPlayingAudio) {
                    currentPlayingAudio.pause();
                    currentPlayingAudio.currentTime = 0;
                    if (currentPlayingElement) {
                        currentPlayingElement.classList.remove('dialogue-line-playing');
                        const prevIcon = currentPlayingElement.querySelector('.play-icon');
                        if (prevIcon) prevIcon.style.display = 'none';
                    }
                }
                
                // 如果点击的是同一个气泡，停止播放
                if (currentPlayingElement === bubble && currentPlayingAudio) {
                    currentPlayingAudio = null;
                    currentPlayingElement = null;
                    return;
                }
                
                // 播放新音频
                const audio = new Audio(audioUrl);
                currentPlayingAudio = audio;
                currentPlayingElement = bubble;
                
                bubble.classList.add('dialogue-line-playing');
                if (playIcon) {
                    playIcon.textContent = '⏸';
                    playIcon.style.display = 'block';
                }
                
                audio.play().catch(err => {
                    console.error('Error playing audio:', err);
                    showError('播放音频失败');
                    bubble.classList.remove('dialogue-line-playing');
                    if (playIcon) playIcon.style.display = 'none';
                });
                
                audio.onended = () => {
                    bubble.classList.remove('dialogue-line-playing');
                    if (playIcon) {
                        playIcon.textContent = '▶';
                        playIcon.style.display = 'none';
                    }
                    currentPlayingAudio = null;
                    currentPlayingElement = null;
                };
                
                audio.onpause = () => {
                    if (playIcon) playIcon.textContent = '▶';
                };
            });
        });
        
        // 复制功能
        const copyBtn = card.querySelector('.copy-btn');
        copyBtn.addEventListener('click', async () => {
            try {
                await navigator.clipboard.writeText(dialogue);
                copyBtn.innerHTML = `
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="20 6 9 17 4 12"></polyline>
                    </svg>
                    <span>已复制</span>
                `;
                setTimeout(() => {
                    copyBtn.innerHTML = `
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                        </svg>
                        <span>复制</span>
                    `;
                }, 2000);
            } catch (error) {
                console.error('Failed to copy:', error);
                showError('复制失败');
            }
        });
        
        // 朗读功能
        const readBtn = card.querySelector('.read-btn');
        readBtn.addEventListener('click', () => {
            if ('speechSynthesis' in window) {
                // 使用提取的纯内容，不包含A:和B:标签
                const cleanText = extractDialogueText(dialogue);
                const utterance = new SpeechSynthesisUtterance(cleanText);
                utterance.lang = 'en-US';
                utterance.rate = 0.9;
                utterance.pitch = 1;
                
                readBtn.innerHTML = `
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="6" y="4" width="4" height="16" rx="1"></rect>
                        <rect x="14" y="4" width="4" height="16" rx="1"></rect>
                    </svg>
                    <span>朗读中...</span>
                `;
                readBtn.disabled = true;
                
                utterance.onend = () => {
                    readBtn.innerHTML = `
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
                            <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path>
                        </svg>
                        <span>朗读</span>
                    `;
                    readBtn.disabled = false;
                };
                
                speechSynthesis.speak(utterance);
            } else {
                showError('您的浏览器不支持语音朗读功能');
            }
        });
        
        // 开始练习功能
        const practiceBtn = card.querySelector('.practice-btn');
        if (practiceBtn) {
            practiceBtn.addEventListener('click', () => {
                startPracticeMode(dialogue, card);
            });
        }
        
        // 存储对话内容到卡片数据属性
        card.dataset.dialogue = dialogue;
        
        messagesList.appendChild(card);
        scrollToBottom();
    }
    
    // 练习模式状态
    let practiceState = {
        dialogueId: null,
        dialogueLines: [],
        currentTurn: 0,
        isActive: false,
        currentHints: null,
        totalTurns: 0
    };
    
    // 开始练习模式
    async function startPracticeMode(dialogue, cardElement) {
        try {
            console.log('Starting practice mode, dialogue:', dialogue);
            
            // 检查对话内容
            if (!dialogue || !dialogue.trim()) {
                showError('对话内容为空，无法开始练习');
                return;
            }
            
            // 显示加载状态
            const practiceBtn = cardElement.querySelector('.practice-btn');
            const originalHTML = practiceBtn.innerHTML;
            practiceBtn.disabled = true;
            practiceBtn.innerHTML = '<span>准备中...</span>';
            
            // 获取对话行数据（包含音频URL）
            const dialogueLines = JSON.parse(cardElement.dataset.dialogueLines || '[]');
            const dialogueId = cardElement.dataset.dialogueId || '';
            
            // 调用API开始练习
            const response = await fetch('/api/practice/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    dialogue: dialogue,
                    dialogue_lines: dialogueLines,
                    dialogue_id: dialogueId
                })
            });
            
            // 检查响应状态
            if (!response.ok) {
                const errorText = await response.text();
                console.error('API error response:', errorText);
                let errorMessage = `服务器错误 (${response.status})`;
                try {
                    const errorJson = JSON.parse(errorText);
                    errorMessage = errorJson.message || errorMessage;
                } catch (e) {
                    errorMessage = errorText || errorMessage;
                }
                throw new Error(errorMessage);
            }
            
            const result = await response.json();
            console.log('Practice start result:', result);
            
            if (result.status === 'success') {
                // 初始化练习状态
                practiceState = {
                    dialogueId: result.dialogue_id,
                    dialogueLines: result.dialogue_lines,
                    currentTurn: 0,
                    isActive: true,
                    currentHints: result.b_hints,
                    totalTurns: result.total_turns
                };
                
                // 折叠并禁用英语卡片
                const collapseBtn = cardElement.querySelector('.collapse-btn');
                const content = cardElement.querySelector('.dialogue-content');
                const practiceBtn = cardElement.querySelector('.practice-btn');
                
                if (content) {
                    content.style.display = 'none';
                }
                if (collapseBtn) {
                    collapseBtn.disabled = true;
                    collapseBtn.style.opacity = '0.5';
                    collapseBtn.style.cursor = 'not-allowed';
                }
                if (practiceBtn) {
                    practiceBtn.style.display = 'none';
                }
                
                // 创建练习模式UI
                createPracticeUI(result.a_text, result.a_audio_url, result.b_hints, result.total_turns);
                
                // 显示AI的第一句话（使用音频气泡）
                if (result.a_audio_url) {
                    createAudioBubble(result.a_text, result.a_audio_url, 'ai');
                } else {
                    addAIMessage(`A: ${result.a_text}`);
                }
                
                showSuccess('练习模式已开始！你是角色B，请回复A的话。');
            } else {
                showError(result.message || '开始练习失败');
                practiceBtn.disabled = false;
                practiceBtn.innerHTML = originalHTML;
            }
        } catch (error) {
            console.error('Error starting practice:', error);
            showError('开始练习失败：' + error.message);
            const practiceBtn = cardElement.querySelector('.practice-btn');
            if (practiceBtn) {
                practiceBtn.disabled = false;
            }
        }
    }
    
    // 创建练习模式UI
    function createPracticeUI(aText, aAudioUrl, hints, totalTurns) {
        // 移除旧的练习UI（如果存在）
        const oldPracticeUI = document.getElementById('practice-mode-ui');
        if (oldPracticeUI) {
            oldPracticeUI.remove();
        }
        
        const practiceUI = document.createElement('div');
        practiceUI.id = 'practice-mode-ui';
        practiceUI.className = 'practice-mode-container';
        practiceUI.innerHTML = `
            <div class="practice-header">
                <h3>🎯 练习模式</h3>
                <div class="practice-progress">
                    <span>进度：<span id="practice-current-turn">1</span>/<span id="practice-total-turns">${totalTurns}</span></span>
                </div>
            </div>
            <div class="practice-hints-panel" id="practice-hints-panel" style="display: none;">
                <div class="hints-header">
                    <h4>💡 提示</h4>
                </div>
                <div class="hints-content" id="hints-content">
                    <!-- 提示内容将动态填充 -->
                </div>
            </div>
            <div class="practice-dialogue-area" id="practice-dialogue-area">
                <!-- 对话历史将显示在这里 -->
            </div>
            <div class="practice-input-area">
                <button id="toggle-hints-btn" class="hint-toggle-btn">显示提示</button>
            </div>
        `;
        
        // 插入到消息列表
        const messagesList = document.getElementById('messages-list');
        if (!messagesList) {
            console.error('Messages list element not found');
            showError('无法找到消息列表，请刷新页面重试');
            return;
        }
        messagesList.appendChild(practiceUI);
        
        // 更新进度
        updatePracticeProgress(1, totalTurns);
        
        // 如果有提示，填充提示内容
        if (hints) {
            fillHintsContent(hints);
        }
        
        // 绑定事件 - 统一的切换按钮
        const toggleHintsBtn = document.getElementById('toggle-hints-btn');
        const hintsPanel = document.getElementById('practice-hints-panel');
        
        function updateToggleButton() {
            if (toggleHintsBtn && hintsPanel) {
                const isVisible = hintsPanel.style.display !== 'none';
                toggleHintsBtn.textContent = isVisible ? '隐藏提示' : '显示提示';
            }
        }
        
        function toggleHintsPanel() {
            if (hintsPanel) {
                const isVisible = hintsPanel.style.display !== 'none';
                hintsPanel.style.display = isVisible ? 'none' : 'block';
                updateToggleButton();
            }
        }
        
        if (toggleHintsBtn) {
            toggleHintsBtn.addEventListener('click', toggleHintsPanel);
        }
        
        // 初始化按钮状态
        updateToggleButton();
        
        scrollToBottom();
    }
    
    // 填充提示内容（只显示重点词组）
    function fillHintsContent(hints) {
        const hintsContent = document.getElementById('hints-content');
        if (!hintsContent) return;
        
        let html = '';
        
        // 只显示重点词组
        if (hints.phrases && hints.phrases.length > 0) {
            html += `<div class="hint-phrases-container">${hints.phrases.map(p => `<span class="hint-phrase-box">${p}</span>`).join('')}</div>`;
        } else {
            html = '<div class="hint-phrases-container"><span class="hint-phrase-box-empty">暂无提示</span></div>';
        }
        
        hintsContent.innerHTML = html;
    }
    
    // 更新练习进度
    function updatePracticeProgress(current, total) {
        const currentTurnEl = document.getElementById('practice-current-turn');
        const totalTurnsEl = document.getElementById('practice-total-turns');
        if (currentTurnEl) currentTurnEl.textContent = current;
        if (totalTurnsEl) totalTurnsEl.textContent = total;
    }
    
    // 创建音频气泡（Instagram风格）
    function createAudioBubble(text, audioUrl, type = 'ai') {
        const messagesList = document.getElementById('messages-list');
        if (!messagesList) return;
        
        // 创建消息容器
        const message = document.createElement('div');
        message.className = `message ${type === 'user' ? 'user' : 'ai'}`;
        
        const audioId = `audio-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        const audio = new Audio(audioUrl);
        let isPlaying = false;
        let duration = 0;
        let textExpanded = false;
        
        // 获取音频时长
        audio.addEventListener('loadedmetadata', () => {
            duration = audio.duration;
            const durationEl = message.querySelector('.audio-duration');
            if (durationEl) {
                durationEl.textContent = formatDuration(duration);
            }
        });
        
        // Instagram风格的消息结构
        message.innerHTML = `
            <div class="message-avatar">${type === 'user' ? '你' : 'AI'}</div>
            <div class="message-content-wrapper">
                <div class="message-content audio-message" data-audio-id="${audioId}">
                    <div class="audio-controls">
                        <button class="audio-play-btn" data-audio-id="${audioId}">
                            <svg class="audio-play-icon" width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                                <polygon points="8 5 8 19 19 12 8 5"></polygon>
                            </svg>
                            <svg class="audio-pause-icon" width="16" height="16" viewBox="0 0 24 24" fill="currentColor" style="display: none;">
                                <rect x="6" y="4" width="4" height="16"></rect>
                                <rect x="14" y="4" width="4" height="16"></rect>
                            </svg>
                        </button>
                        <div class="audio-waveform">
                            <div class="waveform-bar"></div>
                            <div class="waveform-bar"></div>
                            <div class="waveform-bar"></div>
                            <div class="waveform-bar"></div>
                            <div class="waveform-bar"></div>
                        </div>
                        <span class="audio-duration">--:--</span>
                    </div>
                    <div class="audio-text-content" style="display: none;">
                        ${text}
                    </div>
                </div>
            </div>
        `;
        
        const audioMessage = message.querySelector('.audio-message');
        const playBtn = message.querySelector('.audio-play-btn');
        const playIcon = message.querySelector('.audio-play-icon');
        const pauseIcon = message.querySelector('.audio-pause-icon');
        const waveform = message.querySelector('.audio-waveform');
        const textContent = message.querySelector('.audio-text-content');
        
        // 播放/暂停控制（点击播放按钮）
        playBtn.addEventListener('click', (e) => {
            e.stopPropagation(); // 阻止冒泡到消息容器
            
            if (isPlaying) {
                audio.pause();
                isPlaying = false;
                playIcon.style.display = 'block';
                pauseIcon.style.display = 'none';
                waveform.classList.remove('playing');
            } else {
                audio.play();
                isPlaying = true;
                playIcon.style.display = 'none';
                pauseIcon.style.display = 'block';
                waveform.classList.add('playing');
            }
        });
        
        audio.addEventListener('ended', () => {
            isPlaying = false;
            playIcon.style.display = 'block';
            pauseIcon.style.display = 'none';
            waveform.classList.remove('playing');
        });
        
        // 点击整个消息气泡展开/折叠文字（Instagram风格）
        audioMessage.addEventListener('click', (e) => {
            // 如果点击的是播放按钮，不处理
            if (e.target.closest('.audio-play-btn')) {
                return;
            }
            
            textExpanded = !textExpanded;
            if (textExpanded) {
                textContent.style.display = 'block';
                audioMessage.classList.add('text-expanded');
            } else {
                textContent.style.display = 'none';
                audioMessage.classList.remove('text-expanded');
            }
        });
        
        messagesList.appendChild(message);
        scrollToBottom();
        
        // 存储audio对象到message
        message.dataset.audioId = audioId;
        window[audioId] = audio;
    }
    
    // 格式化时长（秒转为MM:SS或SS，Instagram风格）
    function formatDuration(seconds) {
        if (isNaN(seconds) || seconds === 0) return '--:--';
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        // 如果小于1分钟，只显示秒数（Instagram风格）
        if (mins === 0) {
            return `${secs}"`;
        }
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }
    
    // 结束练习模式
    function endPracticeMode() {
        // 恢复英语卡片
        const cards = document.querySelectorAll('.english-dialogue-card');
        cards.forEach(card => {
            const collapseBtn = card.querySelector('.collapse-btn');
            const practiceBtn = card.querySelector('.practice-btn');
            
            if (collapseBtn) {
                collapseBtn.disabled = false;
                collapseBtn.style.opacity = '1';
                collapseBtn.style.cursor = 'pointer';
            }
            if (practiceBtn) {
                practiceBtn.style.display = 'inline-flex';
            }
        });
        
        // 清理练习状态
        practiceState = {
            dialogueId: null,
            dialogueLines: [],
            currentTurn: 0,
            isActive: false,
            currentHints: null,
            totalTurns: 0
        };
    }
    
    // 处理练习模式的用户输入
    async function handlePracticeInput(userInput) {
        console.log('handlePracticeInput called, isActive:', practiceState.isActive);
        if (!practiceState.isActive) {
            console.log('Not in practice mode, returning false');
            return false; // 不在练习模式，正常处理
        }
        
        console.log('In practice mode, processing input...');
        
        try {
            // 显示用户输入
            addUserMessage(userInput);
            
            // 调用API验证
            const response = await fetch('/api/practice/respond', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user_input: userInput,
                    dialogue_lines: practiceState.dialogueLines,
                    current_turn: practiceState.currentTurn
                })
            });
            
            const result = await response.json();
            console.log('Practice respond result:', result);
            
            if (result.status === 'success') {
                if (result.is_consistent) {
                    // 意思一致，继续下一轮
                    practiceState.currentTurn = result.next_turn;
                    practiceState.currentHints = result.next_b_hints;
                    
                    if (result.is_completed) {
                        // 练习完成
                        practiceState.isActive = false;
                        showSuccess('🎉 恭喜！练习完成！');
                        addAIMessage('练习已完成，你做得很好！');
                        
                        // 隐藏练习UI
                        const practiceUI = document.getElementById('practice-mode-ui');
                        if (practiceUI) {
                            practiceUI.style.opacity = '0.7';
                        }
                        
                        // 恢复英语卡片
                        endPracticeMode();
                    } else {
                        // 显示下一句A的台词（使用音频气泡）
                        if (result.next_a_text) {
                            if (result.next_a_audio_url) {
                                createAudioBubble(result.next_a_text, result.next_a_audio_url, 'ai');
                            } else {
                                addAIMessage(`A: ${result.next_a_text}`);
                            }
                            
                            // 更新提示
                            if (result.next_b_hints) {
                                fillHintsContent(result.next_b_hints);
                                practiceState.currentHints = result.next_b_hints;
                            }
                            
                            // 更新进度
                            updatePracticeProgress(practiceState.currentTurn + 1, practiceState.totalTurns);
                            
                            showSuccess('很好！继续下一句。');
                        }
                    }
                } else {
                    // 意思不一致
                    showError('意思不太一致，请再试试。你可以点击"显示提示"查看提示。');
                }
            } else {
                showError(result.message || '验证失败');
            }
            
            return true; // 已处理，不继续正常流程
        } catch (error) {
            console.error('Error handling practice input:', error);
            showError('处理失败：' + error.message);
            return true;
        }
    }

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

