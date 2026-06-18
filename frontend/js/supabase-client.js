// ============================================================
// supabase-client.js – Supabase JS SDK v2 client
// All database reads/writes go through this singleton
// 
// How to configure:
//   Edit SUPABASE_URL and SUPABASE_ANON_KEY below with your
//   values from: Supabase → Project Settings → API
//
// CDN import is in every HTML page:
//   <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/dist/umd/supabase.min.js"></script>
// ============================================================

// ── YOUR SUPABASE CREDENTIALS (replace these) ──
const SUPABASE_URL  = 'https://qvsdepksjqkjpliovvty.supabase.co';
// Backend API URL – change for production
const API_BASE = "https://graphura-group-f-1.onrender.com";

const SUPABASE_ANON = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF2c2RlcGtzanFranBsaW92dnR5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA2OTg3NDIsImV4cCI6MjA5NjI3NDc0Mn0.XFsh4M0I3EdDpmUzdoS9ngCuIfx1tIekwH2dNhsojB4';

// Create the Supabase client (available globally as `supabase`)
const supabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON);

if (!supabase) {
  console.warn('[ScamShield] Supabase client not loaded — using static demo data. Add the Supabase CDN script before supabase-client.js');
}

// ============================================================
// DB helpers — each returns data or throws
// These wrap Supabase queries so pages don't write raw SQL
// ============================================================

