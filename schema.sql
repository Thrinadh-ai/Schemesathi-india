-- ============================================================================
-- SCHEMESATHI AI - SUPABASE POSTGRESQL SCHEMA
-- Complete database schema and seed data for SchemeSathi AI
-- ============================================================================

-- 1. Create Schemes Table
CREATE TABLE IF NOT EXISTS public.schemes (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    government_level VARCHAR(32) NOT NULL CHECK (government_level IN ('Central', 'State')),
    state_code VARCHAR(32) DEFAULT 'ALL',
    department VARCHAR(255) NOT NULL,
    categories JSONB NOT NULL DEFAULT '[]'::jsonb,
    eligibility_rules JSONB NOT NULL DEFAULT '{}'::jsonb,
    benefits JSONB NOT NULL DEFAULT '{}'::jsonb,
    required_documents JSONB NOT NULL DEFAULT '[]'::jsonb,
    application_steps JSONB NOT NULL DEFAULT '[]'::jsonb,
    official_url TEXT NOT NULL,
    source_url TEXT NOT NULL,
    last_verified_at DATE DEFAULT CURRENT_DATE,
    status VARCHAR(32) DEFAULT 'Active' CHECK (status IN ('Active', 'Discontinued', 'Under Review')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Indexes for fast search & filtering
CREATE INDEX IF NOT EXISTS idx_schemes_gov_level ON public.schemes (government_level);
CREATE INDEX IF NOT EXISTS idx_schemes_state_code ON public.schemes (state_code);
CREATE INDEX IF NOT EXISTS idx_schemes_status ON public.schemes (status);
CREATE INDEX IF NOT EXISTS idx_schemes_categories ON public.schemes USING gin (categories);
CREATE INDEX IF NOT EXISTS idx_schemes_name_trgm ON public.schemes (name);

-- 3. Row Level Security (RLS)
ALTER TABLE public.schemes ENABLE ROW LEVEL SECURITY;

-- Allow anonymous and authenticated users to read scheme details
CREATE POLICY "Allow public read access to active schemes"
    ON public.schemes
    FOR SELECT
    USING (status = 'Active');

-- 4. Sample Seed Data
INSERT INTO public.schemes (
    id, name, description, government_level, state_code, department,
    categories, eligibility_rules, benefits, required_documents, application_steps,
    official_url, source_url, last_verified_at, status
) VALUES
(
    'pm-kisan',
    'PM-KISAN (Pradhan Mantri Kisan Samman Nidhi)',
    'Income support of ₹6,000 per year in three equal installments to all cultivable landholding farmer families across India.',
    'Central',
    'ALL',
    'Ministry of Agriculture & Farmers Welfare',
    '["Agriculture", "Farmers", "Financial Inclusion"]'::jsonb,
    '{"min_age": 18, "farmer_only": true, "max_income": null, "target_groups": ["Farmers"], "notes": "Must be a landholding farmer. Institutional landholders and high-tax payers are excluded."}'::jsonb,
    '{"summary": "₹6,000 per year paid in 3 four-monthly installments of ₹2,000 directly into bank accounts via DBT."}'::jsonb,
    '["Aadhaar Card", "Land ownership documentation / Record of Rights (RoR)", "Active Bank Account linked with Aadhaar", "Mobile Number"]'::jsonb,
    '["Visit the official PM-KISAN portal (pmkisan.gov.in)", "Click on New Farmer Registration", "Enter Aadhaar number and land details", "Submit the application and verify through state revenue officials"]'::jsonb,
    'https://pmkisan.gov.in/',
    'https://www.myscheme.gov.in/schemes/pm-kisan',
    '2025-01-10',
    'Active'
),
(
    'pm-jay',
    'Ayushman Bharat Pradhan Mantri Jan Arogya Yojana (AB-PMJAY)',
    'World''s largest government-financed health insurance scheme providing health cover of up to ₹5 lakh per family per year for secondary and tertiary care hospitalization.',
    'Central',
    'ALL',
    'National Health Authority (NHA), Ministry of Health & Family Welfare',
    '["Healthcare", "Social Welfare"]'::jsonb,
    '{"min_age": 0, "max_income": 300000, "target_groups": ["Economically Weaker Section", "Rural Households", "Urban Occupational Categories"], "notes": "Identified based on SECC 2011 deprivation criteria. Senior citizens aged 70+ also get dedicated coverage irrespective of income."}'::jsonb,
    '{"summary": "Cashless and paperless access to health services up to ₹5 lakh per family per year at empaneled hospitals."}'::jsonb,
    '["Aadhaar Card", "Ration Card / Family ID", "Mobile number for OTP verification"]'::jsonb,
    '["Check eligibility on pmjay.gov.in or visit a nearby Empaneled Health Care Provider (EHCP)", "Verify identity via Ayushman Mitra or kiosk", "Generate Ayushman Card for cashless treatment"]'::jsonb,
    'https://pmjay.gov.in/',
    'https://www.myscheme.gov.in/schemes/pmjay',
    '2025-01-15',
    'Active'
),
(
    'pm-mudra',
    'Pradhan Mantri MUDRA Yojana (PMMY)',
    'Provides collateral-free micro-credit loans up to ₹10 lakh to non-corporate, non-farm small and micro enterprises for manufacturing, trading, and services.',
    'Central',
    'ALL',
    'Department of Financial Services, Ministry of Finance',
    '["Small Business", "Employment", "Financial Inclusion"]'::jsonb,
    '{"min_age": 18, "target_groups": ["Small Business Owners", "Entrepreneurs", "Self Employed", "Job Seekers"], "notes": "Any Indian citizen with a viable business idea or running micro-enterprise."}'::jsonb,
    '{"summary": "Loans in 3 categories: Shishu (up to ₹50,000), Kishore (₹50,000 to ₹5 Lakh), and Tarun (₹5 Lakh to ₹10 Lakh) with affordable interest rates."}'::jsonb,
    '["Proof of Identity (Aadhaar/Voter ID/PAN)", "Proof of Residence", "Proof of Business Address and Enterprise Identity", "Bank Statement (last 6 months)", "Quotation/Estimates for machinery or items to be bought"]'::jsonb,
    '["Prepare your business proposal", "Approach an authorized bank, NBFC, or apply online via UdyamiMitra portal", "Submit loan application along with required KYC and business documents", "Loan sanctions and disbursement into bank account"]'::jsonb,
    'https://www.mudra.org.in/',
    'https://www.myscheme.gov.in/schemes/pmmy',
    '2025-01-05',
    'Active'
),
(
    'post-matric-scholarship',
    'Post-Matric Scholarship for SC/ST/OBC Students',
    'Centrally sponsored scholarship to provide financial support to students from scheduled castes, scheduled tribes, and other backward classes studying at post-secondary or post-matriculation stages.',
    'Central',
    'ALL',
    'Ministry of Social Justice and Empowerment / Ministry of Tribal Affairs',
    '["Education", "Scholarships", "Students"]'::jsonb,
    '{"student_only": true, "max_income": 250000, "target_groups": ["Students", "SC", "ST", "OBC"], "notes": "Enrolled in recognized post-matric course (Class 11, 12, Degree, Diploma, PG) with family annual income under ₹2.5 lakh."}'::jsonb,
    '{"summary": "Maintenance allowance, reimbursement of compulsory non-refundable fees, study tour charges, and thesis typing charges."}'::jsonb,
    '["Student Aadhaar Card", "Caste/Community Certificate", "Income Certificate issued by competent authority", "Previous Academic Marksheets", "Fee Receipt & College Bonafide Certificate", "Student Bank Passbook"]'::jsonb,
    '["Register on National Scholarship Portal (scholarships.gov.in)", "Fill applicant details and select Post-Matric Scholarship Scheme", "Upload required academic and category documents", "Submit online and verify through institute nodal officer"]'::jsonb,
    'https://scholarships.gov.in/',
    'https://www.myscheme.gov.in/schemes/pms-sc',
    '2025-01-12',
    'Active'
),
(
    'pm-ujjwala',
    'Pradhan Mantri Ujjwala Yojana (PMUY 2.0)',
    'Aims to safeguard health of women and children by providing clean cooking fuel (LPG) to adult women members of poor households without any upfront cost.',
    'Central',
    'ALL',
    'Ministry of Petroleum & Natural Gas',
    '["Women & Child", "Social Welfare"]'::jsonb,
    '{"min_age": 18, "gender_only": "Female", "target_groups": ["Women", "Economically Weaker Section", "BPL"], "notes": "Applicant must be an adult woman from a BPL household with no existing LPG connection in the family."}'::jsonb,
    '{"summary": "Deposit-free LPG connection including security deposit for cylinder, pressure regulator, safety hose, and domestic gas consumer card book."}'::jsonb,
    '["Aadhaar Card of applicant and adult family members", "Ration Card proving household composition", "Bank Account Passbook / IFSC", "Self-declaration of family details"]'::jsonb,
    '["Visit nearest LPG distributor (Indane, BharatGas, HP Gas) or apply online at pmuy.gov.in", "Fill Ujjwala application form with family details", "Submit required KYC documents", "Distributor inspects and delivers connection upon approval"]'::jsonb,
    'https://www.pmuy.gov.in/',
    'https://www.myscheme.gov.in/schemes/pmuy',
    '2025-01-20',
    'Active'
),
(
    'atal-pension',
    'Atal Pension Yojana (APY)',
    'A voluntary pension scheme administered by PFRDA aimed at unorganized sector workers, guaranteeing fixed monthly pensions of ₹1,000 to ₹5,000 from age 60.',
    'Central',
    'ALL',
    'Pension Fund Regulatory & Development Authority (PFRDA), Ministry of Finance',
    '["Senior Citizens", "Financial Inclusion", "Social Welfare"]'::jsonb,
    '{"min_age": 18, "max_age": 40, "target_groups": ["Unorganized Sector", "Job Seekers", "Senior Citizens"], "notes": "Must be aged between 18 and 40 years. Taxpayers are not eligible to join APY."}'::jsonb,
    '{"summary": "Guaranteed minimum monthly pension of ₹1,000, ₹2,000, ₹3,000, ₹4,000, or ₹5,000 to subscribers after attaining 60 years of age."}'::jsonb,
    '["Savings Bank Account details", "Aadhaar Card", "Mobile Number linked with bank account"]'::jsonb,
    '["Approach the bank branch or post office where you hold a savings account", "Fill out the APY registration form and choose pension slab", "Authorize auto-debit facility for periodic contribution"]'::jsonb,
    'https://www.npscra.nsdl.co.in/',
    'https://www.myscheme.gov.in/schemes/apy',
    '2025-01-08',
    'Active'
),
(
    'stand-up-india',
    'Stand-Up India Scheme',
    'Facilitates bank loans between ₹10 lakh and ₹1 Crore to at least one Scheduled Caste (SC) or Scheduled Tribe (ST) borrower and at least one woman borrower per bank branch for greenfield enterprises.',
    'Central',
    'ALL',
    'Department of Financial Services, Ministry of Finance',
    '["Small Business", "Women & Child", "Employment"]'::jsonb,
    '{"min_age": 18, "target_groups": ["Women", "SC", "ST", "Small Business Owners"], "notes": "For SC/ST or Women entrepreneurs establishing first-time greenfield business in manufacturing, services, or trading."}'::jsonb,
    '{"summary": "Bank composite loan between ₹10 lakh and ₹100 lakh covering up to 85% of project cost with 7-year repayment window."}'::jsonb,
    '["Identity and Address Proof", "Caste Certificate (if SC/ST)", "Project Report with financial projections", "Partnership Deed or Certificate of Incorporation (if non-individual entity with >=51% holding)", "Bank Statements"]'::jsonb,
    '["Register on Stand-Up Mitra portal (standupmitra.in)", "Fill in applicant profile and business plan", "Portal matches application with lead district managers and participating banks", "Bank conducts appraisal and sanctions loan"]'::jsonb,
    'https://www.standupmitra.in/',
    'https://www.myscheme.gov.in/schemes/suis',
    '2025-01-14',
    'Active'
),
(
    'mgnregs',
    'Mahatma Gandhi National Rural Employment Guarantee Act (MGNREGS)',
    'Enhances livelihood security in rural areas by providing at least 100 days of guaranteed wage employment in a financial year to every rural household whose adult members volunteer to do unskilled manual work.',
    'Central',
    'ALL',
    'Ministry of Rural Development',
    '["Employment", "Social Welfare", "Agriculture"]'::jsonb,
    '{"min_age": 18, "target_groups": ["Rural Households", "Job Seekers", "Economically Weaker Section"], "notes": "Must be a rural resident willing to do unskilled manual work."}'::jsonb,
    '{"summary": "Guaranteed 100 days of manual wage employment per household per year with wages credited directly via DBT."}'::jsonb,
    '["Household photo", "Proof of Residence in Gram Panchayat", "Aadhaar Card", "Bank or Post Office Passbook"]'::jsonb,
    '["Apply for Job Card at local Gram Panchayat office", "Gram Panchayat issues verified Job Card within 15 days", "Submit written application for work whenever needed", "Work assigned within 5 km of village within 15 days of demand"]'::jsonb,
    'https://nrega.nic.in/',
    'https://www.myscheme.gov.in/schemes/mgnregs',
    '2025-01-18',
    'Active'
),
(
    'pmay-g',
    'Pradhan Mantri Awas Yojana - Gramin (PMAY-G)',
    'Aims to provide pucca houses with basic amenities to all houseless households and those households living in kutcha and dilapidated houses in rural areas.',
    'Central',
    'ALL',
    'Ministry of Rural Development',
    '["Housing", "Social Welfare"]'::jsonb,
    '{"target_groups": ["Rural Households", "Economically Weaker Section", "BPL"], "notes": "Identified through SECC 2011 and Awas+ survey. Must not already own a pucca house in India."}'::jsonb,
    '{"summary": "Financial assistance of ₹1,20,000 in plains and ₹1,30,000 in hilly/difficult states for house construction plus 90 days of MGNREGA wages."}'::jsonb,
    '["Aadhaar Card", "Bank Account linked to Aadhaar", "MGNREGA Job Card Number", "Swachh Bharat Mission (SBM) registration number", "Consent form for Aadhaar usage"]'::jsonb,
    '["Beneficiary list finalized by Gram Sabha from SECC / Awas+ list", "Geo-tagging of current house site by village nodal officer", "Direct benefit transfer installments disbursed based on construction stages"]'::jsonb,
    'https://pmayg.nic.in/',
    'https://www.myscheme.gov.in/schemes/pmay-g',
    '2025-01-16',
    'Active'
),
(
    'ap-amma-vodi',
    'Jagananna Amma Vodi',
    'State welfare program by Andhra Pradesh providing annual financial assistance of ₹15,000 to poor mothers or recognized guardians to support schooling of their children from Class 1 to 12.',
    'State',
    'AP',
    'School Education Department, Government of Andhra Pradesh',
    '["Education", "Women & Child", "Students"]'::jsonb,
    '{"state_only": "AP", "max_income": 120000, "target_groups": ["Women", "Students", "Economically Weaker Section"], "notes": "Mother must be resident of Andhra Pradesh, child must have minimum 75% attendance in recognized school/junior college."}'::jsonb,
    '{"summary": "₹15,000 per academic year deposited directly into the bank account of the mother or guardian."}'::jsonb,
    '["Mother''s Aadhaar Card", "Child''s Aadhaar Card", "White Ration Card / Rice Card", "Bank Account details with IFSC", "School Bonafide Certificate with 75% attendance proof"]'::jsonb,
    '["Schools submit student attendance data to educational department", "Village/Ward Volunteer verifies eligibility and household data", "Social audit list displayed at Village Secretariat", "Fund credited directly through DBT"]'::jsonb,
    'https://jaganannaammavodi.ap.gov.in/',
    'https://www.myscheme.gov.in/schemes/jagananna-amma-vodi',
    '2025-01-22',
    'Active'
),
(
    'ts-rythu-bandhu',
    'Rythu Bandhu (Agriculture Investment Support Scheme)',
    'Pioneering initiative of Government of Telangana providing investment support of ₹10,000 per acre per year to land-owning farmers for two agricultural seasons (Kharif and Rabi).',
    'State',
    'TG',
    'Department of Agriculture, Government of Telangana',
    '["Agriculture", "Farmers"]'::jsonb,
    '{"state_only": "TG", "farmer_only": true, "target_groups": ["Farmers"], "notes": "Must own agricultural land in Telangana registered with Pattadar Passbook."}'::jsonb,
    '{"summary": "Financial grant of ₹5,000 per acre per season (total ₹10,000 per acre per year) directly transferred to farmer accounts."}'::jsonb,
    '["Pattadar Dharani Passbook", "Aadhaar Card", "Active Bank Account linked to Aadhaar", "Land revenue records"]'::jsonb,
    '["Verify land registration on Dharani portal", "Agriculture Extension Officer (AEO) verifies pattadar details", "DBT transfer directly to the farmer''s linked bank account"]'::jsonb,
    'https://rythubandhu.telangana.gov.in/',
    'https://telangana.gov.in/services/rythu-bandhu/',
    '2025-01-19',
    'Active'
),
(
    'sukanya-samriddhi',
    'Sukanya Samriddhi Yojana (SSY)',
    'Government-backed savings scheme launched as part of Beti Bachao Beti Padhao campaign, offering high interest rates and tax exemptions under Section 80C for the future education and marriage of girl children.',
    'Central',
    'ALL',
    'Department of Economic Affairs, Ministry of Finance',
    '["Women & Child", "Financial Inclusion", "Education"]'::jsonb,
    '{"max_age": 10, "gender_only": "Female", "target_groups": ["Women", "Girl Child"], "notes": "Account can be opened by parents/legal guardian for a girl child from birth up to 10 years of age (maximum two girl children per family)."}'::jsonb,
    '{"summary": "Government-notified quarterly compounding interest (currently ~8.2% p.a.), exempt under EEE tax regime (Section 80C)."}'::jsonb,
    '["Birth Certificate of the girl child", "Identity Proof of parent/guardian (Aadhaar/PAN)", "Address Proof of parent/guardian", "Passport size photograph of child and parent"]'::jsonb,
    '["Visit nearest Post Office or authorized commercial bank branch", "Submit SSY account opening form along with child birth certificate and guardian KYC", "Deposit initial amount (minimum ₹250)", "Passbook issued upon account opening"]'::jsonb,
    'https://www.indiapost.gov.in/Financial/Pages/Content/SSY.aspx',
    'https://www.myscheme.gov.in/schemes/ssy',
    '2025-01-25',
    'Active'
);
