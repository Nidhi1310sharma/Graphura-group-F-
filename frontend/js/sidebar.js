// ============================================================
// sidebar.js – ScamShield v5 Sidebar & Topbar Renderer
// Renders navigation sidebar + topbar on every page
// Supports: user panel, admin panel, chatbot bubble
// ============================================================

function renderSidebar(activeLink, isAdmin) {
  const user = (() => { try { return JSON.parse(localStorage.getItem('ss_user') || 'null'); } catch { return null; } })();
  const avatarContent = user?.avatar
    ? `<img src="${user.avatar}" alt="${user.full_name}">`
    : (user?.full_name?.[0] || 'G').toUpperCase();

  // ── USER SIDEBAR LINKS ──
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

  // ── ADMIN SIDEBAR LINKS ──
  const adminLinks = `
    <li><a href="admin.html"><span class="nav-icon">📊</span> Dashboard</a></li>
    <li><a href="admin-users.html"><span class="nav-icon">👥</span> Users</a></li>
    <li><a href="admin-reports.html"><span class="nav-icon">🚩</span> Reports <span class="nav-badge">67</span></a></li>
    <li><a href="admin-jobs.html"><span class="nav-icon">💼</span> Job Database</a></li>
    <li><a href="admin-analytics.html"><span class="nav-icon">📈</span> Analytics</a></li>
    <li><a href="admin-domains.html"><span class="nav-icon">🌐</span> Blacklist</a></li>
    <li><a href="admin-ml.html"><span class="nav-icon">🤖</span> ML Settings</a></li>`;

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
    <div class="sidebar-section-label">Administration</div>
    <ul class="sidebar-nav">${adminLinks}</ul>
  </div>
  <div class="sidebar-section" style="margin-top:auto">
    <ul class="sidebar-nav">
      <li><a href="index.html" onclick="auth.logout();return false;"><span class="nav-icon">🚪</span> Logout</a></li>
    </ul>
  </div>` : `
  <div class="sidebar-section">
    <div class="sidebar-section-label">Tools</div>
    <ul class="sidebar-nav">${userToolsLinks}</ul>
  </div>
  <div class="sidebar-section">
    <div class="sidebar-section-label">Community</div>
    <ul class="sidebar-nav">${userCommunityLinks}</ul>
  </div>
  <div class="sidebar-section">
    <div class="sidebar-section-label">Account</div>
    <ul class="sidebar-nav">${userAccountLinks}</ul>
  </div>`}
  <div class="sidebar-footer">
    <button class="theme-toggle" onclick="toggleTheme()">
      <span class="theme-toggle-icon">☀️</span>
      <span class="theme-toggle-text">Light Mode</span>
    </button>
  </div>
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
      <span class="topbar-user-role">${user?.role === 'admin' ? '🔐 Administrator' : (user ? '👤 Member' : 'Not signed in')}</span>
    </div>
  </div>
  ${user ? `<button class="btn btn-ghost btn-sm" onclick="auth.logout()">Sign out</button>` : ''}
</header>`;

  const target = document.getElementById('app-shell') || document.body;
  const existing = target.querySelector('.sidebar');
  if (!existing) target.insertAdjacentHTML('afterbegin', sidebarHTML);
  const existingTop = target.querySelector('.topbar');
  if (!existingTop) {
    const mc = target.querySelector('.main-content');
    if (mc) mc.insertAdjacentHTML('afterbegin', topbarHTML);
  }

  // Set active link
  const cur = window.location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.sidebar-nav a').forEach(a => {
    if (a.getAttribute('href') === cur) a.classList.add('active');
  });

  // Inject chatbot
  const chatbot = `
<div class="chatbot-bubble" title="Ask ScamGuard AI">🤖</div>
<div class="chatbot-panel">
  <div class="chatbot-header">
    <div class="chatbot-avatar">🛡️</div>
    <div>
      <div class="chatbot-name">ScamGuard AI</div>
      <div class="chatbot-status">● Online</div>
    </div>
    <button class="chatbot-close">✕</button>
  </div>
  <div class="chatbot-msgs"></div>
  <div class="chatbot-input-row">
    <input class="chatbot-input" placeholder="Ask about scam detection…"/>
    <button class="chatbot-send">➤</button>
  </div>
</div>`;
  if (!document.querySelector('.chatbot-bubble')) document.body.insertAdjacentHTML('beforeend', chatbot);
}
