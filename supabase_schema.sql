-- ============================================================================
-- FinSmart - Supabase PostgreSQL Schema & Seed Data
-- Database Engine: PostgreSQL 15 / 16 (Supabase Managed)
-- Features: Row-Level Security (RLS), DPDP Act 2023 Compliance, Integer Paise
-- ============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 1. Tenants (Colleges, Universities & Public Portal)
CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    domain TEXT,
    subscription_tier TEXT NOT NULL DEFAULT 'standard',
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 2. Users (Bound to Tenant, Argon2id/Bcrypt Authentication)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    phone_number TEXT,
    role TEXT NOT NULL DEFAULT 'student' CHECK (role IN ('student', 'faculty', 'college_admin', 'admin')),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, email)
);

-- 3. Demographic & Socio-economic User Profiles (For Scheme Matching)
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    age INTEGER CHECK (age >= 0 AND age <= 120),
    gender TEXT CHECK (gender IN ('male', 'female', 'other', 'prefer_not_to_say')),
    state TEXT NOT NULL DEFAULT 'Karnataka',
    district TEXT,
    is_student BOOLEAN NOT NULL DEFAULT true,
    academic_year TEXT,
    department TEXT,
    annual_family_income_minor BIGINT NOT NULL DEFAULT 0,
    social_category TEXT NOT NULL DEFAULT 'GEN' CHECK (social_category IN ('GEN', 'OBC', 'SC', 'ST', 'EWS')),
    has_bank_account BOOLEAN NOT NULL DEFAULT true,
    has_disability BOOLEAN NOT NULL DEFAULT false,
    ration_card_type TEXT NOT NULL DEFAULT 'None' CHECK (ration_card_type IN ('BPL', 'APL', 'AAY', 'None')),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 4. Financial Accounts (Cash, Bank, Wallets - Balances in Paise)
CREATE TABLE IF NOT EXISTS accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    account_type TEXT NOT NULL DEFAULT 'BANK' CHECK (account_type IN ('BANK', 'CASH', 'WALLET', 'SAVINGS')),
    balance_minor BIGINT NOT NULL DEFAULT 0,
    currency CHAR(3) NOT NULL DEFAULT 'INR',
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 5. Transactions Ledger (Strictly integer paise minor units)
CREATE TABLE IF NOT EXISTS transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    account_id UUID REFERENCES accounts(id) ON DELETE SET NULL,
    client_id UUID NOT NULL,
    amount_minor BIGINT NOT NULL CHECK (amount_minor > 0),
    currency CHAR(3) NOT NULL DEFAULT 'INR',
    kind TEXT NOT NULL CHECK (kind IN ('DEBIT', 'CREDIT')),
    category TEXT NOT NULL,
    payment_mode TEXT NOT NULL DEFAULT 'UPI' CHECK (payment_mode IN ('CASH', 'UPI', 'CARD', 'BANK', 'WALLET')),
    description TEXT NOT NULL DEFAULT '',
    occurred_on DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, client_id)
);

CREATE INDEX IF NOT EXISTS idx_transactions_user_date ON transactions(user_id, occurred_on DESC);
CREATE INDEX IF NOT EXISTS idx_transactions_tenant_user ON transactions(tenant_id, user_id);

-- 6. Budgets (Category Limits & Overspend Thresholds)
CREATE TABLE IF NOT EXISTS budgets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    limit_minor BIGINT NOT NULL CHECK (limit_minor > 0),
    period TEXT NOT NULL DEFAULT 'MONTHLY' CHECK (period IN ('MONTHLY', 'SEMESTER', 'YEARLY')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, category, period)
);

-- 7. Savings Goals (Milestones & Auto-Allocation)
CREATE TABLE IF NOT EXISTS goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    target_minor BIGINT NOT NULL CHECK (target_minor > 0),
    saved_minor BIGINT NOT NULL DEFAULT 0,
    target_date DATE,
    category TEXT NOT NULL DEFAULT 'General',
    is_completed BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 8. Consents (India DPDP Act 2023 Explicit Audit Ledger)
CREATE TABLE IF NOT EXISTS consents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    purpose TEXT NOT NULL,
    granted BOOLEAN NOT NULL,
    at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 9. Government & State Welfare Schemes
