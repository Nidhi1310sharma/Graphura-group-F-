// ============================================================
// nav.js – ScamShield Navbar
// ============================================================

// ── Auth guard ──
function requireLogin(action) {
  const user = _getUser();
  if (user) return true;
  _showLoginRequired(action);
  return false;
}

function _showLoginRequired(action) {
  document.getElementById('gr-login-overlay')?.remove();
  const el = document.createElement('div');
  el.className = 'login-required-overlay';
  el.id = 'gr-login-overlay';
  el.innerHTML = `
    <div class="login-required-card">
      <span class="login-required-icon">🔒</span>
      <div class="login-required-title">Login Required</div>
      <p class="login-required-sub">You need to be logged in to ${action}. It only takes a minute to join ScamShield free.</p>
      <div class="login-required-btns">
        <a href="login.html" class="btn btn-primary" style="flex:1;justify-content:center">Sign In</a>
        <a href="register.html" class="btn btn-outline" style="flex:1;justify-content:center">Register</a>
      </div>
      <button onclick="document.getElementById('gr-login-overlay').remove()" style="margin-top:12px;background:none;border:none;color:var(--text-muted);font-size:12px;cursor:pointer">Cancel</button>
    </div>`;
  document.body.appendChild(el);
  el.addEventListener('click', e => { if (e.target === el) el.remove(); });
}

function _getUser() {
  try { return JSON.parse(localStorage.getItem('gr_user') || 'null'); } catch { return null; }
}

// ── Shield SVG ──
function _shieldSVG(size = 28) {
  return `<svg width="${size}" height="${size}" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M16 2L4 7v9c0 7.18 5.14 13.9 12 15.93C22.86 29.9 28 23.18 28 16V7L16 2z" fill="url(#gs${size}${Math.random().toString(36).slice(2,5)})" stroke="rgba(200,217,230,0.25)" stroke-width="0.5"/>
    <path d="M11 16l3.5 3.5L21.5 12" stroke="#fff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
    <defs><linearGradient id="gs${size}${Math.random().toString(36).slice(2,5)}" x1="4" y1="2" x2="28" y2="32" gradientUnits="userSpaceOnUse">
      <stop stop-color="#567C8D"/><stop offset="1" stop-color="#2F4156"/>
    </linearGradient></defs>
  </svg>`;
}

