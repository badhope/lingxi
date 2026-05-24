/**
 * DataAgent - Main Application JavaScript
 * 优化版本：修复语法错误，增强功能
 */

const messages = [];
const files = [];
let socket = null;
let isTyping = false;
let polishStyle = null;

// WebSocket Management
function initWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    socket = new WebSocket(wsUrl);

    socket.onopen = () => { 
        updateWsStatus(true); 
        console.log('WebSocket connected');
    };
    
    socket.onclose = () => { 
        updateWsStatus(false); 
        console.log('WebSocket disconnected, reconnecting...');
        setTimeout(initWebSocket, 5000); 
    };
    
    socket.onerror = (e) => { 
        console.error('WebSocket error:', e); 
        showToast('WebSocket connection error', 'error');
    };
    
    socket.onmessage = (e) => {
        try { 
            handleMessage(JSON.parse(e.data)); 
        } catch (err) { 
            console.error('Message parse error:', err); 
        }
    };
}

function updateWsStatus(connected) {
    const statusDot = document.getElementById('ws-status');
    const statusText = document.getElementById('ws-status-text');
    const headerDot = document.getElementById('header-status-dot');
    const headerText = document.getElementById('header-ws-status-text');

    if (statusDot) statusDot.classList.toggle('connected', connected);
    if (statusText) statusText.textContent = connected ? 'Connected' : 'Connecting...';
    if (headerDot) headerDot.classList.toggle('connected', connected);
    if (headerText) headerText.textContent = connected ? 'Connected' : 'Connecting...';
}

// Message Handler
function handleMessage(data) {
    const { type, content, title, id } = data;
    
    switch (type) {
        case 'message':
            addMessage('assistant', content, id);
            isTyping = false;
            updateTypingIndicator();
            break;
            
        case 'typing':
            isTyping = true;
            updateTypingIndicator();
            break;
            
        case 'thinking':
            updateThinking(data);
            break;
            
        case 'error':
            showToast(content, 'error');
            isTyping = false;
            updateTypingIndicator();
            break;
            
        case 'success':
            showToast(content, 'success');
            break;
            
        case 'warning':
            showToast(content, 'warning');
            break;
            
        default:
            console.log('Unknown message type:', type);
    }
}

// Message Display
function addMessage(role, content, id) {
    const container = document.getElementById('messages-container');
    if (!container) return;

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role === 'user' ? 'user-message' : 'assistant-message'}`;
    messageDiv.id = id || `msg-${Date.now()}`;

    const avatar = role === 'user' ? '👤' : '🤖';
    const time = new Date().toLocaleTimeString();
    
    messageDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">
            <div class="message-text">${escapeHtml(content)}</div>
            <div class="message-time">${time}</div>
        </div>
    `;

    container.appendChild(messageDiv);
    container.scrollTop = container.scrollHeight;
    
    messages.push({ role, content, id: messageDiv.id });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function updateThinking(data) {
    const container = document.getElementById('thinking-container');
    if (!container) return;

    const title = data.title || 'Thinking...';
    const content = data.content || '';

    container.innerHTML = `
        <div class="thinking-header">
            <span class="thinking-icon">💭</span>
            <span>${escapeHtml(title)}</span>
        </div>
        <div class="thinking-content">${escapeHtml(content)}</div>
    `;
    container.style.display = 'block';
}

function updateTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    if (!indicator) return;
    
    indicator.style.display = isTyping ? 'flex' : 'none';
}

// Toast Notifications
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.add('show');
    }, 10);

    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Send Message
async function sendMessage() {
    const inputBox = document.getElementById('input-box');
    if (!inputBox) return;

    const content = inputBox.value.trim();
    if (!content) return;

    if (!socket || socket.readyState !== WebSocket.OPEN) {
        showToast('WebSocket not connected', 'error');
        return;
    }

    addMessage('user', content);
    inputBox.value = '';
    updateCharCount();

    socket.send(JSON.stringify({
        type: 'message',
        content: content,
        files: files.map(f => f.name)
    }));

    isTyping = true;
    updateTypingIndicator();
}

