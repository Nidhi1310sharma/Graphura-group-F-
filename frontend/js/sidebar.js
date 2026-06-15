// ============================================================
// sidebar.js – ScamShield Sidebar & Topbar Renderer
// Renders navigation sidebar + topbar on every page
// Supports: user panel, admin panel, chatbot bubble
// ============================================================

function renderSidebar(activeLink, isAdmin) {
  const user = (() => { try { return JSON.parse(localStorage.getItem('gr_user') || 'null'); } catch { return null; } })();
  const avatarContent = user?.avatar
    ? `<img src="${user.avatar}" alt="${user.full_name}">`
    : (user?.full_name?.[0] || 'G').toUpperCase();

  // USER SIDEBAR LINKS - without emojis
  const userToolsLinks = `
    <li><a href="checker.html"><span class="nav-icon">🔍</span> Analyze Job</a></li>
    <li><a href="recruiter.html"><span class="nav-icon">👤</span> Verify Recruiter</a></li>
    <li><a href="domain-scanner.html"><span class="nav-icon">🌐</span> Domain Scanner</a></li>`;

  const userCommunityLinks = `
    <li><a href="report.html"><span class="nav-icon">🚩</span> Report Scam <span class="nav-badge">New</span></a></li>
    <li><a href="community.html"><span class="nav-icon">👥</span> Community Feed</a></li>
    <li><a href="live-feed.html"><span class="nav-icon">📡</span> Live Scam Feed</a></li>
    <li><a href="compare.html"><span class="nav-icon">⚖️</span> Compare Jobs</a></li>`;

  const userAccountLinks = `
    <li><a href="profile.html"><span class="nav-icon">🧑‍💻</span> My Profile</a></li>
    <li><a href="my-reports.html"><span class="nav-icon">📋</span> My Reports</a></li>
    ${!user ? '<li><a href="login.html"><span class="nav-icon">🔐</span> Sign In</a></li>' : ''}`;

  // ADMIN SIDEBAR LINKS - without emojis
  const adminLinks = `
    <li><a href="admin.html" class="${activeLink === 'dashboard' ? 'active' : ''}"><span class="nav-icon">📊</span> Dashboard</a></li>
    <li><a href="admin-users.html" class="${activeLink === 'users' ? 'active' : ''}"><span class="nav-icon">👥</span> Users</a></li>
    <li><a href="admin-reports.html" class="${activeLink === 'reports' ? 'active' : ''}"><span class="nav-icon">🚩</span> Reports <span class="nav-badge">67</span></a></li>
    <li><a href="admin-jobs.html" class="${activeLink === 'jobs' ? 'active' : ''}"><span class="nav-icon">💼</span> Job Database</a></li>
    <li><a href="admin-analytics.html" class="${activeLink === 'analytics' ? 'active' : ''}"><span class="nav-icon">📈</span> Analytics</a></li>
    <li><a href="admin-domains.html" class="${activeLink === 'domains' ? 'active' : ''}"><span class="nav-icon">🌐</span> Blacklist</a></li>
    <li><a href="admin-ml.html" class="${activeLink === 'ml' ? 'active' : ''}"><span class="nav-icon">🤖</span> ML Settings</a></li>`;

  const brandHref = isAdmin ? 'admin.html' : 'checker.html';
  const sidebarClass = isAdmin ? 'sidebar admin-sidebar' : 'sidebar';

  const sidebarHTML = `
<aside class="${sidebarClass}">
  <a href="${brandHref}" class="sidebar-brand">
    <div class="sidebar-logo">🛡️</div>
    <div class="sidebar-brand-text">
      <span class="brand-name">ScamShield</span>
      <span class="brand-sub">${isAdmin ? 'Admin Panel' : 'Job Safety Platform'}</span>
    </div>
  </a>
  ${isAdmin ? `
  <div class="sidebar-section">
    <div class="sidebar-section-label">ADMINISTRATION</div>
    <ul class="sidebar-nav">${adminLinks}</ul>
  </div>
  <div class="sidebar-section logout-section">
    
  </div>
  <div class="sidebar-footer">
    <button class="theme-toggle" onclick="toggleTheme()">
      <span class="theme-toggle-icon">☀️</span>
      <span class="theme-toggle-text">Light Mode</span>
    </button>
  </div>` : `
  <div class="sidebar-section">
    <div class="sidebar-section-label">TOOLS</div>
    <ul class="sidebar-nav">${userToolsLinks}</ul>
  </div>
  <div class="sidebar-section">
    <div class="sidebar-section-label">COMMUNITY</div>
    <ul class="sidebar-nav">${userCommunityLinks}</ul>
  </div>
  <div class="sidebar-section">
    <div class="sidebar-section-label">ACCOUNT</div>
    <ul class="sidebar-nav">${userAccountLinks}</ul>
  </div>
  <div class="sidebar-footer">
    <button class="theme-toggle" onclick="toggleTheme()">
      <span class="theme-toggle-icon">☀️</span>
      <span class="theme-toggle-text">Light Mode</span>
    </button>
  </div>`}
</aside>`;

  const topbarHTML = `
<header class="topbar">
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
  ${user ? `<button class="btn btn-ghost btn-sm" onclick="handleTopbarLogout()">Sign out</button>` : ''}
</header>`;

  const target = document.getElementById('app-shell') || document.body;
  const existing = target.querySelector('.sidebar');
  if (!existing) target.insertAdjacentHTML('afterbegin', sidebarHTML);
  const existingTop = target.querySelector('.topbar');
  if (!existingTop) {
    const mc = target.querySelector('.main-content');
    if (mc) mc.insertAdjacentHTML('afterbegin', topbarHTML);
  }

  // Set active link based on current page
  const cur = window.location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.sidebar-nav a').forEach(a => {
    const href = a.getAttribute('href');
    if (href === cur) a.classList.add('active');
  });

  // Remove any duplicate logout buttons from admin sidebar footer
  if (isAdmin) {
    const logoutBtn = document.querySelector('.logout-section');
    const anyOtherLogout = document.querySelectorAll('.topbar-user + .btn-ghost, .navbar-avatar');
    anyOtherLogout.forEach(btn => {
      if (btn !== logoutBtn) btn.remove();
    });
  }

  // Inject chatbot
  const chatbot = `
<div class="chatbot-bubble" title="Ask ScamShield AI">🤖</div>
<div class="chatbot-panel">
  <div class="chatbot-header">
    <div class="chatbot-avatar">🛡️</div>
    <div>
      <div class="chatbot-name">ScamShield AI</div>
      <div class="chatbot-status">Online</div>
    </div>
    <button class="chatbot-close">✕</button>
  </div>
  <div class="chatbot-msgs"></div>
  <div class="chatbot-input-row">
    <input class="chatbot-input" placeholder="Ask about scam detection…"/>
    <button class="chatbot-send">Send</button>
  </div>
</div>`;
  if (!document.querySelector('.chatbot-bubble')) document.body.insertAdjacentHTML('beforeend', chatbot);
  
  // Initialize chatbot if function exists
  setTimeout(() => { if (typeof initChatbot === 'function') initChatbot(); }, 100);
}

