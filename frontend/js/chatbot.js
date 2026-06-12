// ============================================================
// ScamShield v5 – chatbot.js  (FIXED)
// AI-powered via Anthropic API (claude-sonnet-4-20250514)
//
// FIX NOTES:
//  - Uses event delegation so bubble click works even when
//    chatbot HTML is injected after this script loads (nav.js)
//  - initChatbot() is called both on DOMContentLoaded AND
//    exported as window.initChatbot for nav.js to call after
//    it injects the chatbot HTML
//  - Added chips container to the injected HTML
// ============================================================

const CHATBOT_SYSTEM_PROMPT = `You are ScamGuard AI, the intelligent assistant built into ScamShield — India's job scam detection platform.

Your role:
- Help job seekers identify fake or suspicious job postings
- Explain ScamShield features and guide users to the right page
- Give quick risk assessments when users describe a job offer
- Answer questions about fraud patterns, domain checks, trust cards

Platform pages you can guide users to:
- Home / Analyzer (index.html) — paste URL or description to get a scam score
- Compare Jobs (compare.html) — side-by-side comparison of two job URLs
- Community (community.html) — browse and search real user reports
- Report Scam (report.html) — submit a scam report with evidence
- Live Feed (live-feed.html) — real-time scam detections
- My Profile (profile.html) — view activity, reports, saved items

Tone: Friendly, concise, practical. Max 3-4 sentences per reply.
Format: Use **bold** for key terms. Use bullet points only when listing 3+ items.
Identity: You are ScamGuard AI by ScamShield. Never say you are Claude or made by Anthropic.
Language: Respond in the same language the user writes in (Hindi/English/Marathi etc.).`;

const QUICK_CHIPS = [
  "Signs of a fake job",
  "How to read my Trust Card?",
  "Registration fee asked — scam?",
  "WhatsApp only recruiter safe?",
  "How to report a scam?",
  "Compare two job URLs"
];

// ── State ──────────────────────────────────────────────────
let _chatHistory = [];
let _isTyping    = false;
let _initialized = false;

// ── Inject chatbot HTML if not already present ─────────────
function _ensureChatbotHTML() {
  if (document.querySelector('.chatbot-bubble')) return; // already there

  document.body.insertAdjacentHTML('beforeend', `
    <div class="chatbot-bubble" title="Ask ScamGuard AI" id="chatbot-bubble">🤖</div>
    <div class="chatbot-panel" id="chatbot-panel">
      <div class="chatbot-header">
        <div class="chatbot-avatar">🛡️</div>
        <div>
          <div class="chatbot-name">ScamGuard AI</div>
          <div class="chatbot-status">● Online</div>
        </div>
        <button class="chatbot-close" id="chatbot-close">✕</button>
      </div>
      <div class="chatbot-msgs" id="chatbot-msgs"></div>
      <div class="chatbot-chips" id="chatbot-chips"></div>
      <div class="chatbot-input-row">
        <input class="chatbot-input" id="chatbot-input" placeholder="Ask about job scams…" autocomplete="off"/>
        <button class="chatbot-send" id="chatbot-send">➤</button>
      </div>
    </div>`);
}

// ── Init — safe to call multiple times ────────────────────
function initChatbot() {
  _ensureChatbotHTML();

  if (_initialized) return;

  // Use event delegation on document.body — works regardless of when HTML was injected
  document.body.addEventListener('click', function(e) {
    const bubble = e.target.closest('.chatbot-bubble');
    const closeBtn = e.target.closest('.chatbot-close');
    const sendBtn = e.target.closest('.chatbot-send');
    const chip = e.target.closest('.chatbot-chip');

    if (bubble) {
      const panel = document.querySelector('.chatbot-panel');
      if (!panel) return;
      const isOpen = panel.classList.toggle('open');
      if (isOpen && _chatHistory.length === 0) _greetUser();
      return;
    }

    if (closeBtn) {
      document.querySelector('.chatbot-panel')?.classList.remove('open');
      return;
    }

    if (sendBtn) { _sendMessage(); return; }

    if (chip) {
      const input = document.querySelector('.chatbot-input');
      if (input) { input.value = chip.textContent; _sendMessage(); }
      return;
    }

    // Click outside panel closes it
    const panel = document.querySelector('.chatbot-panel');
    if (panel?.classList.contains('open')) {
      if (!panel.contains(e.target) && !e.target.closest('.chatbot-bubble')) {
        panel.classList.remove('open');
      }
    }
  });

  // Enter key in input
  document.body.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && e.target.classList.contains('chatbot-input')) {
      e.preventDefault();
      _sendMessage();
    }
  });

  _initialized = true;
}