CREATE TABLE IF NOT EXISTS schemes (
    code TEXT PRIMARY KEY,
    title_en TEXT NOT NULL,
    title_kn TEXT,
    title_hi TEXT,
    agency TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'Welfare',
    summary TEXT NOT NULL,
    benefits TEXT NOT NULL,
    source_url TEXT NOT NULL,
    documents_required TEXT[] NOT NULL DEFAULT '{}',
    application_steps TEXT[] NOT NULL DEFAULT '{}',
    last_verified_at DATE,
    rule JSONB NOT NULL
);

-- 10. Financial Literacy Learning Modules
CREATE TABLE IF NOT EXISTS learning_modules (
    id SERIAL PRIMARY KEY,
    lang TEXT NOT NULL CHECK (lang IN ('en', 'kn', 'hi')),
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    body TEXT NOT NULL,
    quiz JSONB NOT NULL DEFAULT '[]'
);

-- 11. Grounding Knowledge Base for AI Assistant
CREATE TABLE IF NOT EXISTS knowledge_docs (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    content TEXT NOT NULL,
    source_citation TEXT NOT NULL
);

-- ============================================================================
-- ROW-LEVEL SECURITY (RLS) POLICIES
-- ============================================================================

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE budgets ENABLE ROW LEVEL SECURITY;
ALTER TABLE goals ENABLE ROW LEVEL SECURITY;
ALTER TABLE consents ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
    -- Users RLS Policy
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'users' AND policyname = 'users_tenant_isolation') THEN
        CREATE POLICY users_tenant_isolation ON users FOR ALL
        USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
        WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);
    END IF;

    -- User Profiles RLS Policy
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'user_profiles' AND policyname = 'user_profiles_tenant_isolation') THEN
        CREATE POLICY user_profiles_tenant_isolation ON user_profiles FOR ALL
        USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
        WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);
    END IF;

    -- Accounts RLS Policy
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'accounts' AND policyname = 'accounts_tenant_isolation') THEN
        CREATE POLICY accounts_tenant_isolation ON accounts FOR ALL
        USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
        WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);
    END IF;

    -- Transactions RLS Policy
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'transactions' AND policyname = 'transactions_tenant_isolation') THEN
        CREATE POLICY transactions_tenant_isolation ON transactions FOR ALL
        USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
        WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);
    END IF;

    -- Budgets RLS Policy
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'budgets' AND policyname = 'budgets_tenant_isolation') THEN
        CREATE POLICY budgets_tenant_isolation ON budgets FOR ALL
        USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
        WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);
    END IF;

    -- Goals RLS Policy
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'goals' AND policyname = 'goals_tenant_isolation') THEN
        CREATE POLICY goals_tenant_isolation ON goals FOR ALL
        USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
        WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);
    END IF;

    -- Consents RLS Policy
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'consents' AND policyname = 'consents_tenant_isolation') THEN
        CREATE POLICY consents_tenant_isolation ON consents FOR ALL
        USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
        WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);
    END IF;
END $$;

-- ============================================================================
-- SEED DATA (Tenants, Schemes, Literacy Modules, Knowledge Base)
-- ============================================================================

-- Tenants
INSERT INTO tenants (slug, name, domain) VALUES
('navkis', 'Navkis College of Engineering, Hassan', 'navkis.edu.in'),
('rvce', 'RV College of Engineering, Bengaluru', 'rvce.edu.in'),
('public', 'FinSmart Public Financial Literacy Portal', 'finsmart.org')
ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name;

