// ============================================================
// api.js - API Service with Authentication
// ============================================================

const API_BASE = "http://localhost:8000/api";

class AuthService {
    static getToken() {
        return localStorage.getItem('auth_token');
    }
    
    static setToken(token) {
        localStorage.setItem('auth_token', token);
    }
    
    static removeToken() {
        localStorage.removeItem('auth_token');
    }
    
    static getUser() {
        const user = localStorage.getItem('user');
        return user ? JSON.parse(user) : null;
    }
    
    static setUser(user) {
        localStorage.setItem('user', JSON.stringify(user));
    }
    
    static isAuthenticated() {
        return !!this.getToken();
    }
    
    static isAdmin() {
        const user = this.getUser();
        return user && user.role === 'admin';
    }
    
    static async login(email, password) {
        const response = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        
        if (!response.ok) throw new Error('Login failed');
        const data = await response.json();
        this.setToken(data.token);
        this.setUser(data.user);
        return data;
    }
    
    static async register(userData) {
        const response = await fetch(`${API_BASE}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(userData)
        });
        
        if (!response.ok) throw new Error('Registration failed');
        return await response.json();
    }
    
    static async logout() {
        this.removeToken();
        this.setUser(null);
        window.location.href = '/login.html';
    }
}

class ApiService {
    static async request(endpoint, options = {}) {
        const token = AuthService.getToken();
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };
        
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        const response = await fetch(`${API_BASE}${endpoint}`, {
            ...options,
            headers
        });
        
        if (response.status === 401) {
            AuthService.logout();
            throw new Error('Session expired');
        }
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Request failed');
        }
        
        return response.json();
    }
    
    static get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    }
    
    static post(endpoint, data) {
        return this.request(endpoint, { method: 'POST', body: JSON.stringify(data) });
    }
    
    static put(endpoint, data) {
        return this.request(endpoint, { method: 'PUT', body: JSON.stringify(data) });
    }
    
    static delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }
    
    // User endpoints
    static getProfile() {
        return this.get('/users/profile');
    }
    
    static updateProfile(data) {
        return this.put('/users/profile', data);
    }
    
    static uploadImage(file) {
        const formData = new FormData();
        formData.append('image', file);
        
        return fetch(`${API_BASE}/users/upload-image`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${AuthService.getToken()}` },
            body: formData
        }).then(res => res.json());
    }
    
    // Job endpoints
    static analyzeJob(data) {
        return this.post('/analyze', data);
    }
    
    static getJobs(params = {}) {
        const query = new URLSearchParams(params).toString();
        return this.get(`/jobs${query ? `?${query}` : ''}`);
    }
    
    // Report endpoints
    static submitReport(data) {
        return this.post('/reports', data);
    }
    
    static getReports() {
        return this.get('/reports');
    }
    
    // Community endpoints
    static getPosts() {
        return this.get('/community/posts');
    }
    
    static createPost(content, scamReportId = null) {
        return this.post('/community/posts', { content, scam_report_id: scamReportId });
    }
    
    static likePost(postId) {
        return this.post(`/community/posts/${postId}/like`);
    }
    
    static addComment(postId, content) {
        return this.post(`/community/posts/${postId}/comments`, { content });
    }
    
    // Admin endpoints
    static getDashboardStats() {
        return this.get('/admin/stats');
    }
    
    static getPendingReports() {
        return this.get('/admin/reports/pending');
    }
    
    static updateReportStatus(reportId, status, notes) {
        return this.put(`/admin/reports/${reportId}`, { status, admin_notes: notes });
    }
    
    static getUsers() {
        return this.get('/admin/users');
    }
    
    static updateUserRole(userId, role) {
        return this.put(`/admin/users/${userId}/role`, { role });
    }
}

// Theme Toggle
function initTheme() {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        document.documentElement.setAttribute('data-theme', 'dark');
    }
    
    const btn = document.createElement('button');
    btn.className = 'theme-toggle';
    btn.innerHTML = document.documentElement.getAttribute('data-theme') === 'dark' ? '☀️' : '🌙';
    btn.onclick = () => {
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        if (isDark) {
            document.documentElement.removeAttribute('data-theme');
            localStorage.setItem('theme', 'light');
            btn.innerHTML = '🌙';
        } else {
            document.documentElement.setAttribute('data-theme', 'dark');
            localStorage.setItem('theme', 'dark');
            btn.innerHTML = '☀️';
        }
    };
    document.body.appendChild(btn);
}

// Navbar with user avatar
function initNavbar() {
    const user = AuthService.getUser();
    const navRight = document.querySelector('.nav-right');
    
    if (user) {
        if (navRight) {
            navRight.innerHTML = `
                <div class="dropdown" id="user-dropdown">
                    <img src="${user.profile_image || '/assets/default-avatar.png'}" class="user-avatar" alt="Profile">
                    <div class="dropdown-menu">
                        <a href="/profile.html">👤 My Profile</a>
                        <a href="/my-activities.html">📋 My Activities</a>
                        <a href="/my-reports.html">🚨 My Reports</a>
                        <hr>
                        ${user.role === 'admin' ? '<a href="/admin.html">⚙️ Admin Panel</a><hr>' : ''}
                        <a href="#" onclick="AuthService.logout()">🚪 Logout</a>
                    </div>
                </div>
            `;
            
            // Dropdown toggle
            const dropdown = document.getElementById('user-dropdown');
            dropdown.addEventListener('click', (e) => {
                e.stopPropagation();
                dropdown.classList.toggle('active');
            });
            
            document.addEventListener('click', () => {
                dropdown.classList.remove('active');
            });
        }
    } else if (navRight) {
        navRight.innerHTML = `
            <a href="/login.html" class="btn btn-outline btn-sm">Login</a>
            <a href="/register.html" class="btn btn-primary btn-sm">Sign Up</a>
        `;
    }
    
    // Set active nav link
    const currentPage = window.location.pathname.split('/').pop();
    document.querySelectorAll('.nav-links a').forEach(link => {
        if (link.getAttribute('href') === currentPage) {
            link.classList.add('active');
        }
    });
}

// Toast notification
function showToast(message, type = 'info') {
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = message;
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initNavbar();
});

// Export for use in HTML
window.AuthService = AuthService;
window.ApiService = ApiService;
window.showToast = showToast;