// ── Greet ─────────────────────────────────────────────────
function _greetUser() {
  const user = _getUser();
  const name = user?.full_name ? `, ${user.full_name.split(' ')[0]}` : '';
  _addBotMessage(`👋 Hi${name}! I'm **ScamGuard AI** — your personal job safety assistant.\n\nI can help you spot fake jobs, explain analysis results, or guide you through ScamShield. What's on your mind?`);
  _renderChips(QUICK_CHIPS);
}

// ── Send ──────────────────────────────────────────────────
async function _sendMessage() {
  const input = document.querySelector('.chatbot-input');
  const text  = input?.value?.trim();
  if (!text || _isTyping) return;

  input.value = '';
  _clearChips();
  _addUserMessage(text);
  _chatHistory.push({ role: 'user', content: text });

  _isTyping = true;
  const typingEl = _addTyping();

  try {
    const reply = await _callAPI(_chatHistory.slice(-12));
    typingEl.remove();
    _addBotMessage(reply);
    _chatHistory.push({ role: 'assistant', content: reply });
    if (reply.length < 250) setTimeout(() => _renderChips(QUICK_CHIPS.slice(0, 4)), 350);
  } catch {
    typingEl.remove();
    const fallback = _fallback(text);
    _addBotMessage(fallback);
    _chatHistory.push({ role: 'assistant', content: fallback });
  }

  _isTyping = false;
}