// ── Render navbar (single navbar for all pages) ──
function renderNavbar() {
  if (document.querySelector('.top-navbar')) return;

  const user = _getUser();
  const isAdmin = user?.role === 'admin';
  const cur = window.location.pathname.split('/').pop() || 'index.html';
  const saved = localStorage.getItem('gr_theme') || 'dark';

  const nav = document.createElement('nav');
  nav.className = 'top-navbar';
  nav.innerHTML = `
  <div class="navbar-inner">
    <a href="index.html" class="navbar-brand">
      ${_shieldSVG(28)}
      <span class="navbar-brand-name">ScamShield</span>
    </a>

    <div class="navbar-search">
      <form onsubmit="doNavSearch(event)">
        <div class="nav-search-wrap">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
          <input type="text" id="nav-search-input" class="nav-search-input" placeholder="Search companies, domains, reports…" autocomplete="off">
        </div>
      </form>
    </div>

    <div class="navbar-actions">
      ${!user ? `
        <a href="community.html" class="navbar-link ${cur==='community.html'?'active':''}">Community</a>
        <a href="report.html" class="btn btn-outline btn-sm" onclick="return requireLogin('report a scam')">Report Scam</a>
        <button class="theme-toggle icon-only" onclick="toggleTheme()"><span class="theme-toggle-icon">☀</span></button>
        <a href="login.html" class="btn btn-ghost btn-sm">Login</a>
        <a href="register.html" class="btn btn-primary btn-sm">Sign Up</a>
      ` : isAdmin ? `
        <a href="admin.html" class="navbar-link ${cur==='admin.html'?'active':''}">Admin</a>
        <a href="admin-reports.html" class="navbar-link">Reports</a>
        <button class="theme-toggle icon-only" onclick="toggleTheme()"><span class="theme-toggle-icon">☀</span></button>
        <div class="navbar-avatar" onclick="openAdminProfileModal()" title="Admin Profile">
          <span>${(user.full_name||'A')[0].toUpperCase()}</span>
        </div>
        <button class="btn btn-outline btn-sm" onclick="handleLogout()" style="margin-left:8px">Sign out</button>
      ` : `
        <a href="index.html" class="navbar-link ${cur==='index.html'?'active':''}">Home</a>
        <a href="community.html" class="navbar-link ${cur==='community.html'?'active':''}">Community</a>
        <a href="report.html" class="navbar-link ${cur==='report.html'?'active':''}">Report Scam</a>
        <button class="btn btn-outline btn-sm" onclick="openPostModal()">+ Post</button>
        <button class="theme-toggle icon-only" onclick="toggleTheme()"><span class="theme-toggle-icon">☀</span></button>
        <div class="navbar-avatar" onclick="window.location.href='profile.html'" title="${user.full_name||'Profile'}">
          ${user.avatar_url ? `<img src="${user.avatar_url}" alt="${user.full_name}">` : `<span>${(user.full_name||'U')[0].toUpperCase()}</span>`}
        </div>
      `}
    </div>

    <button class="navbar-hamburger" onclick="toggleMobileNav()">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/>
      </svg>
    </button>
  </div>
  <div class="navbar-mobile" id="navbar-mobile">
    <a href="index.html">Home</a>
    <a href="community.html">Community</a>
    <a href="report.html" onclick="return requireLogin('report a scam')">Report Scam</a>
    ${user
      ? `<a href="#" onclick="handleLogout()">Sign Out</a>`
      : `<a href="login.html">Login</a><a href="register.html">Sign Up</a>`}
  </div>`;

  document.body.insertAdjacentElement('afterbegin', nav);
  updateThemeBtn(saved);
  setTimeout(() => { if (typeof initChatbot === 'function') initChatbot(); }, 60);
  _injectFooter();
}

// ── Admin Profile Modal ──
function openAdminProfileModal() {
  const user = _getUser();
  if (!user) return;
  
  document.getElementById('admin-profile-modal')?.remove();
  
  const modal = document.createElement('div');
  modal.id = 'admin-profile-modal';
  modal.className = 'admin-profile-modal';
  modal.innerHTML = `
    <div class="admin-profile-overlay" onclick="closeAdminProfileModal()"></div>
    <div class="admin-profile-card">
      <div class="admin-profile-header">
        <div class="admin-profile-avatar">${(user.full_name || 'A')[0].toUpperCase()}</div>
        <button class="admin-profile-close" onclick="closeAdminProfileModal()">✕</button>
      </div>
      <div class="admin-profile-body">
        <h3 class="admin-profile-name">${user.full_name || 'Administrator'}</h3>
        <p class="admin-profile-email">${user.email || 'admin@scamshield.com'}</p>
        <div class="admin-profile-role-badge">Administrator</div>
        
        <div class="admin-profile-stats">
          <div class="admin-profile-stat">
            <div class="stat-value">248</div>
            <div class="stat-label">Total Users</div>
          </div>
          <div class="admin-profile-stat">
            <div class="stat-value">67</div>
            <div class="stat-label">Pending Reports</div>
          </div>
          <div class="admin-profile-stat">
            <div class="stat-value">89</div>
            <div class="stat-label">Blacklisted</div>
          </div>
        </div>
        
        <div class="admin-profile-actions">
          <button class="btn btn-outline btn-full" onclick="window.location.href='admin.html'">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>
              <rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/>
            </svg>
            Dashboard
          </button>
          <button class="btn btn-primary btn-full" onclick="window.location.href='admin-reports.html'">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/>
              <line x1="4" y1="22" x2="4" y2="15"/>
            </svg>
            Review Reports
          </button>
          <button class="btn btn-danger btn-full" onclick="handleLogout()">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
              <polyline points="16 17 21 12 16 7"/>
              <line x1="21" y1="12" x2="9" y2="12"/>
            </svg>
            Sign Out
          </button>
        </div>
      </div>
    </div>
  `;
  
  document.body.appendChild(modal);
  setTimeout(() => modal.classList.add('open'), 10);
}

