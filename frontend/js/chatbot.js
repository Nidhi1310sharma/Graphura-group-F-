// ============================================================
// chatbot.js – ScamShield AI Chatbot (Claude-powered)
// Uses Anthropic API for real AI responses
// Fallback to keyword matching if API unavailable
// ============================================================

// Local keyword responses (instant fallback)
const BOT_KB = {
  greet: ["Hi! I'm ScamShield AI 🛡️ — your job scam assistant. Ask me anything about spotting fake jobs, or paste a job description for quick analysis!", "Hello! How can I help you stay safe from job scams today?"],
  scam_signs: `🚨 **Top Signs of a Fake Job:**\n• Registration/security deposit fee asked\n• Unrealistic salary (₹8-10LPA for freshers)\n• Recruiter uses Gmail/Yahoo instead of company email\n• WhatsApp-only communication\n• No company website or very new domain\n• Domain registered < 90 days ago\n• Immediate joining, no proper interview process`,
  how_it_works: `🔬 **How Our Detection Works:**\n1. NLP scans for 50+ fraud keywords\n2. Domain age & SSL certificate check\n3. Recruiter email domain verification\n4. Salary anomaly detection (vs industry data)\n5. Rule-based + ML hybrid scoring (0-100)`,
  tips: `💡 **Safety Tips:**\n• Never pay any fee for a job — it's always a scam\n• Verify company on LinkedIn & official website\n• Check salary on Glassdoor / AmbitionBox\n• Real HRs always use official company email domains\n• Trust your instincts — if it's too good, it's fake`,
  report: `📢 **To Report a Scam:**\nGo to the **Scam Reports** section in the sidebar.\nYou can submit the company name, job description, and upload proof (screenshot, email, offer letter). Your report helps protect others!`,
  community: `👥 **Community Reports:**\nCheck the **Community Feed** to see what other job seekers have flagged. You can upvote reports, reply, and share your own experience. Use **Search** to find reports about specific companies.`,
  domain: `🌐 **Domain Red Flags:**\n• Domain age < 90 days = very suspicious\n• No SSL certificate = high risk\n• WHOIS privacy hidden = yellow flag\n• Gmail/Yahoo recruiter email = red flag\n• Typosquatting (tcs-careers.xyz vs tcs.com)`,
  default: ["I can help you with: spotting fake jobs, how our tools work, safety tips, reporting scams, or community reports. What do you need?", "Try asking: 'What are signs of a fake job?' or 'How do I check if a domain is fake?'"],
};

function matchLocal(msg) {
  const m = msg.toLowerCase();
  if (/hello|hi|hey|namaste|helo/.test(m)) return rand(BOT_KB.greet);
  if (/sign|fake|spot|detect|how.*(know|tell)|red flag/.test(m)) return BOT_KB.scam_signs;
  if (/how.*(work|detect|analyz|engine|model|ml|nlp|pipeline)/.test(m)) return BOT_KB.how_it_works;
  if (/tip|safe|protect|avoid|prevent/.test(m)) return BOT_KB.tips;
  if (/report|complain|submit/.test(m)) return BOT_KB.report;
  if (/community|feed|post|share/.test(m)) return BOT_KB.community;
  if (/domain|ssl|whois|website/.test(m)) return BOT_KB.domain;
  if (/fee|registr|deposit|pay/.test(m)) return "🚨 **Registration Fee = Always a Scam!**\nNo legitimate company ever charges candidates for joining. Report immediately if you see this red flag!";
  if (/salary|pay|earn|lpa/.test(m)) return "💰 **Salary Red Flags:**\nFresher role with ₹8-10LPA 'no experience needed' = almost certainly fake. Check AmbitionBox or Glassdoor for realistic salary ranges.";
  if (/compare|comparison|vs|versus/.test(m)) return "⚖️ Use the **Compare Jobs** feature to paste two URLs side-by-side. It shows every signal — domain age, SSL, salary, recruiter email — in a visual diff so fakes are instantly obvious.";
  if (/trust card|report card|share/.test(m)) return "📋 The **Job Trust Card** is generated after every analysis. It has a unique report ID, risk score, and per-dimension breakdown. You can download it as an image and share on WhatsApp to warn others!";
  return null;
}

function rand(arr) { return arr[Math.floor(Math.random() * arr.length)]; }

// ── Anthropic API call ──
async function callClaudeAPI(userMessage, conversationHistory) {
  const systemPrompt = `You are ScamShield AI, the intelligent assistant for ScamShield — an Indian job scam detection platform.
You help users identify fake job postings, understand scam signals, and stay safe.

Key facts about ScamShield:
- Detects fake jobs using ML/NLP scoring (0-100 risk score)
- Checks domain age, SSL, recruiter email, salary anomalies, keywords
- Has tools: Analyze Job, Verify Recruiter, Domain Scanner, Compare Jobs, Live Scam Feed, Job Trust Card
- Community feed where users share scam reports
- Common scams in India: registration fee demand, fake WFH jobs, TCS/Infosys impersonation, data entry scams

Be helpful, concise, and friendly. Focus on job safety in India. Use emojis appropriately.
If asked about a specific job/company, give guidance on red flags to check.
Keep responses under 200 words unless the user needs detailed analysis.`;

  const messages = [
    ...conversationHistory.slice(-6),
    { role: "user", content: userMessage }
  ];

  const response = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: "claude-sonnet-4-6",
      max_tokens: 400,
      system: systemPrompt,
      messages: messages,
    })
  });

  const data = await response.json();
  if (data.content && data.content[0]?.text) {
    return data.content[0].text;
  }
  throw new Error("No response from AI");
}