const DB = {

  // ── Community posts ──
  async getCommunityPosts({ type = null, search = null, sort = 'created_at', limit = 20 } = {}) {
    if (!supabase) return DEMO_DATA.communityPosts;
    let q = supabase
      .from('community_posts')
      .select(`*, users(full_name, avatar_url), community_votes(vote_type)`)
      .eq('status', 'active')
      .order(sort, { ascending: false })
      .limit(limit);
    if (type && type !== 'all') q = q.eq('post_type', type);
    if (search) q = q.or(`title.ilike.%${search}%,content.ilike.%${search}%,company.ilike.%${search}%`);
    const { data, error } = await q;
    if (error) throw error;
    return data;
  },

  async createCommunityPost({ title, content, post_type, company, domain, author_id }) {
    if (!supabase) { showToast('Connect Supabase to save posts', 'warning'); return null; }
    const { data, error } = await supabase.from('community_posts').insert({
      title, content, post_type, company, domain, author_id
    }).select().single();
    if (error) throw error;
    return data;
  },

  async votePost(post_id, user_id, vote_type) {
    if (!supabase) return;
    // Upsert: one vote per user per post
    const { error } = await supabase.from('community_votes')
      .upsert({ post_id, user_id, vote_type }, { onConflict: 'post_id,user_id' });
    if (error) throw error;
  },

  async addComment(post_id, author_id, content) {
    if (!supabase) { showToast('Connect Supabase to save comments', 'warning'); return null; }
    const { data, error } = await supabase.from('community_comments')
      .insert({ post_id, author_id, content }).select().single();
    if (error) throw error;
    return data;
  },

  // ── User Reports ──
  async submitReport({ company_name, job_title, domain, job_url, scam_type, description, severity, reporter_id }) {
    if (!supabase) { showToast('Connect Supabase to save reports', 'warning'); return { report_id: 'DEMO-' + Date.now() }; }
    const { data, error } = await supabase.from('user_reports').insert({
      company_name, job_title, domain, job_url, scam_type, description, severity, reporter_id,
      status: 'pending'
    }).select().single();
    if (error) throw error;
    return data;
  },

  async getUserReports(user_id) {
    if (!supabase) return DEMO_DATA.userReports;
    const { data, error } = await supabase.from('user_reports')
      .select('*').eq('reporter_id', user_id).order('reported_at', { ascending: false });
    if (error) throw error;
    return data;
  },

  // ── Admin: Reports ──
  async getAllReports({ status = null } = {}) {
    if (!supabase) return DEMO_DATA.adminReports;
    let q = supabase.from('user_reports')
      .select(`*, users(full_name, email)`)
      .order('reported_at', { ascending: false });
    if (status) q = q.eq('status', status);
    const { data, error } = await q;
    if (error) throw error;
    return data;
  },

  async updateReportStatus(report_id, status, admin_notes = '') {
    if (!supabase) { showToast('Demo mode: status updated locally', 'info'); return; }
    const { error } = await supabase.from('user_reports')
      .update({ status, admin_notes, reviewed_at: new Date().toISOString() })
      .eq('report_id', report_id);
    if (error) throw error;
  },

  // ── Admin: Community ──
  async getAllPosts({ status = null } = {}) {
    if (!supabase) return DEMO_DATA.communityPosts;
    let q = supabase.from('community_posts')
      .select(`*, users(full_name)`)
      .order('created_at', { ascending: false });
    if (status) q = q.eq('status', status);
    const { data, error } = await q;
    if (error) throw error;
    return data;
  },

  async updatePostStatus(post_id, status) {
    if (!supabase) return;
    const { error } = await supabase.from('community_posts').update({ status }).eq('post_id', post_id);
    if (error) throw error;
  },

  // ── Admin: Listings ──
  async getListings({ status = null } = {}) {
    if (!supabase) return DEMO_DATA.listings;
    let q = supabase.from('job_listings')
      .select(`*, analysis(risk_score, risk_level, summary), companies(name, status)`)
      .order('created_at', { ascending: false });
    if (status) q = q.eq('status', status);
    const { data, error } = await q;
    if (error) throw error;
    return data;
  },

  async updateListingStatus(listing_id, status) {
    if (!supabase) return;
    const { error } = await supabase.from('job_listings').update({ status, updated_at: new Date().toISOString() }).eq('listing_id', listing_id);
    if (error) throw error;
  },

  // ── Knowledge Base: Companies ──
  async getCompanies() {
    if (!supabase) return DEMO_DATA.companies;
    const { data, error } = await supabase.from('companies').select('*').order('name');
    if (error) throw error;
    return data;
  },

  async updateCompanyStatus(company_id, status) {
    if (!supabase) return;
    const { error } = await supabase.from('companies').update({ status, updated_at: new Date().toISOString() }).eq('company_id', company_id);
    if (error) throw error;
  },

  // ── Knowledge Base: Domains ──
  async getDomains() {
    if (!supabase) return DEMO_DATA.domains;
    const { data, error } = await supabase.from('domain_analysis').select('*').order('last_checked', { ascending: false });
    if (error) throw error;
    return data;
  },

  async updateDomainStatus(domain_id, status) {
    if (!supabase) return;
    const { error } = await supabase.from('domain_analysis').update({ status }).eq('domain_id', domain_id);
    if (error) throw error;
  },

  // ── Knowledge Base: Scam Indicators ──
  async getIndicators() {
    if (!supabase) return DEMO_DATA.indicators;
    const { data, error } = await supabase.from('scam_indicators').select('*').order('weight', { ascending: false });
    if (error) throw error;
    return data;
  },

  async addIndicator({ keyword, category, weight }) {
    if (!supabase) { showToast('Demo mode', 'info'); return; }
    const { error } = await supabase.from('scam_indicators').insert({ keyword, category, weight });
    if (error) throw error;
  },

  async updateIndicatorWeight(indicator_id, weight) {
    if (!supabase) return;
    const { error } = await supabase.from('scam_indicators').update({ weight }).eq('indicator_id', indicator_id);
    if (error) throw error;
  },

  // ── Audit Logs ──
  async logAction({ admin_id, action, target_type, target_id, notes = '' }) {
    if (!supabase) return;
    await supabase.from('audit_logs').insert({ admin_id, action, target_type, target_id, notes });
  },

  async getAuditLogs(limit = 50) {
    if (!supabase) return DEMO_DATA.auditLogs;
    const { data, error } = await supabase.from('audit_logs')
      .select(`*, admin_users(full_name)`)
      .order('created_at', { ascending: false })
      .limit(limit);
    if (error) throw error;
    return data;
  },

  // ── Users (admin) ──
  async getUsers() {
    if (!supabase) return DEMO_DATA.users;
    const { data, error } = await supabase.from('users').select('*').order('created_at', { ascending: false });
    if (error) throw error;
    return data;
  },

  // ── Admin KPIs ──
  async getKPIs() {
    if (!supabase) return DEMO_DATA.kpis;
    const [reports, posts, listings, domains] = await Promise.all([
      supabase.from('user_reports').select('status', { count: 'exact', head: false }),
      supabase.from('community_posts').select('post_id', { count: 'exact', head: false }),
      supabase.from('job_listings').select('status', { count: 'exact', head: false }),
      supabase.from('domain_analysis').select('status', { count: 'exact', head: false }),
    ]);
    const rData = reports.data || [];
    const lData = listings.data || [];
    const dData = domains.data || [];
    return {
      pendingReports:    rData.filter(r => r.status === 'pending').length,
      confirmedScams:    rData.filter(r => r.status === 'confirmed').length,
      communityPosts:    posts.data?.length || 0,
      highRiskListings:  lData.filter(l => l.status === 'flagged').length,
      blacklistedDomains: dData.filter(d => d.status === 'blacklisted').length,
      suspiciousDomains: dData.filter(d => d.status === 'suspicious').length,
    };
  },

  // ── Public: Blacklisted domains widget ──
  async getBlacklistedDomains(limit = 12) {
    if (!supabase) return DEMO_DATA.domains.filter(d => d.status === 'blacklisted' || d.status === 'suspicious').slice(0, limit);
    const { data, error } = await supabase.from('domain_analysis')
      .select('domain, status, trust_score, report_count, last_checked, reason')
      .in('status', ['blacklisted', 'suspicious'])
      .order('report_count', { ascending: false })
      .limit(limit);
    if (error) return DEMO_DATA.domains;
    return data;
  },

  // ── Save analysis result ──
  async saveAnalysis({ title, company_name, source_url, description, domain, recruiter_email, risk_score, risk_level, domain_risk, recruiter_risk, content_risk, salary_risk, structure_risk, indicators, summary, user_id }) {
    if (!supabase) {
      const reportId = 'SS-2026-' + Math.floor(Math.random() * 90000 + 10000);
      return { analysis_id: 'demo-' + Date.now(), report_id: reportId, risk_score, risk_level };
    }
    // 1. Upsert company
    let companyId = null;
    if (company_name) {
      const { data: co } = await supabase.from('companies').upsert({ name: company_name, domain }, { onConflict: 'domain', ignoreDuplicates: true }).select('company_id').single();
      companyId = co?.company_id;
    }
    // 2. Insert listing
    const { data: listing } = await supabase.from('job_listings').insert({
      title, company_name, company_id: companyId, source_url, description, domain, recruiter_email,
      submitted_by: user_id, status: risk_level === 'LOW' ? 'safe' : 'flagged'
    }).select('listing_id').single();

    // 3. Generate report ID
    const reportId = 'SS-' + new Date().getFullYear() + '-' + Math.floor(Math.random() * 90000 + 10000);

    // 4. Insert analysis
    const { data: anal } = await supabase.from('analysis').insert({
      listing_id: listing.listing_id, risk_score, risk_level,
      domain_risk, recruiter_risk, content_risk, salary_risk, structure_risk,
      indicators, summary, report_id: reportId
    }).select('analysis_id').single();

    // 5. Update listing with analysis_id
    await supabase.from('job_listings').update({ analysis_id: anal.analysis_id }).eq('listing_id', listing.listing_id);

    // 6. Update user check count
    if (user_id) await supabase.from('users').update({ checks_count: supabase.raw('checks_count + 1') }).eq('user_id', user_id);

    return { ...anal, report_id: reportId };
  },
};

