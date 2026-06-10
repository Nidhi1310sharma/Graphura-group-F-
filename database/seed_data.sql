-- ============================================================
-- ScamShield v4 – Seed Data
-- ============================================================

-- Admin user (password: Admin@123)
INSERT INTO users (email, password_hash, full_name, mobile, city, profession, bio, role, skills, is_active, email_verified) VALUES
('admin@scamshield.in', crypt('Admin@123', gen_salt('bf')), 'Admin User', '9999999999', 'Mumbai', 'Platform Administrator', 'ScamShield platform administrator.', 'admin', ARRAY['Platform Management','Data Analysis','Fraud Detection'], TRUE, TRUE)
ON CONFLICT (email) DO NOTHING;

-- Demo users
INSERT INTO users (email, password_hash, full_name, mobile, city, profession, bio, role, skills, is_active, email_verified, reports_count, checks_count) VALUES
('rahul@gmail.com', crypt('User@123', gen_salt('bf')), 'Rahul S.', '9876543210', 'Pune', 'Job Seeker', 'Active community member helping others stay safe from job scams.', 'user', ARRAY['Data Entry','MS Office','Communication'], TRUE, TRUE, 14, 45),
('priya@outlook.com', crypt('User@123', gen_salt('bf')), 'Priya M.', '9123456789', 'Mumbai', 'Fresher', 'Graduate looking for genuine jobs. Exposing scammers!', 'user', ARRAY['Marketing','Social Media','Content Writing'], TRUE, TRUE, 8, 23),
('ankit@gmail.com', crypt('User@123', gen_salt('bf')), 'Ankit R.', '9001234567', 'Aurangabad', 'Working Professional', 'Software engineer. Helping job seekers spot fake IT jobs.', 'user', ARRAY['Python','Java','Software Development'], TRUE, TRUE, 3, 12),
('neha@gmail.com', crypt('User@123', gen_salt('bf')), 'Neha S.', '9876501234', 'Nagpur', 'Student', 'Final year student. Sharing scam experiences to help others.', 'user', ARRAY['Digital Marketing','SEO'], TRUE, TRUE, 1, 5)
ON CONFLICT (email) DO NOTHING;

-- Flagged Keywords
INSERT INTO flagged_keywords (keyword, fraud_weight, category) VALUES
('registration fee', 0.95, 'financial'),
('security deposit', 0.95, 'financial'),
('registration charges', 0.9, 'financial'),
('training fee', 0.9, 'financial'),
('joining fee', 0.9, 'financial'),
('kit fee', 0.88, 'financial'),
('id card fee', 0.88, 'financial'),
('background check fee', 0.85, 'financial'),
('refundable deposit', 0.85, 'financial'),
('work from home', 0.3, 'wfh'),
('data entry', 0.35, 'role'),
('no experience required', 0.4, 'qualification'),
('earn daily', 0.75, 'payment'),
('daily payout', 0.75, 'payment'),
('₹5000 per day', 0.8, 'salary'),
('urgent hiring', 0.5, 'urgency'),
('immediate joining', 0.45, 'urgency'),
('apply asap', 0.45, 'urgency'),
('limited seats', 0.55, 'urgency'),
('contact on whatsapp', 0.7, 'communication'),
('whatsapp only', 0.75, 'communication'),
('telegram group', 0.65, 'communication'),
('gmail.com hr', 0.8, 'email_domain'),
('yahoo.com recruiter', 0.75, 'email_domain'),
('100% job guarantee', 0.8, 'guarantee'),
('guaranteed placement', 0.7, 'guarantee'),
('no interview required', 0.6, 'process'),
('direct joining', 0.55, 'process'),
('part time work from home', 0.5, 'role'),
('earn upto', 0.4, 'salary')
ON CONFLICT (keyword) DO NOTHING;