// ── Inject chatbot HTML into DOM ──
function injectChatbotHTML() {
  if (document.querySelector('.chatbot-bubble')) return; // already injected
  document.body.insertAdjacentHTML('beforeend', `
<div class="chatbot-bubble" id="chatbotBubble" title="Ask ScamShield AI">🤖</div>
<div class="chatbot-panel" id="chatbotPanel">
  <div class="chatbot-header">
    <div class="chatbot-avatar">🛡️</div>
    <div>
      <div class="chatbot-name">ScamShield AI</div>
      <div class="chatbot-status">Online</div>
    </div>
    <button class="chatbot-close" id="chatbotClose">✕</button>
  </div>
  <div class="chatbot-msgs" id="chatbotMsgs"></div>
  <div class="chatbot-input-row">
    <input class="chatbot-input" id="chatbotInput" placeholder="Ask about scam detection…"/>
    <button class="chatbot-send" id="chatbotSend">Send</button>
  </div>
</div>`);
}

// ── Main init — safe to call multiple times, only binds once ──
function initChatbot() {
  // Guard: prevent double-binding
  if (window._chatbotReady) return;

  // Inject HTML if not already present (handles both nav.js and direct call)
  injectChatbotHTML();

  const bubble   = document.querySelector('.chatbot-bubble');
  const panel    = document.querySelector('.chatbot-panel');
  const closeBtn = document.querySelector('.chatbot-close');
  const input    = document.querySelector('.chatbot-input');
  const sendBtn  = document.querySelector('.chatbot-send');
  const msgs     = document.querySelector('.chatbot-msgs');

  // Elements must exist before we proceed
  if (!bubble || !panel || !msgs) return;

  window._chatbotReady = true;

  const conversationHistory = [];

  // ── Open / Close ──
  bubble.addEventListener('click', () => {
    panel.classList.toggle('open');
    if (panel.classList.contains('open') && msgs.children.length === 0) {
      addBotMsg(rand(BOT_KB.greet));
      setTimeout(() => addSuggestions(['Signs of fake job', 'How detection works', 'Safety tips', 'Compare two jobs', 'Report a scam']), 700);
    }
  });

  closeBtn && closeBtn.addEventListener('click', () => panel.classList.remove('open'));

  // ── Send ──
  sendBtn  && sendBtn.addEventListener('click', sendChat);
  input    && input.addEventListener('keydown', e => { if (e.key === 'Enter') sendChat(); });

  async function sendChat() {
    const text = input.value.trim();
    if (!text) return;
    addUserMsg(text);
    input.value = '';
    msgs.querySelectorAll('.chatbot-suggestions').forEach(s => s.remove());
    conversationHistory.push({ role: "user", content: text });

    // Local match = instant response
    const local = matchLocal(text);
    if (local) {
      setTimeout(() => {
        addBotMsg(local);
        conversationHistory.push({ role: "assistant", content: local });
      }, 300 + Math.random() * 200);
      return;
    }

    // Claude API
    const typing = addTypingIndicator();
    try {
      const aiResponse = await callClaudeAPI(text, conversationHistory.slice(0, -1));
      typing.remove();
      addBotMsg(aiResponse);
      conversationHistory.push({ role: "assistant", content: aiResponse });
    } catch (err) {
      typing.remove();
      const fallback = rand(BOT_KB.default);
      addBotMsg(fallback);
      conversationHistory.push({ role: "assistant", content: fallback });
    }
  }

  // ── Helpers ──
  function addTypingIndicator() {
    const d = document.createElement('div');
    d.className = 'chatbot-msg bot typing';
    d.innerHTML = '<span></span><span></span><span></span>';
    msgs.appendChild(d);
    msgs.scrollTop = msgs.scrollHeight;
    return d;
  }

  function addBotMsg(text) {
    const d = document.createElement('div');
    d.className = 'chatbot-msg bot';
    d.innerHTML = text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n/g, '<br>');
    msgs.appendChild(d);
    msgs.scrollTop = msgs.scrollHeight;
  }

  function addUserMsg(text) {
    const d = document.createElement('div');
    d.className = 'chatbot-msg user';
    d.textContent = text;
    msgs.appendChild(d);
    msgs.scrollTop = msgs.scrollHeight;
  }

  function addSuggestions(items) {
    const wrap = document.createElement('div');
    wrap.className = 'chatbot-suggestions';
    items.forEach(item => {
      const b = document.createElement('button');
      b.className = 'chatbot-suggestion';
      b.textContent = item;
      b.onclick = () => {
        addUserMsg(item);
        wrap.remove();
        conversationHistory.push({ role: "user", content: item });
        const local = matchLocal(item);
        if (local) {
          setTimeout(() => {
            addBotMsg(local);
            conversationHistory.push({ role: "assistant", content: local });
          }, 300);
        } else {
          const typing = addTypingIndicator();
          callClaudeAPI(item, conversationHistory.slice(0, -1))
            .then(r => {
              typing.remove();
              addBotMsg(r);
              conversationHistory.push({ role: "assistant", content: r });
            })
            .catch(() => {
              typing.remove();
              addBotMsg(rand(BOT_KB.default));
            });
        }
      };
      wrap.appendChild(b);
    });
    msgs.appendChild(wrap);
    msgs.scrollTop = msgs.scrollHeight;
  }
}

// ── Auto-init on DOMContentLoaded ──
// Works whether chatbot.js is loaded standalone OR via nav.js/sidebar.js
document.addEventListener('DOMContentLoaded', () => {
  // If bubble already in DOM (injected by sidebar.js before this runs), init directly
  // If not, injectChatbotHTML() inside initChatbot() will handle it
  setTimeout(initChatbot, 100);
});