// ============================================================
// DEMO DATA – used when Supabase is not yet connected
// ============================================================
const DEMO_DATA = {
  kpis: { pendingReports: 67, confirmedScams: 214, communityPosts: 189, highRiskListings: 43, blacklistedDomains: 89, suspiciousDomains: 34 },
  domains: [
    { domain_id:'d1', domain:'careers-google-jobs.xyz', status:'blacklisted', trust_score:4, ssl_valid:false, registrar:'Unknown', report_count:14, last_checked:new Date().toISOString(), reason:'Fee demand, brand impersonation' },
    { domain_id:'d2', domain:'tcs-careers2025.in', status:'blacklisted', trust_score:3, ssl_valid:false, registrar:'Unknown', report_count:11, last_checked:new Date().toISOString(), reason:'TCS impersonation, fake offer letters' },
    { domain_id:'d3', domain:'infosys-hr-jobs.tk', status:'blacklisted', trust_score:2, ssl_valid:false, registrar:'Unknown', report_count:9, last_checked:new Date().toISOString(), reason:'Infosys impersonation, phishing' },
    { domain_id:'d4', domain:'netjob-india.xyz', status:'blacklisted', trust_score:6, ssl_valid:false, registrar:'Unknown', report_count:8, last_checked:new Date().toISOString(), reason:'Registration fee, MLM' },
    { domain_id:'d5', domain:'digiwork-india.net', status:'suspicious', trust_score:28, ssl_valid:true, registrar:'Unknown', report_count:9, last_checked:new Date().toISOString(), reason:'Unpaid work, vanished' },
    { domain_id:'d6', domain:'quickearnings-jobs.in', status:'suspicious', trust_score:32, ssl_valid:false, registrar:'Unknown', report_count:4, last_checked:new Date().toISOString(), reason:'MLM structure' },
  ],
  companies: [
    { company_id:'c1', name:'Career Solutions Ltd', domain:'career-solutions.xyz', status:'blacklisted', trust_score:5, report_count:14 },
    { company_id:'c2', name:'DigiWork India', domain:'digiwork-india.net', status:'suspicious', trust_score:28, report_count:9 },
    { company_id:'c3', name:'Tata Consultancy Services', domain:'tcs.com', status:'verified', trust_score:98, report_count:0 },
    { company_id:'c4', name:'Infosys', domain:'infosys.com', status:'verified', trust_score:97, report_count:0 },
  ],
  indicators: [
    { indicator_id:'i1', keyword:'registration fee', category:'fee_demand', weight:3.0, is_active:true },
    { indicator_id:'i2', keyword:'security deposit', category:'fee_demand', weight:3.0, is_active:true },
    { indicator_id:'i3', keyword:'guaranteed placement', category:'urgency', weight:2.0, is_active:true },
    { indicator_id:'i4', keyword:'whatsapp only', category:'contact', weight:2.0, is_active:true },
    { indicator_id:'i5', keyword:'gmail recruiter', category:'contact', weight:2.5, is_active:true },
    { indicator_id:'i6', keyword:'data entry', category:'structure', weight:1.0, is_active:true },
  ],
  communityPosts: [
    { post_id:'p1', title:'Career Solutions Ltd asked for ₹5000 registration fee!', content:'After interview they asked for registration fee. Domain registered 2 weeks ago. Complete fraud!', post_type:'scam_report', company:'Career Solutions Ltd', domain:'career-solutions.xyz', status:'active', created_at: new Date(Date.now()-7*86400000).toISOString(), users:{full_name:'Rahul S.'}, community_votes:[ ...Array(14).fill({vote_type:'upvote'}) ] },
    { post_id:'p2', title:'DigiWork India – no payment after 2 weeks of work', content:'WFH data entry job promised ₹800/hr. After 2 weeks no payment. Website went offline.', post_type:'scam_report', company:'DigiWork India', status:'active', created_at: new Date(Date.now()-3*86400000).toISOString(), users:{full_name:'Priya M.'}, community_votes:[ ...Array(8).fill({vote_type:'upvote'}) ] },
    { post_id:'p3', title:'TCS Impersonation – domain tcs-careers2025.in', content:'Got offer from tcs-careers2025.in — not tcs.com. Offer had ₹3000 security deposit. Fake!', post_type:'scam_report', company:'TCS (Fake)', domain:'tcs-careers2025.in', status:'active', created_at: new Date(Date.now()-1*86400000).toISOString(), users:{full_name:'Ankit R.'}, community_votes:[ ...Array(22).fill({vote_type:'upvote'}) ] },
    { post_id:'p4', title:'Has anyone verified jobs from Naukri today?', content:'Saw multiple suspicious listings on Naukri claiming to be from Amazon. Anyone else?', post_type:'discussion', status:'active', created_at: new Date(Date.now()-2*86400000).toISOString(), users:{full_name:'Sneha P.'}, community_votes:[ ...Array(5).fill({vote_type:'upvote'}) ] },
  ],
  adminReports: [
    { report_id:'r1', company_name:'Career Solutions Ltd', job_title:'Data Entry Executive', domain:'career-solutions.xyz', scam_type:'fee_demand', severity:'critical', status:'pending', reported_at:new Date(Date.now()-7*86400000).toISOString(), users:{full_name:'Rahul S.',email:'rahul@gmail.com'} },
    { report_id:'r2', company_name:'DigiWork India', job_title:'WFH Customer Care', domain:'digiwork-india.net', scam_type:'fake_offer', severity:'high', status:'pending', reported_at:new Date(Date.now()-3*86400000).toISOString(), users:{full_name:'Priya M.',email:'priya@gmail.com'} },
    { report_id:'r3', company_name:'TCS (Fake)', job_title:'Software Engineer', domain:'tcs-careers2025.in', scam_type:'impersonation', severity:'high', status:'under_review', reported_at:new Date(Date.now()-1*86400000).toISOString(), users:{full_name:'Ankit R.',email:'ankit@gmail.com'} },
  ],
  listings: [
    { listing_id:'l1', title:'Data Entry Intern', company_name:'XYZ Solutions', domain:'xyz-solutions.xyz', status:'flagged', created_at:new Date().toISOString(), analysis:{risk_score:87, risk_level:'HIGH', summary:'Fee demand, Gmail recruiter, new domain'} },
    { listing_id:'l2', title:'Python Developer', company_name:'TCS', domain:'tcs.com', status:'safe', created_at:new Date().toISOString(), analysis:{risk_score:5, risk_level:'LOW', summary:'Verified official TCS posting'} },
  ],
  users: [
    { user_id:'u1', full_name:'Rahul Sharma', email:'rahul@gmail.com', role:'user', is_active:true, reports_count:5, checks_count:23, created_at:new Date(Date.now()-14*86400000).toISOString() },
    { user_id:'u2', full_name:'Priya Mehta', email:'priya@gmail.com', role:'user', is_active:true, reports_count:3, checks_count:8, created_at:new Date(Date.now()-7*86400000).toISOString() },
  ],
  userReports: [],
  auditLogs: [
    { log_id:'log1', action:'CONFIRM_REPORT', target_type:'REPORT', target_id:'r1', created_at:new Date().toISOString(), admin_users:{full_name:'Admin'} },
    { log_id:'log2', action:'BLACKLIST_DOMAIN', target_type:'DOMAIN', target_id:'d3', created_at:new Date(Date.now()-3600000).toISOString(), admin_users:{full_name:'Admin'} },
  ],
};
