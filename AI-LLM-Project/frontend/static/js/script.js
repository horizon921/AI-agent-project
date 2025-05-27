document.addEventListener('DOMContentLoaded', function () {
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');

    // 自动调整文本区域高度
    userInput.addEventListener('input', function () {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });

    // 发送消息
    function sendMessage() {
        const message = userInput.value.trim();
        if (message === '') return;

        // 添加用户消息到聊天
        addMessage(message, 'user');

        // 清空输入框并重置高度
        userInput.value = '';
        userInput.style.height = 'auto';

        // 显示"正在输入"指示器
        addTypingIndicator();

        // 发送请求到后端
        fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message })
        })
            .then(response => response.json())
            .then(data => {
                // 移除"正在输入"指示器
                removeTypingIndicator();
                // 添加机器人回复
                addMessage(data.response, 'bot');
            })
            .catch(error => {
                // 移除"正在输入"指示器
                removeTypingIndicator();
                // 显示错误消息
                addMessage('抱歉，发生了错误，请稍后再试。', 'bot');
                console.error('Error:', error);
            });
    }

    // 添加消息到聊天界面
    function addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';

        // 处理文本中的换行
        const paragraphs = text.split('\n');
        paragraphs.forEach((paragraph, index) => {
            if (paragraph.trim() !== '') {
                const p = document.createElement('p');
                p.textContent = paragraph;
                contentDiv.appendChild(p);
            }
            if (index < paragraphs.length - 1) {
                contentDiv.appendChild(document.createElement('br'));
            }
        });

        messageDiv.appendChild(contentDiv);
        chatMessages.appendChild(messageDiv);

        // 滚动到底部
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // 添加"正在输入"指示器
    function addTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message bot-message typing-indicator';
        typingDiv.innerHTML = '<div class="message-content"><p>正在输入...</p></div>';
        chatMessages.appendChild(typingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // 移除"正在输入"指示器
    function removeTypingIndicator() {
        const typingIndicator = document.querySelector('.typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    // 点击发送按钮
    sendButton.addEventListener('click', sendMessage);

    // 按Enter键发送消息（Shift+Enter换行）
    userInput.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
});
