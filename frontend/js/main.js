// ============================================================
// main.js – ScamShield Core Utilities
// ============================================================

const API_BASE = "https://graphura-group-f-1.onrender.com/api";

// ── API Client ──
const api = {
  async request(method, path, body = null) {
  const token = localStorage.getItem('gr_token'); 
   const opts = { method, headers: {} };
   if (token) opts.headers["Authorization"] = "Bearer " + token;

   if (body) {
        if (body instanceof FormData) {
            opts.body = body;
        } else {
            opts.headers["Content-Type"] = "application/json";
            opts.body = JSON.stringify(body);
        }
    }
    try {
        const res = await fetch(API_BASE + path, opts);
      if (!res.ok) { const err = await res.json().catch(() => ({ detail: "Server error" })); throw new Error(err.detail || `HTTP ${res.status}`); }
      return await res.json();
    } catch (e) {
      if (e.message.includes("Failed to fetch")) throw new Error("Cannot connect to server.");
      throw e;
    }
  },
  get:    p    => api.request("GET",    p),
  post:   (p,b)=> api.request("POST",   p, b),
  put:    (p,b)=> api.request("PUT",    p, b),
  delete: p    => api.request("DELETE", p),
};

// ── Theme ──
function initTheme() {
  const saved = localStorage.getItem('gr_theme') || 'dark';
  document.documentElement.setAttribute('data-theme', saved);
  // updateThemeBtn is safe to call even before nav renders – it queries DOM at call time
  updateThemeBtn(saved);
}

function toggleTheme() {
  const curr = document.documentElement.getAttribute('data-theme') || 'dark';
  const next = curr === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('gr_theme', next);
  updateThemeBtn(next);
}

function updateThemeBtn(theme) {
  const isDark = theme === 'dark';
  document.querySelectorAll('.theme-toggle').forEach(btn => {
    const icon = btn.querySelector('.theme-toggle-icon');
    const text = btn.querySelector('.theme-toggle-text');
    // icon-only buttons: just show ☀ (go light) or ☾ (go dark)
    if (icon) icon.textContent = isDark ? '☀' : '☾';
    if (text) text.textContent = isDark ? 'Light Mode' : 'Dark Mode';
    btn.title = isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode';
  });
}

// ── Auth ──
const auth = {
  getUser()    { try { return JSON.parse(localStorage.getItem('gr_user') || 'null'); } catch { return null; } },
  isLoggedIn() { return !!localStorage.getItem('gr_token'); },
  isAdmin()    { const u = this.getUser(); return u?.role === 'admin'; },
  logout() {
    localStorage.removeItem('gr_token');
    localStorage.removeItem('gr_user');
    window.location.href = 'login.html';
  },
};

// ── Guards ──
function requireAdmin() {
  const user = auth.getUser();
  if (!user || user.role !== 'admin') {
    showToast('Admin access required', 'error');
    setTimeout(() => window.location.href = 'login.html', 800);
    return false;
  }
  return true;
}

function requireUser() {
  const user = auth.getUser();
  if (user && user.role === 'admin') window.location.href = 'admin.html';
}

// ── Sidebar init (legacy sidebar pages) ──
function initSidebar() {
  const toggle  = document.querySelector('.sidebar-toggle');
  const sidebar = document.querySelector('.sidebar');
  if (toggle && sidebar) {
    toggle.addEventListener('click', () => sidebar.classList.toggle('open'));
    document.addEventListener('click', e => {
      if (sidebar.classList.contains('open') && !sidebar.contains(e.target) && !toggle.contains(e.target))
        sidebar.classList.remove('open');
    });
  }
  const cur = window.location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.sidebar-nav a').forEach(a => {
    if (a.getAttribute('href') === cur) a.classList.add('active');
  });
  const user = auth.getUser();
  if (user) {
    document.querySelectorAll('.topbar-user-name').forEach(el => el.textContent = user.full_name || 'User');
    document.querySelectorAll('.topbar-user-role').forEach(el => el.textContent = user.role === 'admin' ? '🔐 Administrator' : '👤 Member');
    document.querySelectorAll('.user-avatar').forEach(el => {
      if (user.avatar) el.innerHTML = `<img src="${user.avatar}" alt="${user.full_name}">`;
      else el.textContent = (user.full_name || 'U')[0].toUpperCase();
    });
  }
}

// ── Toast ──
const toastEl = () => {
  let c = document.querySelector('.toast-container');
  if (!c) { c = document.createElement('div'); c.className = 'toast-container'; document.body.appendChild(c); }
  return c;
};
function showToast(msg, type = "info", duration = 4000) {
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.innerHTML = msg;
  toastEl().appendChild(t);
  setTimeout(() => { t.style.opacity = '0'; t.style.transition = 'opacity 0.4s'; setTimeout(() => t.remove(), 400); }, duration);
}

// ── Modal helpers ──
function openModal(id)  { document.getElementById(id)?.classList.add('open'); }
function closeModal(id) {
  if (id) document.getElementById(id)?.classList.remove('open');
  else document.querySelectorAll('.modal-overlay.open').forEach(m => m.classList.remove('open'));
}
document.addEventListener('click', e => {
  if (e.target.classList.contains('modal-overlay'))   e.target.classList.remove('open');
  if (e.target.classList.contains('modal-close'))     e.target.closest('.modal-overlay')?.classList.remove('open');
});

// ── Risk helpers ──
function getRiskClass(r) { return { LOW:"risk-low", MEDIUM:"risk-medium", HIGH:"risk-high", CONFIRMED_SCAM:"risk-scam" }[r] || "risk-low"; }
function getRiskEmoji(r) { return { LOW:"✅", MEDIUM:"⚠️", HIGH:"❌", CONFIRMED_SCAM:"🚫" }[r] || "❓"; }
function getRiskLabel(r) { return { LOW:"Low Risk", MEDIUM:"Medium Risk", HIGH:"High Risk", CONFIRMED_SCAM:"Confirmed Scam" }[r] || "Unknown"; }

function renderScoreBar(containerId, score, riskLevel) {
  const el = document.getElementById(containerId); if (!el) return;
  const color = riskLevel === 'LOW' ? 'var(--accent-green)' : riskLevel === 'MEDIUM' ? 'var(--accent-yellow)' : 'var(--accent-red)';
  el.innerHTML = `<div style="width:100%;height:8px;background:var(--bg-input);border-radius:4px;overflow:hidden"><div style="height:100%;width:${score}%;background:${color};border-radius:4px;transition:width 1s ease"></div></div>`;
}

// ── Init ──
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initSidebar();
});
