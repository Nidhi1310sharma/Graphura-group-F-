// ============================================================
// sidebar.js – ScamShield Sidebar & Topbar Renderer
// ============================================================

function renderSidebar(activeLink, isAdmin) {
  const user = (() => { try { return JSON.parse(localStorage.getItem('gr_user') || 'null'); } catch { return null; } })();
  const avatarContent = user?.avatar
    ? `<img src="${user.avatar}" alt="${user.full_name}">`
    : (user?.full_name?.[0] || 'G').toUpperCase();
    
  const savedTheme = localStorage.getItem('gr_theme') || 'dark';

  // ADMIN SIDEBAR LINKS - Only 4 sections
  const adminLinks = `
    <li><a href="admin.html" class="${activeLink === 'admin.html' ? 'active' : ''}"><span class="nav-icon">📊</span> Dashboard</a></li>
    <li><a href="admin-reports.html" class="${activeLink === 'admin-reports.html' ? 'active' : ''}"><span class="nav-icon">🚩</span> Reports <span class="nav-badge">67</span></a></li>
    <li><a href="admin-community.html" class="${activeLink === 'admin-community.html' ? 'active' : ''}"><span class="nav-icon">👥</span> Community</a></li>
    <li><a href="admin-users.html" class="${activeLink === 'admin-users.html' ? 'active' : ''}"><span class="nav-icon">👤</span> Users</a></li>`;

  const sidebarHTML = `
<aside class="sidebar admin-sidebar" data-theme="${savedTheme}">
  <div class="sidebar-brand">
    <div class="sidebar-logo">🛡️</div>
    <div class="sidebar-brand-text">
      <span class="brand-name">ScamShield</span>
      <span class="brand-sub">Admin Panel</span>
    </div>
  </div>
  <div class="sidebar-section">
    <div class="sidebar-section-label">ADMINISTRATION</div>
    <ul class="sidebar-nav">${adminLinks}</ul>
  </div>
  <div class="sidebar-footer">
    <button class="theme-toggle" onclick="toggleTheme()">
      <span class="theme-toggle-icon">${savedTheme === 'dark' ? '☀️' : '🌙'}</span>
      <span class="theme-toggle-text">${savedTheme === 'dark' ? 'Light Mode' : 'Dark Mode'}</span>
    </button>
  </div>
</aside>`;

  const topbarHTML = `
<header class="topbar" data-theme="${savedTheme}">
  <button class="sidebar-toggle" onclick="document.querySelector('.sidebar').classList.toggle('open')">☰</button>
  <span class="topbar-title" id="page-title"></span>
  <div class="topbar-spacer"></div>
  ${user ? `<div class="alert-chip" onclick="window.location.href='my-reports.html'">🔔 <span>3 alerts</span></div>` : ''}
  <div class="topbar-user" onclick="window.location.href='${isAdmin ? 'admin.html' : (user ? 'profile.html' : 'login.html')}'">
    <div class="user-avatar">${avatarContent}</div>
    <div class="topbar-user-info">
      <span class="topbar-user-name">${user?.full_name || (user ? 'User' : 'Guest')}</span>
      <span class="topbar-user-role">${user?.role === 'admin' ? 'Administrator' : (user ? 'Member' : 'Not signed in')}</span>
    </div>
  </div>
  ${isAdmin ? `<button class="signout-btn" onclick="handleTopbarLogout()">Sign out</button>` : ''}
</header>`;

  const target = document.getElementById('app-shell') || document.body;
  const existingSidebar = target.querySelector('.sidebar');
  if (!existingSidebar) target.insertAdjacentHTML('afterbegin', sidebarHTML);
  const existingTopbar = target.querySelector('.topbar');
  if (!existingTopbar) {
    const mc = target.querySelector('.main-content');
    if (mc) mc.insertAdjacentHTML('afterbegin', topbarHTML);
  }

  // Inject chatbot
  if (!document.querySelector('.chatbot-bubble')) {
    document.body.insertAdjacentHTML('beforeend', `
<div class="chatbot-bubble" title="Ask ScamShield AI">🤖</div>
<div class="chatbot-panel">
  <div class="chatbot-header">
    <div class="chatbot-avatar">🛡️</div>
    <div><div class="chatbot-name">ScamShield AI</div><div class="chatbot-status">Online</div></div>
    <button class="chatbot-close">✕</button>
  </div>
  <div class="chatbot-msgs"></div>
  <div class="chatbot-input-row">
    <input class="chatbot-input" placeholder="Ask about scam detection…"/>
    <button class="chatbot-send">Send</button>
  </div>
</div>`);
  }
  setTimeout(() => { if (typeof initChatbot === 'function') initChatbot(); }, 100);
}

function handleTopbarLogout() {
  localStorage.removeItem('gr_user');
  localStorage.removeItem('token');
  localStorage.removeItem('gr_theme');
  window.location.href = 'login.html';
}

window.toggleTheme = function() {
  const html = document.documentElement;
  const current = html.getAttribute('data-theme') || 'dark';
  const newTheme = current === 'dark' ? 'light' : 'dark';
  
  html.setAttribute('data-theme', newTheme);
  localStorage.setItem('gr_theme', newTheme);
  
  // Update all elements with data-theme
  document.querySelectorAll('[data-theme]').forEach(el => {
    el.setAttribute('data-theme', newTheme);
  });
  
  // Update theme buttons
  const themeBtns = document.querySelectorAll('.theme-toggle');
  themeBtns.forEach(btn => {
    const iconSpan = btn.querySelector('.theme-toggle-icon');
    const textSpan = btn.querySelector('.theme-toggle-text');
    if (iconSpan) iconSpan.textContent = newTheme === 'dark' ? '☀️' : '🌙';
    if (textSpan) textSpan.textContent = newTheme === 'dark' ? 'Light Mode' : 'Dark Mode';
  });
};

(function initTheme() {
  const saved = localStorage.getItem('gr_theme') || 'dark';
  document.documentElement.setAttribute('data-theme', saved);
})();