// Handle sidebar logout
function handleSidebarLogout() {
  localStorage.removeItem('gr_user');
  localStorage.removeItem('token');
  localStorage.removeItem('gr_theme');
  window.location.href = 'login.html';
}

// Handle topbar logout
function handleTopbarLogout() {
  localStorage.removeItem('gr_user');
  localStorage.removeItem('token');
  localStorage.removeItem('gr_theme');
  window.location.href = 'login.html';
}

// Theme toggle function
window.toggleTheme = function() {
  const html = document.documentElement;
  const current = html.getAttribute('data-theme') || 'dark';
  const newTheme = current === 'dark' ? 'light' : 'dark';
  html.setAttribute('data-theme', newTheme);
  localStorage.setItem('gr_theme', newTheme);
  
  // Update theme button text
  const themeBtns = document.querySelectorAll('.theme-toggle');
  themeBtns.forEach(btn => {
    const iconSpan = btn.querySelector('.theme-toggle-icon');
    const textSpan = btn.querySelector('.theme-toggle-text');
    if (iconSpan) iconSpan.textContent = newTheme === 'dark' ? '☀️' : '🌙';
    if (textSpan) textSpan.textContent = newTheme === 'dark' ? 'Light Mode' : 'Dark Mode';
  });
};

// Initialize theme on load
(function initTheme() {
  const saved = localStorage.getItem('gr_theme') || 'dark';
  document.documentElement.setAttribute('data-theme', saved);
})();