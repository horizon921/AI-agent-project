// 页面加载时执行
document.addEventListener('DOMContentLoaded', () => {
    // UI 元素引用
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const messagesContainer = document.getElementById('messagesContainer');
    const userInput = document.getElementById('userInput');
    const sendBtn = document.getElementById('sendBtn');
    const statusIndicator = document.getElementById('statusIndicator');
    const temperatureInput = document.getElementById('temperature');
    const temperatureValue = document.getElementById('temperatureValue');
    const topPInput = document.getElementById('topP');
    const topPValue = document.getElementById('topPValue');
    const providerSelect = document.getElementById('modelProvider');
    const searchTreeholeBtn = document.getElementById('searchTreeholeBtn');
    const clearChatBtn = document.getElementById('clearChat');
    const tabButtons = document.querySelectorAll('.tab-btn');
    const updateTreeholeAuthBtn = document.getElementById('updateTreeholeAuth');
    
    // 当前对话的历史记录
    let conversationHistory = [];
    let currentMessageElement = null; // 当前正在接收的消息元素
    let activeController = null; // 当前活动的AbortController

    // 侧边栏切换
    sidebarToggle.addEventListener('click', () => {
        sidebar.classList.toggle('active');
    });

    // 标签页切换
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabId = button.getAttribute('data-tab');
            
            // 切换标签按钮状态
            tabButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            
            // 切换标签内容
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            document.getElementById(tabId).classList.add('active');
        });
    });

    // 模型供应商切换
    providerSelect.addEventListener('change', () => {
        const provider = providerSelect.value;
        document.querySelectorAll('.provider-settings').forEach(el => {
            el.style.display = 'none';
        });
        document.getElementById(`${provider}Settings`).style.display = 'block';
    });

    // Temperature 滑块更新
    temperatureInput.addEventListener('input', () => {
        temperatureValue.textContent = temperatureInput.value;
    });

    // Top-P 滑块更新
    topPInput.addEventListener('input', () => {
        topPValue.textContent = topPInput.value;
    });

    // 调整输入框高度
    userInput.addEventListener('input', () => {
        userInput.style.height = 'auto';
        userInput.style.height = `${Math.min(userInput.scrollHeight, 200)}px`;
    });

    // 发送按钮点击事件
    sendBtn.addEventListener('click', sendUserMessage);

    // 按下Enter发送消息（Shift+Enter换行）
    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendUserMessage();
        }
    });

    // 点击清除聊天按钮
    clearChatBtn.addEventListener('click', () => {
        if (confirm('确定要清除当前会话吗？')) {
            conversationHistory = [];
            
            // 保留AI的欢迎消息
            messagesContainer.innerHTML = '';
            addAIMessage('你好！我是AI助手，有什么我可以帮助你的吗？');
            
            // 保存到本地存储
            saveConversationToLocalStorage();
        }
    });

    // 更新树洞认证信息
    updateTreeholeAuthBtn.addEventListener('click', async () => {
        try {
            statusIndicator.textContent = '正在更新认证信息...';
            
            const serverUrl = document.getElementById('treeholeServer').value;
            const auth = document.getElementById('treeholeAuth').value;
            const cookie = document.getElementById('treeholeCookie').value;
            const xsrfToken = document.getElementById('treeholeXsrfToken').value;
            const uuid = document.getElementById('treeholeUuid').value;
            
            const response = await fetch(`${serverUrl}/api/update_auth`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    authorization: auth,
                    cookie: cookie,
                    xsrf_token: xsrfToken,
                    uuid: uuid,
                    user_agent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
                    sec_ch_ua: '"Chromium";v="136", "Not A(Brand";v="99"',
                    sec_ch_ua_platform: '"Windows"'
                })
            });
            
            const data = await response.json();
            if (data.status === 'success') {
                alert('认证信息更新成功！');
                statusIndicator.textContent = '空闲';
                
                // 保存到本地存储
                localStorage.setItem('treeholeServer', serverUrl);
                localStorage.setItem('treeholeAuth', auth);
                localStorage.setItem('treeholeCookie', cookie);
                localStorage.setItem('treeholeXsrfToken', xsrfToken);
                localStorage.setItem('treeholeUuid', uuid);
            } else {
                alert(`认证信息更新警告: ${data.message}`);
                statusIndicator.textContent = '空闲';
            }
        } catch (error) {
            console.error('更新认证信息失败', error);
            alert(`更新认证信息失败: ${error.message}`);
            statusIndicator.textContent = '错误';
        }
    });

    // 树洞搜索按钮事件
    searchTreeholeBtn.addEventListener('click', async () => {
        const keyword = prompt('请输入要搜索的树洞关键词:');
        if (!keyword || keyword.trim() === '') return;
        
        try {
            statusIndicator.textContent = '正在搜索树洞...';
            
            const serverUrl = document.getElementById('treeholeServer').value;
            const pageStart = parseInt(document.getElementById('treeholePageStart').value);
            const pageEnd = parseInt(document.getElementById('treeholePageEnd').value);
            const postLimit = parseInt(document.getElementById('treeholePostLimit').value);
            const commentsLimit = parseInt(document.getElementById('treeholeCommentsLimit').value);
            const fetchAll = document.getElementById('treeholeFetchAllComments').checked;
            
            const response = await fetch(`${serverUrl}/api/search`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    keyword: keyword,
                    page_start: pageStart,
                    page_end: pageEnd,
                    limit: postLimit,
                    max_comments_per_post: commentsLimit,
                    fetch_all_comments: fetchAll
                })
            });
            
            if (!response.ok) {
                throw new Error(`Server responded with status: ${response.status}`);
            }
            
            const data = await response.json();
            displayTreeholeResults(data, keyword);
            statusIndicator.textContent = '空闲';
        } catch (error) {
            console.error('搜索树洞失败', error);
            alert(`搜索树洞失败: ${error.message}`);
            statusIndicator.textContent = '错误';
        }
    });

    // 显示树洞搜索结果
    function displayTreeholeResults(data, keyword) {
        // 构建消息文本
        let messageText = `## 北大树洞搜索结果: "${keyword}"\n\n`;
        messageText += `找到符合条件的帖子数: ${data.total_posts_found_in_api}\n`;
        messageText += `实际获取的帖子数: ${data.fetched_posts_count}\n\n`;
        
        // 如果有结果，展示树洞内容
        if (data.posts && data.posts.length > 0) {
            const posts = data.posts;
            
            for (let i = 0; i < Math.min(posts.length, 10); i++) {  // 最多显示10个帖子
                const post = posts[i];
                const date = new Date(post.timestamp * 1000).toLocaleString();
                
                messageText += `---\n\n`;
                messageText += `### 树洞 #${post.pid}\n`;
                messageText += `**时间**: ${date} | **点赞**: ${post.likenum} | **回复**: ${post.reply}\n\n`;
                messageText += `${post.text || '(无内容)'}\n\n`;
                
                if (post.comments && post.comments.length > 0) {
                    messageText += `#### 评论 (${post.comments.length})\n\n`;
                    
                    for (let j = 0; j < Math.min(post.comments.length, 5); j++) {  // 最多显示5条评论
                        const comment = post.comments[j];
                        const commentDate = new Date(comment.timestamp * 1000).toLocaleString();
                        
                        messageText += `**${comment.name}** (${commentDate}):\n`;
                        messageText += `${comment.text}\n\n`;
                    }
                    
                    if (post.comments.length > 5) {
                        messageText += `*还有 ${post.comments.length - 5} 条评论未显示*\n\n`;
                    }
                }
            }
            
            if (posts.length > 10) {
                messageText += `\n*还有 ${posts.length - 10} 个树洞未显示*`;
            }
        } else {
            messageText += "没有找到符合条件的树洞。";
        }
        
        // 添加到对话框中
        addAIMessage(messageText);
        
        // 添加到对话历史（但标记为系统消息，不发送到AI）
        conversationHistory.push({
            role: "system",
            content: `[用户搜索了北大树洞，关键词: "${keyword}"，找到 ${data.fetched_posts_count} 个结果]`
        });
    }

    // 发送用户消息
    async function sendUserMessage() {
        const message = userInput.value.trim();
        if (!message) return;
        
        // 中断当前正在进行的请求
        if (activeController) {
            activeController.abort();
            activeController = null;
        }
        
        // 添加用户消息到界面
        addUserMessage(message);
        
        // 清空输入框并重置高度
        userInput.value = '';
        userInput.style.height = 'auto';
        
        // 添加消息到历史记录
        conversationHistory.push({
            role: "user",
            content: message
        });
        
        // 保存到本地存储
        saveConversationToLocalStorage();
        
        // 向服务器请求AI回复
        try {
            statusIndicator.textContent = '思考中...';
            await getAIResponse();
        } catch (error) {
            console.error('获取AI响应出错', error);
            if (error.name !== 'AbortError') {
                addAIMessage(`抱歉，发生了一个错误: ${error.message}`);
                statusIndicator.textContent = '错误';
            }
        }
    }

    // 获取AI响应
    async function getAIResponse() {
        const provider = document.getElementById('modelProvider').value;
        const temperature = parseFloat(document.getElementById('temperature').value);
        const topP = parseFloat(document.getElementById('topP').value);
        const maxTokens = parseInt(document.getElementById('maxTokens').value);
        const streaming = document.getElementById('streaming').checked;
        
        // 初始化AI消息容器
        addAIMessage('', true);
        
        // 创建AbortController用于取消请求
        activeController = new AbortController();
        
        try {
            switch(provider) {
                case 'openai':
                    await callOpenAI(temperature, topP, maxTokens, streaming);
                    break;
                case 'anthropic':
                    await callAnthropic(temperature, topP, maxTokens, streaming);
                    break;
                case 'custom':
                    await callCustomMCP(temperature, topP, maxTokens, streaming);
                    break;
                default:
                    throw new Error('未知的模型供应商');
            }
        } finally {
            activeController = null;
            statusIndicator.textContent = '空闲';
        }
    }

    // 调用OpenAI API
    async function callOpenAI(temperature, topP, maxTokens, streaming) {
        const apiKey = document.getElementById('openaiApiKey').value;
        const model = document.getElementById('openaiModel').value;
        const endpoint = document.getElementById('openaiEndpoint').value;
        
        if (!apiKey) {
            throw new Error('未设置OpenAI API Key');
        }
        
        const messages = conversationHistory.map(msg => ({
            role: msg.role,
            content: msg.content
        }));
        
        const requestBody = {
            model: model,
            messages: messages,
            temperature: temperature,
            top_p: topP,
            max_tokens: maxTokens,
            stream: streaming
        };
        
        if (streaming) {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${apiKey}`
                },
                body: JSON.stringify(requestBody),
                signal: activeController.signal
            });
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error?.message || `HTTP error: ${response.status}`);
            }
            
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let completeMessage = '';
            
            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                
                const chunk = decoder.decode(value, { stream: true });
                const lines = chunk.split('\n');
                
                for (const line of lines) {
                    if (line.startsWith('data: ') && line !== 'data: [DONE]') {
                        try {
                            const jsonStr = line.slice(6);
                            const json = JSON.parse(jsonStr);
                            const content = json.choices[0]?.delta?.content || '';
                            
                            if (content) {
                                updateCurrentAIMessage(content);
                                completeMessage += content;
                            }
                        } catch (e) {
                            console.warn('Error parsing SSE line', e, line);
                        }
                    }
                }
            }
            
            // 完成后将完整消息添加到历史记录
            if (completeMessage) {
                conversationHistory.push({
                    role: 'assistant',
                    content: completeMessage
                });
                saveConversationToLocalStorage();
            }
        } else {
            // 非流式请求
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${apiKey}`
                },
                body: JSON.stringify(requestBody),
                signal: activeController.signal
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error?.message || `HTTP error: ${response.status}`);
            }
            
            const messageContent = data.choices[0].message.content;
            updateCurrentAIMessage(messageContent);
            
            // 添加到历史记录
            conversationHistory.push({
                role: 'assistant',
                content: messageContent
            });
            saveConversationToLocalStorage();
        }
    }

    // 调用Anthropic API
    async function callAnthropic(temperature, topP, maxTokens, streaming) {
        const apiKey = document.getElementById('anthropicApiKey').value;
        const model = document.getElementById('anthropicModel').value;
        const endpoint = document.getElementById('anthropicEndpoint').value;
        
        if (!apiKey) {
            throw new Error('未设置Anthropic API Key');
        }
        
        // 将对话历史转换为Anthropic格式
        const messages = [];
        for (const msg of conversationHistory) {
            if (msg.role === 'system') continue;  // Anthropic处理system消息的方式不同
            
            const role = msg.role === 'user' ? 'user' : 'assistant';
            messages.push({
                role: role,
                content: msg.content
            });
        }
        
        // 提取系统消息
        const systemMessages = conversationHistory
            .filter(msg => msg.role === 'system')
            .map(msg => msg.content)
            .join('\n');
        
        const requestBody = {
            model: model,
            messages: messages,
            system: systemMessages || undefined,
            temperature: temperature,
            top_p: topP,
            max_tokens: maxTokens,
            stream: streaming
        };
        
        if (streaming) {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Anthropic-Version': '2023-06-01',
                    'x-api-key': apiKey
                },
                body: JSON.stringify(requestBody),
                signal: activeController.signal
            });
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error?.message || `HTTP error: ${response.status}`);
            }
            
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let completeMessage = '';
            
            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                
                const chunk = decoder.decode(value, { stream: true });
                const lines = chunk.split('\n');
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            if (line === 'data: [DONE]') continue;
                            
                            const jsonStr = line.slice(6);
                            const json = JSON.parse(jsonStr);
                            const content = json.delta?.text || '';
                            
                            if (content) {
                                updateCurrentAIMessage(content);
                                completeMessage += content;
                            }
                        } catch (e) {
                            console.warn('Error parsing SSE line', e, line);
                        }
                    }
                }
            }
            
            // 完成后将完整消息添加到历史记录
            if (completeMessage) {
                conversationHistory.push({
                    role: 'assistant',
                    content: completeMessage
                });
                saveConversationToLocalStorage();
            }
        } else {
            // 非流式请求
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Anthropic-Version': '2023-06-01',
                    'x-api-key': apiKey
                },
                body: JSON.stringify(requestBody),
                signal: activeController.signal
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error?.message || `HTTP error: ${response.status}`);
            }
            
            // 添加到
            const messageContent = data.content[0].text;
            updateCurrentAIMessage(messageContent);
            
            // 添加到历史记录
            conversationHistory.push({
                role: 'assistant',
                content: messageContent
            });
            saveConversationToLocalStorage();
        }
    }

    // 调用自定义MCP服务器
    async function callCustomMCP(temperature, topP, maxTokens, streaming) {
        const name = document.getElementById('customName').value;
        const endpoint = document.getElementById('customEndpoint').value;
        const authType = document.getElementById('customAuthType').value;
        const authKey = document.getElementById('customAuthKey').value;
        
        if (!endpoint) {
            throw new Error('未设置MCP服务器端点');
        }
        
        // 构建请求头
        const headers = {
            'Content-Type': 'application/json',
        };
        
        if (authType === 'api_key') {
            headers['x-api-key'] = authKey;
        } else if (authType === 'bearer') {
            headers['Authorization'] = `Bearer ${authKey}`;
        }
        
        // 构建请求体
        const messages = conversationHistory.map(msg => ({
            role: msg.role,
            content: msg.content
        }));
        
        const requestBody = {
            messages: messages,
            temperature: temperature,
            top_p: topP,
            max_tokens: maxTokens,
            stream: streaming,
            model: name || 'custom-model'  // 自定义模型名称
        };
        
        if (streaming) {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify(requestBody),
                signal: activeController.signal
            });
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error?.message || `HTTP error: ${response.status}`);
            }
            
            // 处理流式响应
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let completeMessage = '';
            
            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                
                const chunk = decoder.decode(value, { stream: true });
                const lines = chunk.split('\n');
                
                for (const line of lines) {
                    if (line.startsWith('data: ') && line !== 'data: [DONE]') {
                        try {
                            const jsonStr = line.slice(6);
                            const json = JSON.parse(jsonStr);
                            // 适配不同的MCP流式接口格式
                            const content = 
                                json.choices?.[0]?.delta?.content || 
                                json.delta?.text || 
                                json.content || 
                                '';
                            
                            if (content) {
                                updateCurrentAIMessage(content);
                                completeMessage += content;
                            }
                        } catch (e) {
                            console.warn('Error parsing SSE line', e, line);
                        }
                    }
                }
            }
            
            // 完成后将完整消息添加到历史记录
            if (completeMessage) {
                conversationHistory.push({
                    role: 'assistant',
                    content: completeMessage
                });
                saveConversationToLocalStorage();
            }
        } else {
            // 非流式请求
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify(requestBody),
                signal: activeController.signal
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error?.message || `HTTP error: ${response.status}`);
            }
            
            // 适配不同的MCP接口响应格式
            const messageContent = 
                data.choices?.[0]?.message?.content || 
                data.content?.[0]?.text || 
                data.content || 
                '';
                
            updateCurrentAIMessage(messageContent);
            
            // 添加到历史记录
            conversationHistory.push({
                role: 'assistant',
                content: messageContent
            });
            saveConversationToLocalStorage();
        }
    }

    // 添加用户消息到界面
    function addUserMessage(text) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', 'message-user');
        
        const avatarElement = document.createElement('div');
        avatarElement.classList.add('message-avatar', 'avatar-user');
        avatarElement.textContent = 'U';
        
        const contentElement = document.createElement('div');
        contentElement.classList.add('message-content');
        contentElement.textContent = text;
        
        messageElement.appendChild(avatarElement);
        messageElement.appendChild(contentElement);
        
        messagesContainer.appendChild(messageElement);
        scrollToBottom();
    }

    // 添加AI消息到界面
    function addAIMessage(text, loading = false) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', 'message-ai');
        
        const avatarElement = document.createElement('div');
        avatarElement.classList.add('message-avatar', 'avatar-ai');
        avatarElement.textContent = 'AI';
        
        const contentElement = document.createElement('div');
        contentElement.classList.add('message-content');
        
        if (loading) {
            contentElement.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
            currentMessageElement = contentElement;
        } else {
            contentElement.innerHTML = renderMarkdown(text);
        }
        
        messageElement.appendChild(avatarElement);
        messageElement.appendChild(contentElement);
        
        messagesContainer.appendChild(messageElement);
        scrollToBottom();
        
        return messageElement;
    }

    // 更新当前AI消息内容
    function updateCurrentAIMessage(text) {
        if (!currentMessageElement) return;
        
        // 如果是第一次更新，清除加载指示器
        if (currentMessageElement.querySelector('.typing-indicator')) {
            currentMessageElement.innerHTML = '';
        }
        
        const content = renderMarkdown(
            currentMessageElement.innerHTML + text
        );
        
        currentMessageElement.innerHTML = content;
        scrollToBottom();
    }

    // 渲染Markdown内容
    function renderMarkdown(text) {
        marked.setOptions({
            breaks: true,
            gfm: true,
            highlight: function(code, language) {
                if (language && hljs.getLanguage(language)) {
                    try {
                        return hljs.highlight(code, { language }).value;
                    } catch (err) {}
                }
                return hljs.highlightAuto(code).value;
            }
        });
        
        return marked.parse(text);
    }

    // 滚动到底部
    function scrollToBottom() {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    // 保存对话历史到本地存储
    function saveConversationToLocalStorage() {
        localStorage.setItem('conversationHistory', JSON.stringify(conversationHistory));
    }

    // 从本地存储加载对话历史
    function loadConversationFromLocalStorage() {
        const saved = localStorage.getItem('conversationHistory');
        if (saved) {
            try {
                conversationHistory = JSON.parse(saved);
                
                // 重新渲染对话
                messagesContainer.innerHTML = '';
                
                for (const message of conversationHistory) {
                    if (message.role === 'user') {
                        addUserMessage(message.content);
                    } else if (message.role === 'assistant') {
                        addAIMessage(message.content);
                    }
                    // 系统消息不显示在界面上
                }
                
                // 如果没有消息，添加一个默认的AI欢迎消息
                if (conversationHistory.length === 0) {
                    addAIMessage('你好！我是AI助手，有什么我可以帮助你的吗？');
                }
            } catch (e) {
                console.error('加载对话历史失败', e);
                // 出错时清空对话历史
                conversationHistory = [];
                messagesContainer.innerHTML = '';
                addAIMessage('你好！我是AI助手，有什么我可以帮助你的吗？');
            }
        }
    }

    // 加载保存的设置
    function loadSavedSettings() {
        // OpenAI 设置
        if (localStorage.getItem('openaiApiKey')) {
            document.getElementById('openaiApiKey').value = localStorage.getItem('openaiApiKey');
        }
        if (localStorage.getItem('openaiModel')) {
            document.getElementById('openaiModel').value = localStorage.getItem('openaiModel');
        }
        if (localStorage.getItem('openaiEndpoint')) {
            document.getElementById('openaiEndpoint').value = localStorage.getItem('openaiEndpoint');
        }
        
        // Anthropic 设置
        if (localStorage.getItem('anthropicApiKey')) {
            document.getElementById('anthropicApiKey').value = localStorage.getItem('anthropicApiKey');
        }
        if (localStorage.getItem('anthropicModel')) {
            document.getElementById('anthropicModel').value = localStorage.getItem('anthropicModel');
        }
        if (localStorage.getItem('anthropicEndpoint')) {
            document.getElementById('anthropicEndpoint').value = localStorage.getItem('anthropicEndpoint');
        }
        
        // 自定义 MCP 设置
        if (localStorage.getItem('customName')) {
            document.getElementById('customName').value = localStorage.getItem('customName');
        }
        if (localStorage.getItem('customEndpoint')) {
            document.getElementById('customEndpoint').value = localStorage.getItem('customEndpoint');
        }
        if (localStorage.getItem('customAuthType')) {
            document.getElementById('customAuthType').value = localStorage.getItem('customAuthType');
        }
        if (localStorage.getItem('customAuthKey')) {
            document.getElementById('customAuthKey').value = localStorage.getItem('customAuthKey');
        }
        
        // 模型参数
        if (localStorage.getItem('temperature')) {
            const temp = localStorage.getItem('temperature');
            document.getElementById('temperature').value = temp;
            document.getElementById('temperatureValue').textContent = temp;
        }
        if (localStorage.getItem('topP')) {
            const topP = localStorage.getItem('topP');
            document.getElementById('topP').value = topP;
            document.getElementById('topPValue').textContent = topP;
        }
        if (localStorage.getItem('maxTokens')) {
            document.getElementById('maxTokens').value = localStorage.getItem('maxTokens');
        }
        if (localStorage.getItem('streaming')) {
            document.getElementById('streaming').checked = localStorage.getItem('streaming') === 'true';
        }
        
        // 模型供应商
        if (localStorage.getItem('modelProvider')) {
            const provider = localStorage.getItem('modelProvider');
            document.getElementById('modelProvider').value = provider;
            
            // 显示正确的设置面板
            document.querySelectorAll('.provider-settings').forEach(el => {
                el.style.display = 'none';
            });
            document.getElementById(`${provider}Settings`).style.display = 'block';
        }
        
        // 树洞设置
        if (localStorage.getItem('treeholeServer')) {
            document.getElementById('treeholeServer').value = localStorage.getItem('treeholeServer');
        }
        if (localStorage.getItem('treeholeAuth')) {
            document.getElementById('treeholeAuth').value = localStorage.getItem('treeholeAuth');
        }
        if (localStorage.getItem('treeholeCookie')) {
            document.getElementById('treeholeCookie').value = localStorage.getItem('treeholeCookie');
        }
        if (localStorage.getItem('treeholeXsrfToken')) {
            document.getElementById('treeholeXsrfToken').value = localStorage.getItem('treeholeXsrfToken');
        }
        if (localStorage.getItem('treeholeUuid')) {
            document.getElementById('treeholeUuid').value = localStorage.getItem('treeholeUuid');
        }
        if (localStorage.getItem('treeholePageStart')) {
            document.getElementById('treeholePageStart').value = localStorage.getItem('treeholePageStart');
        }
        if (localStorage.getItem('treeholePageEnd')) {
            document.getElementById('treeholePageEnd').value = localStorage.getItem('treeholePageEnd');
        }
        if (localStorage.getItem('treeholePostLimit')) {
            document.getElementById('treeholePostLimit').value = localStorage.getItem('treeholePostLimit');
        }
        if (localStorage.getItem('treeholeCommentsLimit')) {
            document.getElementById('treeholeCommentsLimit').value = localStorage.getItem('treeholeCommentsLimit');
        }
        if (localStorage.getItem('treeholeFetchAllComments')) {
            document.getElementById('treeholeFetchAllComments').checked = localStorage.getItem('treeholeFetchAllComments') === 'true';
        }
    }

    // 保存设置到本地存储
    function saveSettings() {
        // OpenAI 设置
        localStorage.setItem('openaiApiKey', document.getElementById('openaiApiKey').value);
        localStorage.setItem('openaiModel', document.getElementById('openaiModel').value);
        localStorage.setItem('openaiEndpoint', document.getElementById('openaiEndpoint').value);
        
        // Anthropic 设置
        localStorage.setItem('anthropicApiKey', document.getElementById('anthropicApiKey').value);
        localStorage.setItem('anthropicModel', document.getElementById('anthropicModel').value);
        localStorage.setItem('anthropicEndpoint', document.getElementById('anthropicEndpoint').value);
        
        // 自定义 MCP 设置
        localStorage.setItem('customName', document.getElementById('customName').value);
        localStorage.setItem('customEndpoint', document.getElementById('customEndpoint').value);
        localStorage.setItem('customAuthType', document.getElementById('customAuthType').value);
        localStorage.setItem('customAuthKey', document.getElementById('customAuthKey').value);
        
        // 模型
        // 模型参数
        localStorage.setItem('temperature', document.getElementById('temperature').value);
        localStorage.setItem('topP', document.getElementById('topP').value);
        localStorage.setItem('maxTokens', document.getElementById('maxTokens').value);
        localStorage.setItem('streaming', document.getElementById('streaming').checked);
        
        // 模型供应商
        localStorage.setItem('modelProvider', document.getElementById('modelProvider').value);
        
        // 不保存敏感的树洞认证信息，这些应该通过更新按钮单独保存
    }

    // 为设置输入添加变更监听器以保存设置
    function addSettingsChangeListeners() {
        const settingsInputs = [
            'openaiModel', 'openaiEndpoint',
            'anthropicModel', 'anthropicEndpoint',
            'customName', 'customEndpoint', 'customAuthType',
            'temperature', 'topP', 'maxTokens', 'streaming',
            'modelProvider'
        ];
        
        settingsInputs.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.addEventListener('change', saveSettings);
            }
        });
        
        // API Keys 需要在失去焦点时保存，避免频繁写入
        const apiKeys = [
            'openaiApiKey', 'anthropicApiKey', 'customAuthKey'
        ];
        
        apiKeys.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.addEventListener('blur', saveSettings);
            }
        });
    }

    // 初始化
    function init() {
        // 加载保存的设置
        loadSavedSettings();
        
        // 加载对话历史
        loadConversationFromLocalStorage();
        
        // 添加设置变更监听
        addSettingsChangeListeners();
        
        // 初始显示正确的设置面板
        const provider = document.getElementById('modelProvider').value;
        document.querySelectorAll('.provider-settings').forEach(el => {
            el.style.display = 'none';
        });
        document.getElementById(`${provider}Settings`).style.display = 'block';
    }

    // 启动应用
    init();
});
