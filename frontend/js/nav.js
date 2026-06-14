//
// ============================================================
// nav.js – Top Navbar renderer (replaces sidebar.js for public pages)
// ScamShield uses a top navbar, NOT a sidebar
// The homepage IS the analyzer — VirusTotal style
// ============================================================

function renderNavbar() {
  const user = (() => { try { return JSON.parse(localStorage.getItem('ss_user') || 'null'); } catch { return null; } })();
  const isAdmin = user?.role === 'admin';
  const cur = window.location.pathname.split('/').pop() || 'index.html';

  const navHTML = `
<nav class="top-navbar">
  <div class="navbar-inner">
    <!-- Brand -->
    <a href="index.html" class="navbar-brand">
      <span class="navbar-brand-icon">🛡️</span>
      <span class="navbar-brand-name">ScamShield</span>
    </a>

    <!-- Center: Search -->
    <div class="navbar-search">
      <form onsubmit="doNavSearch(event)">
        <div class="nav-search-wrap">
          <span class="nav-search-icon">🔍</span>
          <input type="text" id="nav-search-input" class="nav-search-input" placeholder="Search posts, companies, domains…" autocomplete="off">
        </div>
      </form>
    </div>

    <!-- Right actions -->
    <div class="navbar-actions">
      ${!user ? `
        <a href="community.html" class="navbar-link ${cur==='community.html'?'active':''}">Community</a>
        <a href="report.html" class="btn btn-outline btn-sm">Report Scam</a>
        <button class="theme-toggle icon-only" onclick="toggleTheme()" title="Toggle theme">
          <span class="theme-toggle-icon">☀️</span>
        </button>
        <a href="login.html" class="btn btn-ghost btn-sm">Login</a>
        <a href="register.html" class="btn btn-primary btn-sm">Sign Up</a>
      ` : isAdmin ? `
        <a href="admin.html" class="btn btn-primary btn-sm">⚡ Admin Panel</a>
        <button class="theme-toggle icon-only" onclick="toggleTheme()" title="Toggle theme"><span class="theme-toggle-icon">☀️</span></button>
        <div class="navbar-avatar" onclick="auth.logout()" title="Sign out">
          <span>${(user.full_name||'A')[0].toUpperCase()}</span>
        </div>
      ` : `
        <a href="index.html" class="navbar-link ${cur==='index.html'?'active':''}">Home</a>
        <a href="community.html" class="navbar-link ${cur==='community.html'?'active':''}">Community</a>
        <a href="report.html" class="navbar-link ${cur==='report.html'?'active':''}">Report Scam</a>
        <button class="btn btn-outline btn-sm" onclick="openPostModal()">+ Create Post</button>
        <button class="theme-toggle icon-only" onclick="toggleTheme()" title="Toggle theme"><span class="theme-toggle-icon">☀️</span></button>
        <div class="navbar-avatar" onclick="window.location.href='profile.html'" title="${user.full_name}">
          ${user.avatar_url ? `<img src="${user.avatar_url}" alt="${user.full_name}">` : `<span>${(user.full_name||'U')[0].toUpperCase()}</span>`}
        </div>
      `}
    </div>

    <button class="navbar-hamburger" onclick="toggleMobileNav()" aria-label="Menu">☰</button>
  </div>

  <!-- Mobile dropdown -->
  <div class="navbar-mobile" id="navbar-mobile">
    <a href="index.html">Home</a>
    <a href="community.html">Community</a>
    <a href="report.html">Report Scam</a>
    ${user ? `<a href="profile.html">Profile</a><a href="#" onclick="auth.logout()">Sign Out</a>` : `<a href="login.html">Login</a><a href="register.html">Sign Up</a>`}
  </div>
</nav>`;

  document.body.insertAdjacentHTML('afterbegin', navHTML);
  document.body.style.paddingTop = 'var(--navbar-h)';

  // Chatbot bubble
  if (!document.querySelector('.chatbot-bubble')) {
    document.body.insertAdjacentHTML('beforeend', `
      <div class="chatbot-bubble" title="Ask ScamGuard AI">🤖</div>
      <div class="chatbot-panel">
        <div class="chatbot-header">
          <div class="chatbot-avatar">🛡️</div>
          <div><div class="chatbot-name">ScamGuard AI</div><div class="chatbot-status">● Online</div></div>
          <button class="chatbot-close">✕</button>
        </div>
        <div class="chatbot-msgs"></div>
        <div class="chatbot-input-row">
          <input class="chatbot-input" placeholder="Ask about scam detection…"/>
          <button class="chatbot-send">➤</button>
        </div>
      </div>`);
  }
  updateThemeBtn(localStorage.getItem('ss_theme') || 'dark');
}