function closeAdminProfileModal() {
  const modal = document.getElementById('admin-profile-modal');
  if (modal) {
    modal.classList.remove('open');
    setTimeout(() => modal.remove(), 300);
  }
}

function handleLogout() {
  localStorage.removeItem('gr_user');
  localStorage.removeItem('token');
  window.location.href = 'login.html';
}

function _injectFooter() {
  if (document.querySelector('.site-footer')) return;
  if (window.location.pathname.includes('admin')) return;

  const footer = document.createElement('footer');
  footer.className = 'site-footer';
  footer.innerHTML = `
    <div class="footer-inner">
      <div class="footer-grid">
        <div>
          <div class="footer-brand-row">${_shieldSVG(30)}<span class="footer-brand-name">ScamShield</span></div>
          <p class="footer-tagline">India's first AI-powered fake job detection system. We help job seekers identify fraudulent postings before they fall victim to employment scams.</p>
        </div>
        <div>
          <div class="footer-col-title">Analyze</div>
          <ul class="footer-links">
            <li><a href="index.html">Job Analyzer (Home)</a></li>
            <li><a href="checker.html?mode=url">Check a URL</a></li>
            <li><a href="checker.html?mode=text">Paste Job Description</a></li>
            <li><a href="checker.html?mode=offer">Check Offer Letter</a></li>
            <li><a href="checker.html?mode=screenshot">Screenshot Check</a></li>
          </ul>
        </div>
        <div>
          <div class="footer-col-title">Community</div>
          <ul class="footer-links">
            <li><a href="community.html">Community Feed</a></li>
            <li><a href="community.html#live-feed">Live Scam Feed</a></li>
            <li><a href="report.html">Report a Scam</a></li>
            <li><a href="my-reports.html">My Reports</a></li>
          </ul>
        </div>
        <div>
          <div class="footer-col-title">Account</div>
          <ul class="footer-links">
            <li><a href="login.html">Sign In</a></li>
            <li><a href="register.html">Create Account</a></li>
            <li><a href="profile.html">My Profile</a></li>
            <li><a href="settings.html">Settings</a></li>
          </ul>
        </div>
      </div>
      <div class="footer-bottom">
        <span class="footer-copy">&copy; ${new Date().getFullYear()} ScamShield. Built to protect Indian job seekers.</span>
        <div class="footer-badges">
          <span class="footer-badge">AI Powered</span>
          <span class="footer-badge">Free Analyzer</span>
          <span class="footer-badge">Community Driven</span>
        </div>
      </div>
    </div>`;
  document.body.appendChild(footer);
}

function doNavSearch(e) {
  e.preventDefault();
  const q = document.getElementById('nav-search-input')?.value.trim();
  if (!q) return;
  window.location.href = `community.html?search=${encodeURIComponent(q)}`;
}

function toggleMobileNav() {
  document.getElementById('navbar-mobile')?.classList.toggle('open');
}

function openPostModal() {
  if (!requireLogin('create a post')) return;
  window.location.href = 'community.html?compose=1';
}

function updateThemeBtn(theme) {
  const btns = document.querySelectorAll('.theme-btn');
  btns.forEach(btn => {
    const iconSpan = btn.querySelector('.theme-toggle-icon');
    const textSpan = btn.querySelector('span:last-child');
    if (iconSpan) iconSpan.textContent = theme === 'dark' ? '☀' : '🌙';
    if (textSpan && !btn.closest('.admin-sidebar-actions')) textSpan.textContent = theme === 'dark' ? 'Light Mode' : 'Dark Mode';
  });
}

window.toggleTheme = function() {
  const html = document.documentElement;
  const current = html.getAttribute('data-theme') || 'dark';
  const newTheme = current === 'dark' ? 'light' : 'dark';
  html.setAttribute('data-theme', newTheme);
  localStorage.setItem('gr_theme', newTheme);
  updateThemeBtn(newTheme);
};