// Character Count
function updateCharCount() {
    const inputBox = document.getElementById('input-box');
    const charCount = document.getElementById('char-count');
    if (!inputBox || !charCount) return;

    const count = inputBox.value.length;
    charCount.textContent = `${count}/10000`;
    charCount.style.color = count > 9000 ? '#ff4444' : '#666';
}

// File Upload
function addFilePreview(file) {
    const list = document.getElementById('file-list');
    if (!list) return;

    const card = document.createElement('div');
    card.className = 'file-card';
    
    const size = (file.size / 1024).toFixed(1) + ' KB';
    card.innerHTML = `
        <span class="file-icon">📄</span>
        <div class="file-info">
            <div class="file-name">${escapeHtml(file.name)}</div>
            <div class="file-size">${size}</div>
        </div>
        <button class="file-remove" onclick="removeFile('${escapeHtml(file.name)}')">×</button>
    `;

    list.appendChild(card);
}

function removeFile(filename) {
    const index = files.findIndex(f => f.name === filename);
    if (index > -1) {
        files.splice(index, 1);
        renderFileList();
    }
}

function renderFileList() {
    const list = document.getElementById('file-list');
    if (!list) return;
    
    list.innerHTML = '';
    files.forEach(file => addFilePreview(file));
}

// Modal Functions
function showModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'flex';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
    }
}

// Form Handlers
function handlePolishSubmit() {
    const style = document.getElementById('polish-type')?.value;
    const text = document.getElementById('polish-input')?.value;
    
    if (!text?.trim()) {
        showToast('Please enter text to polish', 'warning');
        return;
    }

    closeModal('polish-modal');
    
    const styleNames = { 
        academic: 'academic', 
        formal: 'formal', 
        concise: 'concise', 
        casual: 'casual' 
    };
    
    const prompt = `Please polish this text to be more ${styleNames[style] || style}:\n\n${text}`;
    document.getElementById('input-box').value = prompt;
    updateCharCount();
}

function handlePptSubmit() {
    const topic = document.getElementById('ppt-topic')?.value;
    const content = document.getElementById('ppt-content')?.value;

    if (!topic?.trim()) {
        showToast('Please enter PPT topic', 'warning');
        return;
    }

    closeModal('ppt-modal');
    
    let prompt = 'Please generate a PPT about: ' + topic;
    if (content?.trim()) prompt += '\n\nContent outline:\n' + content;
    
    document.getElementById('input-box').value = prompt;
    updateCharCount();
}

function handleTodoSubmit() {
    const text = document.getElementById('todo-input')?.value;
    
    if (!text?.trim()) {
        showToast('Please enter text', 'warning');
        return;
    }

    closeModal('todo-modal');
    
    const prompt = 'Extract todo items from this text:\n\n' + text;
    document.getElementById('input-box').value = prompt;
    updateCharCount();
}

function handleMeetingSubmit() {
    const text = document.getElementById('meeting-input')?.value;
    
    if (!text?.trim()) {
        showToast('Please enter meeting notes', 'warning');
        return;
    }

    closeModal('meeting-modal');
    
    const prompt = 'Generate meeting minutes from these notes:\n\n' + text;
    document.getElementById('input-box').value = prompt;
    updateCharCount();
}

function selectPolishStyle(style) {
    polishStyle = style;
    document.querySelectorAll('.style-option').forEach(opt => {
        opt.classList.toggle('selected', opt.dataset.style === style);
    });
}

// Navigation
function showSection(sectionId) {
    document.querySelectorAll('.section').forEach(section => {
        section.style.display = 'none';
    });
    
    const targetSection = document.getElementById(sectionId);
    if (targetSection) {
        targetSection.style.display = 'block';
    }
    
    highlightNav(sectionId + '-nav');
}

function highlightNav(navId) {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    
    const navItem = document.getElementById(navId);
    if (navItem) {
        navItem.classList.add('active');
    }
}

// Initialization
document.addEventListener('DOMContentLoaded', () => {
    initWebSocket();
    
    const inputBox = document.getElementById('input-box');
    if (inputBox) {
        inputBox.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        
        inputBox.addEventListener('input', updateCharCount);
    }
    
    // Enter key to send
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && e.target.id === 'input-box' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
        
        // Escape to close modals
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal').forEach(modal => {
                modal.style.display = 'none';
            });
        }
    });
    
    console.log('DataAgent initialized');
});