function doNavSearch(e) {
  e.preventDefault();
  const q = document.getElementById('nav-search-input').value.trim();
  if (!q) return;
  window.location.href = `community.html?search=${encodeURIComponent(q)}`;
}

function toggleMobileNav() {
  document.getElementById('navbar-mobile').classList.toggle('open');
}

function openPostModal() {
  // Show quick-post modal or redirect
  if (window.location.pathname.includes('community')) {
    document.querySelector('#post-modal')?.classList.add('open');
  } else {
    window.location.href = 'community.html?compose=1';
  }
}

// Admin sidebar renderer — for admin pages only
function renderAdminSidebar(activePage) {
  const user = (() => { try { return JSON.parse(localStorage.getItem('ss_user') || 'null'); } catch { return null; } })();
  const sidebarHTML = `
<div class="admin-layout">
  <aside class="admin-sidebar">
    <a href="admin.html" class="sidebar-brand">
      <span class="sidebar-logo">🛡️</span>
      <div><span class="brand-name">ScamShield</span><span class="brand-sub">Admin Panel</span></div>
    </a>
    <nav class="admin-nav">
      <a href="admin.html" class="${activePage==='overview'?'active':''}"><span>📊</span> Overview</a>
      <a href="admin-reports.html" class="${activePage==='reports'?'active':''}"><span>🚩</span> Reports <span class="nav-badge" id="pending-badge">67</span></a>
      <a href="admin-community.html" class="${activePage==='community'?'active':''}"><span>👥</span> Community</a>
      <a href="admin-listings.html" class="${activePage==='listings'?'active':''}"><span>💼</span> Listings</a>
      <div class="admin-nav-group">Knowledge Base</div>
      <a href="admin-companies.html" class="${activePage==='companies'?'active':''}"><span>🏢</span> Companies</a>
      <a href="admin-domains.html" class="${activePage==='domains'?'active':''}"><span>🌐</span> Domains</a>
      <a href="admin-indicators.html" class="${activePage==='indicators'?'active':''}"><span>⚡</span> Scam Indicators</a>
      <div class="admin-nav-group">System</div>
      <a href="admin-users.html" class="${activePage==='admins'?'active':''}"><span>👤</span> Admins & Logs</a>
    </nav>
    <div class="admin-sidebar-footer">
      <div class="admin-sidebar-user">
        <div class="admin-sidebar-avatar">${(user?.full_name||'A')[0].toUpperCase()}</div>
        <div>
          <div style="font-weight:600;font-size:13px">${user?.full_name||'Admin'}</div>
          <div style="font-size:11px;color:var(--text-muted)">Administrator</div>
        </div>
      </div>
      <div style="display:flex;gap:8px;margin-top:10px">
        <button class="theme-toggle" onclick="toggleTheme()" style="flex:1"><span class="theme-toggle-icon">☀️</span><span class="theme-toggle-text">Light</span></button>
        <button class="btn btn-ghost btn-sm" onclick="auth.logout()">Sign out</button>
      </div>
    </div>
  </aside>
  <div class="admin-main" id="admin-main"></div>
</div>`;

  // Insert before body content
  document.body.innerHTML = sidebarHTML + '<script>document.getElementById("admin-main").appendChild(document.querySelector(".page-inner") || document.createElement("div"));<\/script>';
}