// ── Admin Sidebar (only for admin pages) ──
function renderAdminSidebar(activePage) {
  if (document.querySelector('.admin-layout')) return;

  const user = _getUser();
  const saved = localStorage.getItem('gr_theme') || 'dark';
  const is = k => activePage === k;

  const navItems = [
    { href: 'admin.html', key: 'overview', label: 'Dashboard',
      icon: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>` },
    { href: 'admin-reports.html', key: 'reports', label: 'Reports', badge: '67',
      icon: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><line x1="4" y1="22" x2="4" y2="15"/></svg>` },
    { href: 'admin-community.html', key: 'community', label: 'Community',
      icon: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/></svg>` },
    { href: 'admin-listings.html', key: 'listings', label: 'Job Listings',
      icon: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>` },
    { group: 'Knowledge Base' },
    { href: 'admin-companies.html', key: 'companies', label: 'Companies',
      icon: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>` },
    { href: 'admin-domains.html', key: 'domains', label: 'Blacklisted Domains',
      icon: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>` },
    { href: 'admin-indicators.html', key: 'indicators', label: 'Scam Indicators',
      icon: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>` },
    { group: 'System' },
    { href: 'admin-users.html', key: 'admins', label: 'Admins & Logs',
      icon: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>` },
  ];

  let navHTML = '';
  for (const item of navItems) {
    if (item.group) {
      navHTML += `<div class="admin-nav-group">${item.group}</div>`;
    } else {
      const badge = item.badge ? `<span class="nav-badge">${item.badge}</span>` : '';
      const activeClass = is(item.key) ? 'active' : '';
      navHTML += `<a href="${item.href}" class="${activeClass}">${item.icon} ${item.label}${badge}</a>`;
    }
  }

  const adminLayout = document.createElement('div');
  adminLayout.className = 'admin-layout';
  adminLayout.innerHTML = `
    <aside class="admin-sidebar">
      <div class="admin-sidebar-header">
        <a href="admin.html" class="admin-logo">
          ${_shieldSVG(24)}
          <div>
            <span class="admin-logo-title">ScamShield</span>
            <span class="admin-logo-sub">Admin Panel</span>
          </div>
        </a>
        <button class="admin-sidebar-close" onclick="toggleAdminSidebar()">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="15 18 9 12 15 6"/></svg>
        </button>
      </div>
      <nav class="admin-nav">${navHTML}</nav>
      <div class="admin-sidebar-footer">
        <div class="admin-sidebar-user" onclick="openAdminProfileModal()">
          <div class="admin-sidebar-avatar">${(user?.full_name || 'A')[0].toUpperCase()}</div>
          <div>
            <div class="admin-sidebar-name">${user?.full_name || 'Administrator'}</div>
            <div class="admin-sidebar-role">Administrator</div>
          </div>
        </div>
        <div class="admin-sidebar-actions">
          <button class="admin-action-btn theme-btn" onclick="toggleTheme()">
            <span class="theme-icon">${saved === 'dark' ? '☀️' : '🌙'}</span>
            <span>${saved === 'dark' ? 'Light Mode' : 'Dark Mode'}</span>
          </button>
        </div>
      </div>
    </aside>
    <main class="admin-main" id="admin-main"></main>
  `;

  const pageContent = document.querySelector('.page-inner');
  const appShell = document.querySelector('.app-shell');
  
  if (appShell) {
    appShell.innerHTML = '';
    appShell.appendChild(adminLayout);
  } else {
    document.body.innerHTML = '';
    document.body.appendChild(adminLayout);
  }

  if (pageContent) {
    const adminPage = document.createElement('div');
    adminPage.className = 'admin-page';
    adminPage.appendChild(pageContent);
    document.getElementById('admin-main').appendChild(adminPage);
  }

  document.documentElement.setAttribute('data-theme', saved);
  updateThemeBtn(saved);
  
  const sidebarState = localStorage.getItem('admin_sidebar_open');
  if (sidebarState === 'false') {
    document.querySelector('.admin-layout')?.classList.add('sidebar-closed');
  }
}

function toggleAdminSidebar() {
  const layout = document.querySelector('.admin-layout');
  if (layout) {
    layout.classList.toggle('sidebar-closed');
    localStorage.setItem('admin_sidebar_open', !layout.classList.contains('sidebar-closed'));
  }
}

// Initialize theme
(function initTheme() {
  const saved = localStorage.getItem('gr_theme') || 'dark';
  document.documentElement.setAttribute('data-theme', saved);
})();