// ── Anthropic API call ─────────────────────────────────────
// Routes through your FastAPI /api/chat endpoint (key stays server-side).
// To test locally without backend: uncomment Option A below and paste key.
async function _callAPI(messages) {

  // ── Option A: Direct browser call (dev/demo only — key visible in source) ──
  // Uncomment and set your key to test without running the backend:
  //
  // const ANTHROPIC_KEY = 'sk-ant-api03-YOUR-KEY-HERE';
  // const res = await fetch('https://api.anthropic.com/v1/messages', {
  //   method: 'POST',
  //   headers: {
  //     'Content-Type': 'application/json',
  //     'x-api-key': ANTHROPIC_KEY,
  //     'anthropic-version': '2023-06-01',
  //     'anthropic-dangerous-direct-browser-access': 'true'
  //   },
  //   body: JSON.stringify({
  //     model: 'claude-sonnet-4-20250514',
  //     max_tokens: 400,
  //     system: CHATBOT_SYSTEM_PROMPT,
  //     messages
  //   })
  // });
  // const data = await res.json();
  // if (!res.ok) throw new Error(data?.error?.message || 'API error');
  // return data?.content?.[0]?.text || _fallback('');

  // ── Option B: Via FastAPI backend /api/chat (production — key stays safe) ──
  const BASE = typeof BASE_URL !== 'undefined' ? BASE_URL : 'http://localhost:8000';
  const token = localStorage.getItem('ss_token');

  const res = await fetch(`${BASE}/api/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    },
    body: JSON.stringify({
      messages,
      system: CHATBOT_SYSTEM_PROMPT,
      max_tokens: 400
    })
  });

  if (!res.ok) throw new Error(`API ${res.status}`);
  const data = await res.json();
  return data?.reply || data?.content || _fallback('');
}

// ── Offline fallback (no API key / backend down) ─────────
function _fallback(msg) {
  const m = (msg || '').toLowerCase();

  if (/fee|deposit|pay|registration|charges|money|kit/.test(m))
    return "🚨 **Registration fees are always a scam.** No legitimate employer charges candidates for joining, training, ID cards, or background checks. Block the recruiter and **[report it here](report.html)**.";

  if (/trust card|score|result|risk score|analyzed|what.*mean/.test(m))
    return "📊 Your **Trust Card** shows a 0–100 risk score. Above 70 = very likely a scam. Scores break down by domain age, recruiter email, keywords, salary, and community reports. Use **Share** to warn friends on WhatsApp instantly.";

  if (/compare|two.*job|vs |versus|side.*side/.test(m))
    return "⚖️ Open **[Compare Jobs](compare.html)**, paste the suspicious URL on the left and the official company careers URL on the right. ScamShield compares every signal side-by-side with an AI summary.";

  if (/whatsapp|telegram|phone.*only|only.*phone|no.*email/.test(m))
    return "⚠️ **WhatsApp/Telegram-only recruitment is a red flag.** Real HR always has an official company email domain. If there's no @company.com email, verify the recruiter directly on the company's official website first.";

  if (/offer letter|pdf|docx/.test(m))
    return "📄 Use the **Offer Letter tab** on the home page analyzer. Upload your PDF or DOCX and we scan it for fee demands, suspicious contacts, and unrealistic salaries.";

  if (/report|complain|submit|found scam|got scammed/.test(m))
    return "📢 Go to **[Report Scam](report.html)**. Enter company name, scam type, description, and attach any proof. Your report gets reviewed and published to the community to protect others.";

  if (/community|other people|others report|real experience/.test(m))
    return "👥 Visit **[Community](community.html)** for real reports from job seekers across India. Search by company, domain, or scam type. You can upvote, comment, and share posts.";

  if (/gmail|yahoo|hotmail|personal email|free email/.test(m))
    return "📧 **Gmail/Yahoo HR emails are a red flag.** Legitimate companies always use company-domain emails like hr@tcs.com. If a recruiter contacts you from a free email, verify them via the company's official contact page.";

  if (/salary|pay high|unrealistic|too good|lpa|lakhs/.test(m))
    return "💰 **Unrealistic salary is a classic scam tactic.** Cross-check offers on Glassdoor or LinkedIn Salary. Freshers offered ₹8–15 LPA with 'no experience required' is almost always fake.";

  if (/domain|website|ssl|certificate|new.*website/.test(m))
    return "🌐 Paste the job URL into the **analyzer on the home page**. We automatically check domain age (under 90 days = red flag), SSL status, WHOIS, and blacklist status.";

  if (/hello|hi |hey |namaste|good morning|good afternoon|hii/.test(m))
    return "👋 Hi there! I'm **ScamGuard AI**. Describe any job offer and I'll assess it, or ask me how to use any ScamShield feature. What's on your mind?";

  if (/help|what can|features|how.*work|what.*do/.test(m))
    return "Here's what I can help with:\n\n• **Spot fake jobs** — describe any offer, I'll assess it\n• **Trust Card** — explain your risk score\n• **Compare URLs** — guide you to comparison tool\n• **Report scams** — walk through the process\n• **Any ScamShield feature** — just ask";

  return "I can help you **spot fake jobs**, **understand analysis results**, or **navigate ScamShield**. Could you share more details — like the job title, company name, or what seems suspicious?";
}

// ── DOM helpers ───────────────────────────────────────────
function _addBotMessage(text) {
  const msgs = document.querySelector('.chatbot-msgs');
  if (!msgs) return;
  const d = document.createElement('div');
  d.className = 'chatbot-msg bot';
  d.innerHTML = _fmt(text);
  msgs.appendChild(d);
  msgs.scrollTop = msgs.scrollHeight;
  return d;
}

function _addUserMessage(text) {
  const msgs = document.querySelector('.chatbot-msgs');
  if (!msgs) return;
  const d = document.createElement('div');
  d.className = 'chatbot-msg user';
  d.textContent = text;
  msgs.appendChild(d);
  msgs.scrollTop = msgs.scrollHeight;
}

function _addTyping() {
  const msgs = document.querySelector('.chatbot-msgs');
  if (!msgs) return document.createElement('div');
  const d = document.createElement('div');
  d.className = 'chatbot-msg bot';
  d.innerHTML = `<span style="display:inline-flex;gap:3px;align-items:center;padding:2px 0">
    <span class="tdot"></span><span class="tdot"></span><span class="tdot"></span>
  </span>`;
  msgs.appendChild(d);
  msgs.scrollTop = msgs.scrollHeight;
  return d;
}

function _renderChips(items) {
  const chips = document.querySelector('.chatbot-chips');
  if (!chips) return;
  chips.innerHTML = '';
  items.forEach(item => {
    const b = document.createElement('button');
    b.className = 'chatbot-chip';
    b.textContent = item;
    chips.appendChild(b);
  });
}

function _clearChips() {
  const c = document.querySelector('.chatbot-chips');
  if (c) c.innerHTML = '';
}

// ── Markdown formatter ────────────────────────────────────
function _fmt(text) {
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g,
      '<a href="$2" style="color:var(--accent-blue);text-decoration:underline;font-weight:600">$1</a>')
    .replace(/^[•\-]\s+(.+)$/gm,
      '<div style="display:flex;gap:6px;margin:3px 0"><span style="color:var(--accent-blue);flex-shrink:0;margin-top:1px">•</span><span>$1</span></div>')
    .replace(/\n\n/g, '<br><br>')
    .replace(/\n/g, '<br>');
}

function _getUser() {
  try { return JSON.parse(localStorage.getItem('ss_user') || 'null'); }
  catch { return null; }
}

// ── Public helpers ────────────────────────────────────────
function openChatbotWith(message) {
  _ensureChatbotHTML();
  const panel = document.querySelector('.chatbot-panel');
  const input = document.querySelector('.chatbot-input');
  if (!panel || !input) return;
  panel.classList.add('open');
  if (_chatHistory.length === 0) _greetUser();
  setTimeout(() => { input.value = message; _sendMessage(); }, 350);
}

function resetChatbot() {
  _chatHistory = [];
  _isTyping = false;
  const msgs = document.querySelector('.chatbot-msgs');
  if (msgs) msgs.innerHTML = '';
  _clearChips();
}

// ── Inject typing animation CSS ───────────────────────────
(function injectCSS() {
  if (document.getElementById('chatbot-keyframes')) return;
  const s = document.createElement('style');
  s.id = 'chatbot-keyframes';
  s.textContent = `
    @keyframes tdot { 0%,80%,100%{transform:scale(.6);opacity:.4} 40%{transform:scale(1);opacity:1} }
    .tdot { width:7px;height:7px;border-radius:50%;background:var(--text-muted,#8b949e);display:inline-block;animation:tdot .9s ease-in-out infinite; }
    .tdot:nth-child(2){animation-delay:.2s}
    .tdot:nth-child(3){animation-delay:.4s}
    .chatbot-chips { display:flex;flex-wrap:wrap;gap:5px;padding:0 10px 8px;min-height:0; }
    .chatbot-chip {
      background:var(--bg-input,#21262d);
      border:1px solid var(--border,#30363d);
      border-radius:99px;
      padding:4px 10px;
      font-size:11.5px;
      cursor:pointer;
      color:var(--text-secondary,#8b949e);
      transition:all .15s;
      font-family:inherit;
    }
    .chatbot-chip:hover { border-color:var(--accent-blue,#58a6ff);color:var(--accent-blue,#58a6ff); }
  `;
  document.head.appendChild(s);
})();

// ── Boot ──────────────────────────────────────────────────
// Called on DOMContentLoaded — also called by nav.js after injecting HTML
document.addEventListener('DOMContentLoaded', initChatbot);

// Export so nav.js can call it after injecting HTML
window.initChatbot = initChatbot;