-- Schemes
INSERT INTO schemes (code, title_en, title_kn, title_hi, agency, category, summary, benefits, source_url, documents_required, application_steps, last_verified_at, rule) VALUES
(
  'PMJDY',
  'Pradhan Mantri Jan Dhan Yojana',
  'ಪ್ರಧಾನ ಮಂತ್ರಿ ಜನ ಧನ ಯೋಜನೆ',
  'प्रधानमंत्री जन धन योजना',
  'Government of India (MoF)',
  'Banking & Insurance',
  'National mission for financial inclusion to ensure access to financial services: basic savings account, credit, insurance, and pension.',
  'Zero minimum balance, free RuPay debit card, ₹2 Lakh accidental insurance cover, ₹10,000 overdraft facility for eligible accounts.',
  'https://pmjdy.gov.in/',
  ARRAY['Aadhaar Card', 'Passport size photo', 'Address proof (if not Aadhaar)', 'Contact number'],
  ARRAY['Visit nearest nationalized bank branch or Bank Mitra / CSC kiosk', 'Fill out the PMJDY account opening form', 'Submit Aadhaar as primary KYC document', 'Receive instant passbook and RuPay debit card'],
  '2026-01-15',
  '{"all": [{"field": "age", "op": "gte", "value": 10, "label": "Age 10 years or older"}, {"field": "has_bank_account", "op": "eq", "value": false, "label": "Does not currently possess a bank account"}]}'
),
(
  'APY',
  'Atal Pension Yojana',
  'ಅಟಲ್ ಪಿಂಚಣಿ ಯೋಜನೆ',
  'अटल पेंशन योजना',
  'PFRDA / Ministry of Finance',
  'Pension & Social Security',
  'Guaranteed monthly pension scheme primarily targeted at unorganized sector workers, young earners, and gig economy participants.',
  'Guaranteed pension of ₹1,000 to ₹5,000 per month upon reaching age 60, with spouse benefit and nominee corpus return.',
  'https://www.npscra.nsdl.co.in/',
  ARRAY['Aadhaar Card', 'Active Bank Savings Account with Auto-Debit', 'Mobile Number'],
  ARRAY['Log in to internet banking or visit your savings bank branch', 'Request the APY enrolment form', 'Select preferred monthly pension slab (₹1000 - ₹5000)', 'Enable monthly auto-debit consent from your bank account'],
  '2026-02-01',
  '{"all": [{"field": "age", "op": "between", "value": [18, 40], "label": "Age between 18 and 40 years"}, {"field": "has_bank_account", "op": "eq", "value": true, "label": "Has an active bank account with auto-debit facility"}]}'
),
(
  'NSP-POSTMATRIC',
  'Post-Matric Scholarship Scheme (National)',
  'ಮೆಟ್ರಿಕ್ ನಂತರದ ವಿದ್ಯಾರ್ಥಿವೇತನ (ರಾಷ್ಟ್ರೀಯ)',
  'पोस्ट-मैट्रिक छात्रवृत्ति योजना (राष्ट्रीय)',
  'Ministry of Social Justice & Empowerment',
  'Scholarship',
  'Central sector financial support for students from underprivileged backgrounds pursuing higher education (ITI, Diploma, Degree, Masters).',
  'Full tuition fee reimbursement plus maintenance allowance up to ₹13,500/year directly to Aadhaar-seeded bank account.',
  'https://scholarships.gov.in/',
  ARRAY['Aadhaar Card', 'Income Certificate (Revenue Authority)', 'Caste Certificate (SC/ST/OBC)', 'Previous year marks sheet', 'College Bonafide / Fee Receipt'],
  ARRAY['Register online on the National Scholarship Portal (NSP)', 'Enter Aadhaar OTR (One Time Registration) verification', 'Fill academic, category, and family income details', 'Upload verified documents and submit for Institute verification'],
  '2026-02-10',
  '{"all": [{"field": "is_student", "op": "eq", "value": true, "label": "Must be an enrolled student"}, {"field": "annual_family_income", "op": "lte", "value": 250000, "label": "Annual family income up to ₹2.5 Lakhs"}, {"field": "social_category", "op": "in", "value": ["SC", "ST", "OBC"], "label": "Belongs to SC, ST, or OBC category"}]}'
),
(
  'KAR-SSP',
  'Karnataka State Scholarship Portal (SSP Post-Matric)',
  'ಕರ್ನಾಟಕ ರಾಜ್ಯ ವಿದ್ಯಾರ್ಥಿವೇತನ ತಂತ್ರಾಂಶ (SSP)',
  'कर्नाटक राज्य छात्रवृत्ति पोर्टल (एसएसपी)',
  'Government of Karnataka',
  'Scholarship',
  'Unified scholarship portal for Karnataka domicile students across Social Welfare, Tribal Welfare, Backward Classes, and Minorities departments.',
  'Tuition fee reimbursement, hostel fee concession, and direct cash incentive for college studies in Karnataka institutions.',
  'https://ssp.postmatric.karnataka.gov.in/',
  ARRAY['Student Aadhaar & Parent Aadhaar', 'KUTUMBA ID / Ration Card', 'RD Number for Caste & Income Certificate', 'SSLC & College Registration Number (UUCMS / VTU)'],
  ARRAY['Create Student Account on Karnataka SSP Portal using Aadhaar', 'Link KUTUMBA family ID for automated income verification', 'Select current college (e.g. Navkis, RVCE) and university roll number', 'Verify e-Attestation of documents and submit for approval'],
  '2026-02-14',
  '{"all": [{"field": "is_student", "op": "eq", "value": true, "label": "Currently studying in Karnataka college/university"}, {"field": "state", "op": "eq", "value": "Karnataka", "label": "Karnataka Domicile / Resident"}, {"field": "annual_family_income", "op": "lte", "value": 300000, "label": "Annual household income within eligibility ceiling (₹3 Lakhs)"}]}'
),
(
  'PM-MUDRA',
  'Pradhan Mantri MUDRA Yojana (Micro Credit)',
  'ಪ್ರಧಾನ ಮಂತ್ರಿ ಮುದ್ರಾ ಯೋಜನೆ',
  'प्रधानमंत्री मुद्रा योजना',
  'Ministry of Finance / SIDBI',
  'Livelihood & Loans',
  'Collateral-free micro loans up to ₹10 Lakhs for young entrepreneurs, artisans, graduates, and small business enterprises.',
  'Loans categorized into Shishu (up to ₹50,000), Kishore (₹50,000 to ₹5 Lakhs), and Tarun (up to ₹10 Lakhs) with subsidized interest rates.',
  'https://www.mudra.org.in/',
  ARRAY['Proof of Identity & Address (Aadhaar/PAN)', 'Business Idea / Project Report', 'Quotation of machinery or inventory to be purchased', 'Bank statement for last 6 months'],
  ARRAY['Prepare project proposal for venture or freelancing setup', 'Apply online via Udyami Mitra portal or visit designated PSU bank branch', 'Submit quotation of equipment to be funded', 'Loan disbursed directly to supplier / business account upon sanction'],
  '2026-01-20',
  '{"all": [{"field": "age", "op": "gte", "value": 18, "label": "Age 18 years or above"}, {"field": "has_bank_account", "op": "eq", "value": true, "label": "Must hold an active bank account"}]}'
),
(
  'SUKANYA',
  'Sukanya Samriddhi Yojana (SSY)',
  'ಸುಕನ್ಯಾ ಸಮೃದ್ಧಿ ಯೋಜನೆ',
  'सुकन्या समृद्धि योजना',
  'Ministry of Women and Child Development / India Post',
  'Women & Child',
  'High-interest government-backed savings scheme for girl child education and marriage with Section 80C tax exemption.',
  'Attractive sovereign interest rate (currently ~8.2% p.a.), exempt-exempt-exempt (EEE) tax status, partial withdrawal allowed for higher education at age 18.',
  'https://www.indiapost.gov.in/',
  ARRAY['Birth Certificate of girl child', 'Aadhaar / ID proof of parent or legal guardian', 'Address proof', 'Passport photos of child and guardian'],
  ARRAY['Visit Post Office or authorized commercial bank branch', 'Submit SSY application form with child birth certificate', 'Make initial deposit (minimum ₹250)', 'Passbook issued for ongoing monthly or annual deposits'],
  '2026-01-30',
  '{"all": [{"field": "age", "op": "lte", "value": 10, "label": "Girl child age up to 10 years at account opening"}]}'
)
ON CONFLICT (code) DO UPDATE SET
  title_en = EXCLUDED.title_en,
  summary = EXCLUDED.summary,
  benefits = EXCLUDED.benefits,
  rule = EXCLUDED.rule,
  documents_required = EXCLUDED.documents_required,
  application_steps = EXCLUDED.application_steps,
  last_verified_at = EXCLUDED.last_verified_at;

