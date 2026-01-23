// ==========================================
// 1. DOM ELEMENTS SELECTION
// ==========================================
const aiTextContainer = document.getElementById('ai-text-container');
const btnAccept       = document.getElementById('btn-accept');
const btnRefine       = document.getElementById('btn-refine');
const btnCopy         = document.getElementById('btn-copy');

// Chat Section Elements
const chatSection     = document.getElementById('chat-section');
const closeChatBtn    = document.getElementById('close-chat');
const chatHistory     = document.getElementById('chat-history');
const chatInput       = document.getElementById('chat-input');
const sendBtn         = document.getElementById('send-msg');

// ==========================================
// 2. PAGE INITIALIZATION
// ==========================================
document.addEventListener('DOMContentLoaded', () => {
    // A. Set today's date in the UI
    document.getElementById('date-display').textContent = new Date().toISOString().split('T')[0];

    // B. Retrieve text saved by the previous page
    const storedText = localStorage.getItem('aiResultText');
    if (storedText) {
        aiTextContainer.textContent = storedText;
    } else {
        // Error handling if opened directly without data
        aiTextContainer.textContent = "لم يتم العثور على نص. الرجاء إعادة المحاولة من الصفحة الرئيسية.";
        aiTextContainer.style.color = "#ef4444";
    }
});

// ==========================================
// 3. MAIN BUTTON ACTIONS
// ==========================================

// COPY BUTTON: Copies text to clipboard
btnCopy.addEventListener('click', () => {
    navigator.clipboard.writeText(aiTextContainer.textContent);
    
    // Feedback animation (Change icon briefly)
    const originalText = btnCopy.textContent;
    btnCopy.textContent = "✅";
    setTimeout(() => btnCopy.textContent = originalText, 2000);
});

// ACCEPT BUTTON: Saves and finishes
btnAccept.addEventListener('click', () => {
    if(confirm("هل أنت متأكد من اعتماد النتيجة؟")) {
        alert("تم الحفظ!");
        // Logic to redirect or close would go here
    }
});

// ==========================================
// 4. CHAT SHOW/HIDE LOGIC
// ==========================================

// OPEN CHAT
btnRefine.addEventListener('click', () => {
    // 1. Remove the 'hidden' attribute to make it visible
    chatSection.removeAttribute('hidden');
    
    // 2. Smooth scroll down so the user sees it opening
    setTimeout(() => {
        chatSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
        chatInput.focus();
    }, 100);
});

// CLOSE CHAT
closeChatBtn.addEventListener('click', () => {
    // 1. Add 'hidden' back to hide it
    chatSection.setAttribute('hidden', '');
    
    // 2. Scroll back up to the main card
    window.scrollTo({ top: 0, behavior: 'smooth' });
});

// ==========================================
// 5. MESSAGING LOGIC
// ==========================================

sendBtn.addEventListener('click', sendMessage);

// Allow pressing "Enter" to send
chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

function sendMessage() {
    const text = chatInput.value.trim();
    if (!text) return;

    // 1. Add User Message
    addMessage(text, 'user');
    chatInput.value = '';

    // 2. Simulate AI Thinking/Response
    // In a real app, this would be a fetch() call to your API
    setTimeout(() => {
        addMessage("جاري العمل على طلبك... (محاكاة)", 'ai');
    }, 1000);
}

// Helper to create HTML bubbles
function addMessage(text, sender) {
    const div = document.createElement('div');
    div.className = `message ${sender}`;
    div.innerHTML = `<div class="bubble">${text}</div>`;
    
    chatHistory.appendChild(div);
    
    // Auto-scroll to the bottom of the chat
    chatHistory.scrollTop = chatHistory.scrollHeight;
}