-- Domain Reputation
INSERT INTO domain_reputation (domain_name, domain_age_days, ssl_valid, trust_score, blacklisted, suspicious_pattern, report_count) VALUES
('careers-google-jobs.xyz', 14, FALSE, 2.0, TRUE, TRUE, 14),
('infosys-hr-jobs.tk', 8, FALSE, 1.5, TRUE, TRUE, 9),
('tcs-careers2025.in', 22, FALSE, 3.0, TRUE, TRUE, 11),
('workfromhome-india.net', 45, FALSE, 8.0, TRUE, TRUE, 6),
('wipro-global.xyz', 18, FALSE, 2.5, TRUE, TRUE, 7),
('infosys.com', 9800, TRUE, 98.0, FALSE, FALSE, 0),
('tcs.com', 9500, TRUE, 97.0, FALSE, FALSE, 0),
('wipro.com', 9200, TRUE, 96.5, FALSE, FALSE, 0),
('naukri.com', 8000, TRUE, 95.0, FALSE, FALSE, 0),
('linkedin.com', 7500, TRUE, 99.0, FALSE, FALSE, 0)
ON CONFLICT (domain_name) DO NOTHING;

-- Blacklisted Entities
INSERT INTO blacklisted_entities (entity_type, entity_value, reason, report_count, severity, source) VALUES
('domain', 'careers-google-jobs.xyz', 'Fake Google careers site, fee demand', 14, 'critical', 'user_report'),
('domain', 'infosys-hr-jobs.tk', 'Infosys impersonation, 0-day SSL', 9, 'critical', 'auto_detected'),
('domain', 'tcs-careers2025.in', 'TCS brand abuse, phishing', 11, 'critical', 'admin'),
('email', 'tcs-hr@gmail.com', 'Fake TCS HR, demanded background check fee', 9, 'critical', 'user_report'),
('email', 'hr@infosys-careers.tk', 'Infosys impersonation via fake domain', 7, 'critical', 'user_report'),
('company', 'Career Solutions Ltd', 'Multiple reports of ₹5000 fee demand', 14, 'critical', 'auto_detected'),
('company', 'DigiWork India', 'No payment after work completed', 8, 'high', 'user_report'),
('company', 'GlobalWork', 'Kit fee demand scam', 6, 'high', 'user_report'),
('phone', '7894561230', 'WhatsApp scam recruiter for fake WFH jobs', 5, 'medium', 'user_report')
ON CONFLICT (entity_type, entity_value) DO NOTHING;

-- Job Posts
INSERT INTO job_posts (title, company_name, salary_text, location, description, domain_name, recruiter_email, scam_score, risk_level, is_flagged, keyword_score, domain_score, salary_score, analyzed_at) VALUES
('Data Entry Intern', 'Career Solutions Ltd', '₹25,000/month', 'Work From Home', 'Urgent hiring for data entry. No experience required. Register now with ₹5000 security deposit to secure your seat. Immediate joining. Contact on WhatsApp only.', 'careers-google-jobs.xyz', 'hr.careersolutions@gmail.com', 87.5, 'CONFIRMED_SCAM', TRUE, 85.0, 92.0, 60.0, NOW()),
('WFH Data Analyst', 'TechGrow India', '₹40,000/month', 'Work From Home', 'Work from home data entry and analysis. Earn daily ₹800-1200. No experience needed. Training provided. Limited seats available. Apply ASAP.', 'techgrow-wfh.net', 'techgrow.hr@yahoo.com', 72.0, 'HIGH', TRUE, 70.0, 75.0, 55.0, NOW()),
('Digital Marketing Executive', 'GlobalWork', '₹6 LPA', 'Remote', 'Digital marketing role. No interview required. Direct joining. Register by paying kit fee of ₹1500. 100% job guarantee. WFH available.', 'globalwork.in', 'globalwork@gmail.com', 61.0, 'HIGH', TRUE, 65.0, 45.0, 50.0, NOW()),
('HR Recruiter WFH', 'CareerBoost Pvt', '₹35,000/month', 'Work From Home', 'Hiring HR recruiters for WFH. Earn daily. Part time work from home available. WhatsApp only for communication.', 'careerboost-pvt.xyz', 'hr@careerboost.in', 68.0, 'HIGH', TRUE, 62.0, 70.0, 45.0, NOW()),
('Software Engineer', 'Infosys (Verified)', '₹6-10 LPA', 'Pune / Bengaluru', 'Join Infosys as a Software Engineer. We are hiring freshers and experienced professionals. Online test followed by HR interview. Official joining process.', 'infosys.com', 'campus@infosys.com', 8.0, 'LOW', FALSE, 5.0, 0.0, 10.0, NOW())
ON CONFLICT DO NOTHING;