-- Learning Modules
INSERT INTO learning_modules (lang, category, title, summary, body, quiz) VALUES
(
  'en',
  'Budgeting',
  'The 50/30/20 Rule for Students and Households',
  'Master how to split your income into essentials, lifestyle, and savings.',
  'The 50/30/20 framework is a proven budgeting guideline: Allocate 50% of your net income to Needs (rent, tuition, groceries, mess fees, medicine); 30% to Wants (dining out, entertainment, streaming, travel); and 20% to Savings or Debt repayment (emergency fund, SIP, recurring deposit). For students on a tight stipend, you can adjust this to 60/20/20, ensuring at least a small portion is saved every month.',
  '[{"question": "Under the 50/30/20 rule, which category does mess/canteen food and college tuition belong to?", "options": ["Wants", "Needs", "Savings", "Discretionary"], "correct_index": 1, "explanation": "Essential food, rent, and education tuition are non-negotiable living costs, categorized as Needs."}]'
),
(
  'en',
  'Digital Safety',
  'UPI Security & Cyber Hygiene',
  'Essential rules to safeguard your bank account from UPI scams.',
  '1. PIN Rule: You NEVER need to enter your UPI PIN to RECEIVE money. Entering your PIN always debits funds from your account. 2. QR Code Scams: Never scan a QR code sent over WhatsApp or OLX to receive payment. 3. Verification: Always verify the verified name shown in your UPI app before completing payment. 4. If defrauded, immediately dial the National Cyber Crime Helpline at 1930 and report on cybercrime.gov.in within 24 hours.',
  '[{"question": "Someone claims they are transferring a scholarship prize of ₹5,000 to you and asks you to scan a QR code and enter your UPI PIN. What will happen?", "options": ["You will receive ₹5,000", "Money will be deducted from your bank account", "Nothing will happen", "Your phone will update"], "correct_index": 1, "explanation": "Scanning a QR code and entering your UPI PIN authorizes a payment debit from your account. Legitimate payers never ask you to enter a PIN to receive funds."}]'
),
(
  'en',
  'Fraud Alerts',
  'Beware of Illegal Instant Loan Apps',
  'How to identify predatory lending apps and protect your data.',
  'Many unauthorized instant loan apps lure vulnerable students and citizens with 5-minute loans. Once installed, they steal your phone contacts, private photos, and demand exorbitant interest rates (up to 300% p.a.) with abusive harassment tactics. Legitimate digital lenders must be registered NBFCs or Banks regulated by the RBI. Before borrowing, verify the lending partner on the RBI website (rbi.org.in) and never grant contacts or gallery permissions to loan apps.',
  '[{"question": "Where should you verify if a loan application is authorized and legally regulated?", "options": ["Social media comments", "RBI (Reserve Bank of India) official website", "App Store star ratings", "WhatsApp message"], "correct_index": 1, "explanation": "All legitimate non-banking financial companies (NBFCs) and banks must be registered with and listed on the Reserve Bank of India (RBI) portal."}]'
),
(
  'kn',
  'Budgeting',
  'ಅಗತ್ಯಗಳು vs ಬಯಕೆಗಳು (Needs vs Wants)',
  'ಖರ್ಚುಗಳನ್ನು ನಿಯಂತ್ರಿಸಲು ಮತ್ತು ಉಳಿತಾಯ ಮಾಡಲು ಪ್ರಮುಖ ನಿಯಮಗಳು.',
  'ಹಣಕಾಸು ನಿರ್ವಹಣೆಯ ಮೊದಲ ಹೆಜ್ಜೆ ಎಂದರೆ ಅಗತ್ಯ ಮತ್ತು ಬಯಕೆಗಳ ನಡುವಿನ ವ್ಯತ್ಯಾಸವನ್ನು ತಿಳಿಯುವುದು. ಅಗತ್ಯಗಳು (Needs): ಆಹಾರ, ಕಾಲೇಜು ಶುಲ್ಕ, ವಸತಿ ಬಾಡಿಗೆ, ಔಷಧಿ. ಬಯಕೆಗಳು (Wants): ಹೊಸ ಗ್ಯಾಜೆಟ್‌ಗಳು, ದುಬಾರಿ ಹೋಟೆಲ್ ಊಟ, ಸಿನಿಮಾ. ಯಾವಾಗಲೂ ಅಗತ್ಯಗಳಿಗೆ ಮೊದಲು ಆದ್ಯತೆ ನೀಡಿ, ನಂತರ ಕನಿಷ್ಠ 20% ಉಳಿತಾಯ ಮಾಡಿ, ಉಳಿದ ಹಣವನ್ನು ಬಯಕೆಗಳಿಗೆ ಬಳಸಿ.',
  '[{"question": "ಕೆಳಗಿನವುಗಳಲ್ಲಿ ಯಾವುದು ಅಗತ್ಯ (Need) ಆಗಿದೆ?", "options": ["ಹೊಸ ಐಫೋನ್", "ಕಾಲೇಜು ಪುಸ್ತಕ ಮತ್ತು ಶುಲ್ಕ", "ವಾರಾಂತ್ಯದ ಚಲನಚಿತ್ರ", "ದುಬಾರಿ ಕಾಫಿ"], "correct_index": 1, "explanation": "ಶಿಕ್ಷಣ, ಕಾಲೇಜು ಶುಲ್ಕ ಮತ್ತು ಪುಸ್ತಕಗಳು ಜೀವನದ ಅಗತ್ಯಗಳಾಗಿವೆ."}]'
),
(
  'kn',
  'Digital Safety',
  'ಸುರಕ್ಷಿತ ಯುಪಿಐ (UPI) ಡಿಜಿಟಲ್ ಪಾವತಿ',
  'ಆನ್‌ಲೈನ್ ಹಣಕಾಸು ವಂಚನೆಗಳಿಂದ ರಕ್ಷಣೆ ಪಡೆಯುವುದು ಹೇಗೆ.',
  'ಯುಪಿಐ ಪಿನ್ (UPI PIN) ಕೇವಲ ನಿಮ್ಮ ಖಾತೆಯಿಂದ ಹಣ ಕಳುಹಿಸಲು ಮಾತ್ರ ಬಳಸಲಾಗುತ್ತದೆ. ಯಾರಾದರೂ ಹಣ ಕಳುಹಿಸುತ್ತೇವೆ ಎಂದು ಪಿನ್ ನಮೂದಿಸಲು ಹೇಳಿದರೆ ಅದು ಖಂಡಿತ ವಂಚನೆ! ಅಪರಿಚಿತ QR ಕೋಡ್‌ಗಳನ್ನು ಸ್ಕ್ಯಾನ್ ಮಾಡಬೇಡಿ. ವಂಚನೆ ಸಂಭವಿಸಿದರೆ ತಕ್ಷಣ 1930 ಸೈಬರ್ ಸಹಾಯವಾಣಿಗೆ ಕರೆ ಮಾಡಿ.',
  '[{"question": "ಹಣವನ್ನು ಸ್ವೀಕರಿಸಲು (Receive) ನೀವು UPI PIN ನಮೂದಿಸಬೇಕೇ?", "options": ["ಹೌದು, ಯಾವಾಗಲೂ", "ಇಲ್ಲ, ಎಂದಿಗೂ ಬೇಡ", "ಕೇವಲ ಶನಿವಾರ", "OTP ಬಂದಾಗ ಮಾತ್ರ"], "correct_index": 1, "explanation": "ಹಣವನ್ನು ಸ್ವೀಕರಿಸಲು ಎಂದಿಗೂ UPI PIN ನಮೂದಿಸುವ ಅಗತ್ಯವಿಲ್ಲ."}]'
),
(
  'hi',
  'Budgeting',
  '50/30/20 बजट नियम - छात्रों और परिवारों के लिए',
  'अपनी आय को जरूरतों, चाहतों और बचत में विभाजित करना सीखें।',
  '50/30/20 का नियम बताता है: अपनी कुल मासिक आय का 50% बुनियादी जरूरतों (किराया, राशन, फीस, दवाएं) पर खर्च करें। 30% जीवनशैली की चाहतों (मनोरंजन, बाहर खाना) पर और न्यूनतम 20% आपातकालीन फंड और बचत में रखें। यदि आप छात्र हैं, तो भी प्रति माह एक निश्चित राशि बचाने की आदत डालें।',
  '[{"question": "50/30/20 नियम में 20% हिस्सा किसके लिए निर्धारित है?", "options": ["शॉपिंग", "बचत और आपातकालीन फंड", "सिनेमा", "घूमना-फिरना"], "correct_index": 1, "explanation": "20% हिस्सा हमेशा बचत, आपातकालीन फंड और भविष्य के लक्ष्यों के लिए होना चाहिए."}]'
),
(
  'hi',
  'Digital Safety',
  'सुरक्षित यूपीआई और ऑनलाइन धोखाधड़ी से बचाव',
  'अपने बैंक खाते को ऑनलाइन साइबर अपराधियों से कैसे सुरक्षित रखें।',
  '1. सबसे महत्वपूर्ण नियम: पैसे प्राप्त करने के लिए आपको कभी भी अपना UPI PIN दर्ज करने की आवश्यकता नहीं होती। PIN दर्ज करने का मतलब है आपके खाते से पैसे कटना। 2. किसी अजनबी द्वारा भेजे गए QR कोड को कभी स्कैन न करें। 3. यदि कोई धोखाधड़ी हो, तो तुरंत 1930 डायल करें और cybercrime.gov.in पर रिपोर्ट दर्ज करें।',
  '[{"question": "यदि कोई कहता है कि वह आपको छात्रवृत्ति भेज रहा है और आपसे UPI PIN दर्ज करने को कहता है, तो क्या होगा?", "options": ["खाते में पैसे आएंगे", "आपके बैंक खाते से पैसे कट जाएंगे", "पुरस्कार मिलेगा", "कुछ नहीं होगा"], "correct_index": 1, "explanation": "UPI PIN दर्ज करते ही आपके खाते से पैसे कट जाते हैं। पैसे प्राप्त करने के लिए कभी PIN की आवश्यकता नहीं होती."}]'
);

