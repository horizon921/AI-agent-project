document.addEventListener('DOMContentLoaded', function () {
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');

    // 🔥 检查必需元素是否存在
    if (!chatMessages || !userInput || !sendButton) {
        console.error('Required elements not found');
        return;
    }

    // 自动调整文本区域高度
    userInput.addEventListener('input', function () {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });

    // 🔥 改进的发送消息函数
    function sendMessage() {
        const message = userInput.value.trim();
        if (!message) return;

        // 禁用发送按钮防止重复发送
        sendButton.disabled = true;
        sendButton.textContent = '发送中...';

        addMessage(message, 'user');
        userInput.value = '';
        userInput.style.height = 'auto';
        addTypingIndicator();

        // 🔥 安全获取文件输入
        const form = new FormData();
        form.append('message', message);

        const fileInput = document.getElementById('file-input');
        const audioInput = document.getElementById('audio-input');

        if (fileInput && fileInput.files[0]) {
            form.append('file', fileInput.files[0]);
        }
        if (audioInput && audioInput.files[0]) {
            form.append('file', audioInput.files[0]);
        }

        // 🔥 改进的fetch处理
        fetch('/api/chat', {
            method: 'POST',
            body: form
        })
            .then(response => {
                // 🔥 检查HTTP状态
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                removeTypingIndicator();

                // 🔥 检查响应数据
                if (data && data.response) {
                    addMessage(data.response, 'bot');
                } else if (data && data.error) {
                    addMessage(`错误: ${data.error}`, 'bot', 'error');
                } else {
                    addMessage('收到了空响应，请重试。', 'bot', 'error');
                }
            })
            .catch(err => {
                removeTypingIndicator();
                console.error('Chat error:', err);

                // 🔥 更详细的错误信息
                let errorMessage = '抱歉，发生了错误：';
                if (err.message.includes('Failed to fetch')) {
                    errorMessage += '网络连接失败，请检查网络连接。';
                } else if (err.message.includes('HTTP')) {
                    errorMessage += `服务器错误 (${err.message})`;
                } else {
                    errorMessage += err.message || '未知错误，请稍后再试。';
                }

                addMessage(errorMessage, 'bot', 'error');
            })
            .finally(() => {
                // 🔥 恢复发送按钮
                sendButton.disabled = false;
                sendButton.textContent = '发送';
            });
    }

    // 🔥 改进的添加消息函数
    function addMessage(text, sender, type = 'normal') {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;

        // 🔥 添加错误样式
        if (type === 'error') {
            messageDiv.classList.add('error-message');
        }

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';

        // 🔥 改进的文本处理
        if (sender === 'bot' && text.includes('```')) {
            // 处理代码块
            contentDiv.innerHTML = formatBotMessage(text);
        } else {
            // 处理普通文本的换行
            const paragraphs = text.split('\n');
            paragraphs.forEach((paragraph, index) => {
                if (paragraph.trim() !== '') {
                    const p = document.createElement('p');
                    p.textContent = paragraph;
                    contentDiv.appendChild(p);
                }
                if (index < paragraphs.length - 1 && paragraph.trim() !== '') {
                    contentDiv.appendChild(document.createElement('br'));
                }
            });
        }

        messageDiv.appendChild(contentDiv);
        chatMessages.appendChild(messageDiv);

        // 🔥 平滑滚动到底部
        chatMessages.scrollTo({
            top: chatMessages.scrollHeight,
            behavior: 'smooth'
        });
    }

    // 🔥 新增：格式化机器人消息（支持基本Markdown）
    function formatBotMessage(text) {
        // 简单的Markdown处理
        return text
            .replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre><code class="language-$1">$2</code></pre>')
            .replace(/`([^`]+)`/g, '<code>$1</code>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n/g, '<br>');
    }

    // 添加"正在输入"指示器
    function addTypingIndicator() {
        // 🔥 防止重复添加
        removeTypingIndicator();

        const typingDiv = document.createElement('div');
        typingDiv.className = 'message bot-message typing-indicator';
        typingDiv.innerHTML = `
            <div class="message-content">
                <p>
                    <span class="typing-dots">
                        <span></span><span></span><span></span>
                    </span>
                    正在输入...
                </p>
            </div>
        `;
        chatMessages.appendChild(typingDiv);
        chatMessages.scrollTo({
            top: chatMessages.scrollHeight,
            behavior: 'smooth'
        });
    }

    // 移除"正在输入"指示器
    function removeTypingIndicator() {
        const typingIndicator = document.querySelector('.typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    // 🔥 防抖处理按钮点击
    let isSubmitting = false;
    sendButton.addEventListener('click', function () {
        if (!isSubmitting) {
            isSubmitting = true;
            sendMessage();
            setTimeout(() => { isSubmitting = false; }, 1000);
        }
    });

    // 按Enter键发送消息（Shift+Enter换行）
    userInput.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' && !e.shiftKey && !isSubmitting) {
            e.preventDefault();
            isSubmitting = true;
            sendMessage();
            setTimeout(() => { isSubmitting = false; }, 1000);
        }
    });

    // 🔥 新增：文件上传预览
    function setupFilePreview() {
        const fileInput = document.getElementById('file-input');
        if (fileInput) {
            fileInput.addEventListener('change', function (e) {
                const file = e.target.files[0];
                if (file) {
                    console.log('Selected file:', file.name, file.type, file.size);
                    // 可以添加文件预览逻辑
                }
            });
        }
    }

    setupFilePreview();
});