-- Scam Reports
INSERT INTO scam_reports (company_name, job_title, scam_type, report_reason, reporter_name, reporter_email, status, upvotes, reported_at) VALUES
('Career Solutions Ltd', 'Data Entry Intern', 'fee_demand', 'Asked for ₹5000 registration fee after interview. Domain registered 2 weeks ago. Gmail account used for communication. Avoid!', 'Rahul S.', 'rahul@gmail.com', 'confirmed', 14, NOW() - INTERVAL '7 days'),
('DigiWork India', 'WFH Data Entry', 'fake_offer', 'WFH data entry job promised ₹800/hr. After 2 weeks of work, no payment received. Company website now offline.', 'Priya M.', 'priya@outlook.com', 'confirmed', 8, NOW() - INTERVAL '3 days'),
('TCS (Impersonation)', 'Software Engineer', 'impersonation', 'Received offer from tcs-hr@gmail.com. Asked to pay ₹2000 for background verification. TCS never charges for this.', 'Ankit R.', 'ankit@gmail.com', 'pending', 3, NOW() - INTERVAL '1 day'),
('PixelBoost Media', 'Digital Marketing Exec', 'suspicious', 'Offered ₹6LPA as fresher with no experience. 5-minute WhatsApp interview. Offer letter had grammatical errors.', 'Neha S.', 'neha@gmail.com', 'pending', 5, NOW() - INTERVAL '5 days')
ON CONFLICT DO NOTHING;

-- Community Posts
INSERT INTO community_posts (company_name, job_title, domain, salary_offered, post_type, body, upvotes, reply_count) VALUES
('Career Solutions Ltd', 'Data Entry Intern', 'careers-google-jobs.xyz', NULL, 'scam', 'Asked for ₹5000 registration fee after interview. Domain was registered just 2 weeks ago. They used a Gmail account for communication despite claiming to be from Google. Complete fraud — avoid at all costs! Reported to cyber crime portal also.', 14, 3),
('DigiWork India', 'WFH Data Entry', NULL, '₹800/hr promised', 'suspicious', 'WFH data entry job that promised ₹800/hr. After 2 weeks of actual work — entering data daily — no payment was received. Company website went offline last week. Phone numbers are now unreachable.', 8, 1),
('TCS Impersonation', 'Software Engineer', NULL, NULL, 'scam', 'Received an offer from someone claiming to be from TCS HR. Email was tcs-hr@gmail.com — no official TCS domain. They asked to pay ₹2000 for background verification before joining. TCS never charges for background checks.', 3, 0),
('PixelBoost Media', 'Digital Marketing Executive', NULL, '₹6LPA', 'suspicious', 'Received an offer for ₹6LPA as a digital marketing executive — freshers welcome, no experience needed. Interview was just 5 minutes on WhatsApp call. Offer letter had many grammatical errors.', 5, 0)
ON CONFLICT DO NOTHING;

-- Recruiter Profiles (Blacklisted)
INSERT INTO recruiter_profiles (recruiter_name, email, company, domain_name, verified, blacklisted, blacklist_reason, previous_reports, trust_score) VALUES
('Fake TCS HR', 'tcs-hr@gmail.com', 'TCS (Impersonation)', 'gmail.com', FALSE, TRUE, 'Impersonating TCS HR, demanded background check fee', 9, 2.0),
('Fake Infosys HR', 'hr@infosys-careers.tk', 'Infosys (Impersonation)', 'infosys-careers.tk', FALSE, TRUE, 'Infosys brand abuse, phishing attempts', 7, 1.5)
ON CONFLICT (email) DO NOTHING;