-- Seed Knowledge Documents for AI Assistant
INSERT INTO knowledge_docs (title, category, content, source_citation) VALUES
(
  'Post-Matric Scholarship Rules and Deadlines',
  'Scholarships',
  'National Scholarship Portal (NSP) and Karnataka State Scholarship Portal (SSP) provide post-matric scholarships for SC, ST, OBC, and EWS students whose family annual income is below ₹2.5 Lakhs (or ₹3 Lakhs for certain Karnataka categories). Verification requires Aadhaar-seeded bank account, caste certificate with RD number, income certificate, and institution e-attestation. Deadlines generally fall between October and January each academic year.',
  'National Scholarship Portal (scholarships.gov.in) & Karnataka SSP'
),
(
  'Emergency Fund Sizing and Allocation',
  'Personal Finance',
  'An emergency fund is a liquid safety buffer to protect individuals and families from unexpected events such as medical crises, laptop repair, sudden job loss, or family emergency. Financial planners recommend keeping 3 to 6 months of mandatory living expenses (rent, food, loan EMIs, utility bills) in high-liquidity instruments such as savings bank accounts or liquid mutual funds, never locked in illiquid assets or volatile equities.',
  'RBI Financial Education Handbook & SEBI Investor Guidelines'
),
(
  'Pradhan Mantri Jan Dhan Yojana Benefits',
  'Government Schemes',
  'PMJDY provides zero balance basic savings bank deposit (BSBD) accounts with no minimum balance penalty. It includes an accidental insurance cover of ₹2 Lakhs on RuPay cards, overdraft facility of up to ₹10,000 for accounts with good transaction history, and direct benefit transfer (DBT) credit for central and state government subsidies and scholarships.',
  'Ministry of Finance, Government of India (pmjdy.gov.in)'
),
(
  'Predatory Loan Apps and RBI Digital Lending Guidelines',
  'Cyber Safety',
  'Under RBI digital lending guidelines, all loan disbursements and repayments must happen directly between the borrower bank account and the regulated entity (Bank/NBFC) without any third-party pass-through account. Loan apps cannot access biometric data, phone contacts, or private photos. Borrowers should never install APKs from outside Google Play Store or borrow from unregistered entities.',
  'Reserve Bank of India Circular on Digital Lending Guidelines'
);
