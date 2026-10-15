#!/usr/bin/env python3
"""
SchemeSathi AI - Backend Server
Your Guide to Government Schemes.
Full-stack REST API for scheme discovery, rule-based eligibility evaluation, and grounded AI assistant.
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("schemesathi")

# Application Initialization
app = Flask(__name__, static_folder=".", static_url_path="")
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024  # 1 MB request ceiling

# Secure CORS Setup
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "*")
if FRONTEND_ORIGIN == "*":
    CORS(app, resources={r"/api/*": {"origins": "*"}})
else:
    origins = [o.strip() for o in FRONTEND_ORIGIN.split(",") if o.strip()]
    CORS(app, resources={r"/api/*": {"origins": origins}})

# Environment Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
AI_API_KEY = os.getenv("AI_API_KEY", "").strip()
AI_MODEL = os.getenv("AI_MODEL", "gpt-4o-mini").strip()
AI_API_BASE_URL = os.getenv("AI_API_BASE_URL", "https://api.openai.com/v1").strip()
PORT = int(os.getenv("PORT", "5000"))

# State and Category Master Data
INDIAN_STATES = [
    {"code": "ALL", "name": "All India / Central"},
    {"code": "AP", "name": "Andhra Pradesh"},
    {"code": "AR", "name": "Arunachal Pradesh"},
    {"code": "AS", "name": "Assam"},
    {"code": "BR", "name": "Bihar"},
    {"code": "CG", "name": "Chhattisgarh"},
    {"code": "GA", "name": "Goa"},
    {"code": "GJ", "name": "Gujarat"},
    {"code": "HR", "name": "Haryana"},
    {"code": "HP", "name": "Himachal Pradesh"},
    {"code": "JH", "name": "Jharkhand"},
    {"code": "KA", "name": "Karnataka"},
    {"code": "KL", "name": "Kerala"},
    {"code": "MP", "name": "Madhya Pradesh"},
    {"code": "MH", "name": "Maharashtra"},
    {"code": "MN", "name": "Manipur"},
    {"code": "ML", "name": "Meghalaya"},
    {"code": "MZ", "name": "Mizoram"},
    {"code": "NL", "name": "Nagaland"},
    {"code": "OD", "name": "Odisha"},
    {"code": "PB", "name": "Punjab"},
    {"code": "RJ", "name": "Rajasthan"},
    {"code": "SK", "name": "Sikkim"},
    {"code": "TN", "name": "Tamil Nadu"},
    {"code": "TG", "name": "Telangana"},
    {"code": "TR", "name": "Tripura"},
    {"code": "UP", "name": "Uttar Pradesh"},
    {"code": "UK", "name": "Uttarakhand"},
    {"code": "WB", "name": "West Bengal"},
    {"code": "DL", "name": "Delhi (NCT)"},
    {"code": "JK", "name": "Jammu & Kashmir"},
    {"code": "LA", "name": "Ladakh"},
    {"code": "PY", "name": "Puducherry"},
    {"code": "CH", "name": "Chandigarh"}
]

CATEGORIES_MASTER = [
    "Agriculture",
    "Education",
    "Scholarships",
    "Healthcare",
    "Women & Child",
    "Social Welfare",
    "Small Business",
    "Employment",
    "Financial Inclusion",
    "Housing",
    "Senior Citizens",
    "Farmers",
    "Students"
]

# Verified Demo Dataset (Grounded Public Information)
DEMO_SCHEMES: List[Dict[str, Any]] = [
    {
        "id": "pm-kisan",
        "name": "PM-KISAN (Pradhan Mantri Kisan Samman Nidhi)",
        "description": "Income support scheme providing ₹6,000 per year in three equal four-monthly installments of ₹2,000 directly to landholding farmer families across India.",
        "government_level": "Central",
        "state_code": "ALL",
        "department": "Ministry of Agriculture & Farmers Welfare",
        "categories": ["Agriculture", "Farmers", "Financial Inclusion"],
        "eligibility_rules": {
            "min_age": 18,
            "max_age": None,
            "farmer_only": True,
            "student_only": False,
            "max_income": None,
            "gender": None,
            "target_groups": ["Farmers"],
            "notes": "Farmer family owning cultivable land. High net-worth tax payers, institutional landholders, and serving/retired government officers are excluded."
        },
        "benefits": {
            "summary": "₹6,000 per year transferred directly via Direct Benefit Transfer (DBT) in 3 equal installments of ₹2,000.",
            "mode": "Direct Bank Account Transfer"
        },
        "required_documents": [
            "Aadhaar Card",
            "Land Ownership Proof (RoR / Khasra / Khatoni)",
            "Bank Account Passbook (Aadhaar linked)",
            "Active Mobile Number"
        ],
        "application_steps": [
            "Visit the official PM-KISAN portal (pmkisan.gov.in).",
            "Go to 'Farmers Corner' and select 'New Farmer Registration'.",
            "Enter Aadhaar number and state, then complete the landholding details.",
            "Submit application. The state revenue department verifies land records before DBT approval."
        ],
        "official_url": "https://pmkisan.gov.in/",
        "source_url": "https://www.myscheme.gov.in/schemes/pm-kisan",
        "last_verified_at": "2025-01-10",
        "status": "Active"
    },
    {
        "id": "pm-jay",
        "name": "Ayushman Bharat Pradhan Mantri Jan Arogya Yojana (AB-PMJAY)",
        "description": "National flagship public health insurance scheme providing health coverage of up to ₹5 lakh per family per year for secondary and tertiary care hospitalization.",
        "government_level": "Central",
        "state_code": "ALL",
        "department": "National Health Authority, Ministry of Health and Family Welfare",
        "categories": ["Healthcare", "Social Welfare"],
        "eligibility_rules": {
            "min_age": 0,
            "max_age": None,
            "farmer_only": False,
            "student_only": False,
            "max_income": 300000,
            "gender": None,
            "target_groups": ["Economically Weaker Section", "Rural Deprived Households", "Urban Workers", "Senior Citizens"],
            "notes": "Families identified via SECC 2011 deprivation criteria. All senior citizens aged 70 years and above are covered under Ayushman Vay Vandana regardless of income."
        },
        "benefits": {
            "summary": "Up to ₹5,00,000 cashless and paperless hospitalization treatment per family per year at public and empaneled private hospitals.",
            "mode": "Cashless Hospital Treatment"
        },
        "required_documents": [
            "Aadhaar Card",
            "Ration Card or State Family ID",
            "Active Mobile Number"
        ],
        "application_steps": [
            "Check eligibility on pmjay.gov.in or visit the nearest Common Service Centre (CSC) / Empaneled Hospital.",
            "Meet the Ayushman Mitra at the hospital reception.",
            "Complete biometric e-KYC using Aadhaar.",
            "Receive your Ayushman Bharat Golden Card for cashless treatment."
        ],
        "official_url": "https://pmjay.gov.in/",
        "source_url": "https://www.myscheme.gov.in/schemes/pmjay",
        "last_verified_at": "2025-01-15",
        "status": "Active"
    },
    {
        "id": "pm-mudra",
        "name": "Pradhan Mantri MUDRA Yojana (PMMY)",
        "description": "Provides formal collateral-free micro-credit loans up to ₹10 lakh to non-corporate, non-farm small and micro enterprises across manufacturing, services, and trading.",
        "government_level": "Central",
        "state_code": "ALL",
        "department": "Department of Financial Services, Ministry of Finance",
        "categories": ["Small Business", "Employment", "Financial Inclusion"],
        "eligibility_rules": {
            "min_age": 18,
            "max_age": 65,
            "farmer_only": False,
            "student_only": False,
            "max_income": None,
            "gender": None,
            "target_groups": ["Small Business Owners", "Entrepreneurs", "Self Employed", "Job Seekers"],
            "notes": "Indian citizens running or starting a non-farm income generating micro-enterprise."
        },
        "benefits": {
            "summary": "Collateral-free loans in 3 tiers: Shishu (up to ₹50,000), Kishore (₹50,000 - ₹5 Lakh), Tarun (₹5 Lakh - ₹10 Lakh) with reasonable interest rates.",
            "mode": "Institutional Bank Loan"
        },
        "required_documents": [
            "Identity Proof (Aadhaar / Voter ID / PAN)",
            "Address Proof (Electricity Bill / Ration Card)",
            "Business Identity & Registration Proof (Udyam / Shop Act)",
            "Bank Statements for the last 6 months",
            "Project Report / Quotation of Machinery"
        ],
        "application_steps": [
            "Formulate a business plan and calculate machinery/working capital requirements.",
            "Apply via the UdyamiMitra portal (udyamimitra.in) or visit any commercial bank/RRB/NBFC.",
            "Submit the loan application form with business documentation.",
            "Upon credit appraisal, loan is sanctioned and disbursed directly to supplier/account."
        ],
        "official_url": "https://www.mudra.org.in/",
        "source_url": "https://www.myscheme.gov.in/schemes/pmmy",
        "last_verified_at": "2025-01-05",
        "status": "Active"
    },
    {
        "id": "post-matric-scholarship",
        "name": "Post-Matric Scholarship Scheme for SC/ST/OBC Students",
        "description": "Centrally sponsored scholarship providing comprehensive financial aid to meritorious and needy students pursuing post-matriculation or post-secondary education.",
        "government_level": "Central",
        "state_code": "ALL",
        "department": "Ministry of Social Justice and Empowerment / Ministry of Tribal Affairs",
        "categories": ["Education", "Scholarships", "Students"],
        "eligibility_rules": {
            "min_age": 15,
            "max_age": 35,
            "farmer_only": False,
            "student_only": True,
            "max_income": 250000,
            "gender": None,
            "target_groups": ["Students", "SC", "ST", "OBC"],
            "notes": "Must be enrolled in recognized post-secondary course (Class 11, 12, ITI, Diploma, Degree, PG). Total annual parental income cannot exceed ₹2,50,000."
        },
        "benefits": {
            "summary": "Full reimbursement of compulsory non-refundable college fees plus monthly maintenance allowance directly credited to student's bank account.",
            "mode": "Direct Benefit Transfer"
        },
        "required_documents": [
            "Student Aadhaar Card",
            "Community / Caste Certificate issued by revenue authority",
            "Current Financial Year Family Income Certificate",
            "Marksheet of previous qualifying examination",
            "College Bonafide Certificate & Fee Receipt",
            "Student Bank Account Passbook"
        ],
        "application_steps": [
            "Register on National Scholarship Portal (scholarships.gov.in).",
            "Select State and Community category (SC/ST/OBC).",
            "Fill academic details, upload caste and income certificates.",
            "Submit online; institute verifies records, followed by state welfare officer approval."
        ],
        "official_url": "https://scholarships.gov.in/",
        "source_url": "https://www.myscheme.gov.in/schemes/pms-sc",
        "last_verified_at": "2025-01-12",
        "status": "Active"
    },
    {
        "id": "pm-ujjwala",
        "name": "Pradhan Mantri Ujjwala Yojana (PMUY 2.0)",
        "description": "Empowers women and safeguards family health by providing deposit-free LPG cooking gas connections to adult women from economically disadvantaged households.",
        "government_level": "Central",
        "state_code": "ALL",
        "department": "Ministry of Petroleum and Natural Gas",
        "categories": ["Women & Child", "Social Welfare"],
        "eligibility_rules": {
            "min_age": 18,
            "max_age": None,
            "farmer_only": False,
            "student_only": False,
            "max_income": 150000,
            "gender": "Female",
            "target_groups": ["Women", "Economically Weaker Section", "BPL"],
            "notes": "Applicant must be an adult female member of a BPL/poor household without any existing domestic LPG connection in the family."
        },
        "benefits": {
            "summary": "Free LPG connection with zero security deposit for cylinder and regulator, plus free first refill and hotplate (stove).",
            "mode": "In-kind Hardware + Subsidy"
        },
        "required_documents": [
            "Aadhaar Card of the applicant woman and adult family members",
            "Ration card or household document confirming family composition",
            "Bank Account Passbook (linked with Aadhaar)",
            "Self-declaration / 14-point declaration"
        ],
        "application_steps": [
            "Submit application online at pmuy.gov.in or directly at an authorized local LPG distributor.",
            "Provide family KYC documents and bank details.",
            "Oil Marketing Company (OMC) performs deduplication checks.",
            "Connection is issued and installed at the beneficiary home."
        ],
        "official_url": "https://www.pmuy.gov.in/",
        "source_url": "https://www.myscheme.gov.in/schemes/pmuy",
        "last_verified_at": "2025-01-20",
        "status": "Active"
    },
    {
        "id": "atal-pension",
        "name": "Atal Pension Yojana (APY)",
        "description": "Government-backed social security pension scheme administered by PFRDA guaranteeing monthly pensions between ₹1,000 and ₹5,000 for unorganized workers upon reaching age 60.",
        "government_level": "Central",
        "state_code": "ALL",
        "department": "Pension Fund Regulatory and Development Authority (PFRDA)",
        "categories": ["Senior Citizens", "Financial Inclusion", "Social Welfare"],
        "eligibility_rules": {
            "min_age": 18,
            "max_age": 40,
            "farmer_only": False,
            "student_only": False,
            "max_income": None,
            "gender": None,
            "target_groups": ["Unorganized Sector", "Job Seekers", "Senior Citizens"],
            "notes": "Subscribers must be aged between 18 and 40 years. Taxpayers are not eligible to enroll in APY."
        },
        "benefits": {
            "summary": "Guaranteed lifetime monthly pension of ₹1,000, ₹2,000, ₹3,000, ₹4,000, or ₹5,000 starting from 60 years of age.",
            "mode": "Monthly Bank Pension"
        },
        "required_documents": [
            "Savings Bank Account details",
            "Aadhaar Card",
            "Active Mobile Number linked with bank account"
        ],
        "application_steps": [
            "Visit the bank branch where you have a savings account or access net-banking APY section.",
            "Fill out the APY registration form and select the desired pension amount.",
            "Set up automatic debit instruction for monthly/quarterly contribution.",
            "Receive PRAN (Permanent Retirement Account Number) card confirmation."
        ],
        "official_url": "https://www.npscra.nsdl.co.in/",
        "source_url": "https://www.myscheme.gov.in/schemes/apy",
        "last_verified_at": "2025-01-08",
        "status": "Active"
    },
    {
        "id": "stand-up-india",
        "name": "Stand-Up India Scheme",
        "description": "Facilitates bank loans between ₹10 lakh and ₹1 Crore to SC/ST borrowers and women borrowers for setting up greenfield enterprises in manufacturing, services, or trading.",
        "government_level": "Central",
        "state_code": "ALL",
        "department": "Department of Financial Services, Ministry of Finance",
        "categories": ["Small Business", "Women & Child", "Employment"],
        "eligibility_rules": {
            "min_age": 18,
            "max_age": None,
            "farmer_only": False,
            "student_only": False,
            "max_income": None,
            "gender": None,
            "target_groups": ["Women", "SC", "ST", "Small Business Owners"],
            "notes": "Borrower must be an SC/ST or Woman entrepreneur. Enterprise must be a first-time greenfield venture. If non-individual, 51% stake must be held by SC/ST or Woman."
        },
        "benefits": {
            "summary": "Composite loan (term loan + working capital) between ₹10 lakh and ₹100 lakh covering up to 85% of total project cost.",
            "mode": "Commercial Bank Term Loan"
        },
        "required_documents": [
            "Identity and Address Proof (Aadhaar / Voter ID / Passport)",
            "Caste Certificate (for SC/ST applicants)",
            "Detailed Project Report (DPR) with financial cashflow projections",
            "Enterprise proof of registration / Partnership Deed / MoA",
            "Bank account statements for the past 6 months"
        ],
        "application_steps": [
            "Prepare detailed project report and estimate financial requirements.",
            "Register on the Stand-Up Mitra portal (standupmitra.in).",
            "Connect with Lead District Manager or directly with bank branch.",
            "Application appraisal and loan sanction within scheduled timeframe."
        ],
        "official_url": "https://www.standupmitra.in/",
        "source_url": "https://www.myscheme.gov.in/schemes/suis",
        "last_verified_at": "2025-01-14",
        "status": "Active"
    },
    {
        "id": "mgnregs",
        "name": "Mahatma Gandhi National Rural Employment Guarantee Scheme (MGNREGS)",
        "description": "Legal guarantee providing at least 100 days of wage employment in a financial year to every rural household whose adult members volunteer to do unskilled manual work.",
        "government_level": "Central",
        "state_code": "ALL",
        "department": "Ministry of Rural Development",
        "categories": ["Employment", "Social Welfare", "Agriculture"],
        "eligibility_rules": {
            "min_age": 18,
            "max_age": None,
            "farmer_only": False,
            "student_only": False,
            "max_income": None,
            "gender": None,
            "target_groups": ["Rural Households", "Job Seekers", "Economically Weaker Section"],
            "notes": "Must reside in rural areas and be willing to perform unskilled manual public works."
        },
        "benefits": {
            "summary": "Guaranteed 100 days of paid wage employment per household per year. Wages notified annually per state and disbursed directly via DBT.",
            "mode": "Direct Wage Transfer"
        },
        "required_documents": [
            "Applicant Photographs",
            "Proof of Residence in Gram Panchayat jurisdiction",
            "Aadhaar Card",
            "Bank or Post Office Savings Passbook"
        ],
        "application_steps": [
            "Apply in writing or orally to Gram Panchayat for a Job Card.",
            "Gram Panchayat conducts verification and issues Job Card within 15 days.",
            "Beneficiary submits demand for work.",
            "Work allocated within 5 km of village within 15 days of demand, or unemployment allowance is payable."
        ],
        "official_url": "https://nrega.nic.in/",
        "source_url": "https://www.myscheme.gov.in/schemes/mgnregs",
        "last_verified_at": "2025-01-18",
        "status": "Active"
    },
    {
        "id": "pmay-g",
        "name": "Pradhan Mantri Awas Yojana - Gramin (PMAY-G)",
        "description": "Provides financial assistance to houseless rural families and those living in kutcha or dilapidated houses to construct a durable pucca house with basic amenities.",
        "government_level": "Central",
        "state_code": "ALL",
        "department": "Ministry of Rural Development",
        "categories": ["Housing", "Social Welfare"],
        "eligibility_rules": {
            "min_age": 18,
            "max_age": None,
            "farmer_only": False,
            "student_only": False,
            "max_income": 200000,
            "gender": None,
            "target_groups": ["Rural Households", "Economically Weaker Section", "BPL"],
            "notes": "Families with no pucca house identified through SECC 2011 and Awas+ surveys. Excludes households with motorized vehicles, mechanized agricultural equipment, or government employees."
        },
        "benefits": {
            "summary": "Unit assistance of ₹1.20 lakh in plains and ₹1.30 lakh in hilly/difficult areas, plus 90-95 days of unskilled labor wages under MGNREGA.",
            "mode": "Stage-wise Direct Benefit Transfer"
        },
        "required_documents": [
            "Aadhaar Card",
            "Bank Account details linked to Aadhaar",
            "MGNREGA Job Card Number",
            "Swachh Bharat Mission (SBM) ID",
            "Geo-tagged photograph of current kutcha house site"
        ],
        "application_steps": [
            "Beneficiary selection is based on verified Awas+ deprivation priority list.",
            "Gram Sabha scrutinizes and approves the verified priority list.",
            "Nodal officer takes geo-tagged geo-photos at pre-construction, plinth, and lintel levels.",
            "Financial installments transferred stage-by-stage directly into beneficiary bank account."
        ],
        "official_url": "https://pmayg.nic.in/",
        "source_url": "https://www.myscheme.gov.in/schemes/pmay-g",
        "last_verified_at": "2025-01-16",
        "status": "Active"
    },
    {
        "id": "ap-amma-vodi",
        "name": "Jagananna Amma Vodi",
        "description": "State welfare scheme by Andhra Pradesh providing annual financial assistance of ₹15,000 to eligible poor mothers or recognized guardians to educate their school-going children.",
        "government_level": "State",
        "state_code": "AP",
        "department": "School Education Department, Government of Andhra Pradesh",
        "categories": ["Education", "Women & Child", "Students"],
        "eligibility_rules": {
            "min_age": 18,
            "max_age": None,
            "state_only": "AP",
            "farmer_only": False,
            "student_only": False,
            "max_income": 120000,
            "gender": "Female",
            "target_groups": ["Women", "Students", "Economically Weaker Section"],
            "notes": "Mother/guardian must reside in Andhra Pradesh with annual family income below ₹1.2 Lakh (rural) or ₹1.44 Lakh (urban). Child must maintain minimum 75% school attendance."
        },
        "benefits": {
            "summary": "₹15,000 credited annually into the bank account of the mother/guardian to support schooling from Class 1 to 12.",
            "mode": "Direct Benefit Transfer"
        },
        "required_documents": [
            "Mother's Aadhaar Card",
            "Child's Aadhaar Card",
            "White Ration Card / Rice Card",
            "Active Bank Account Passbook (Mother's account)",
            "School Bonafide Certificate with attendance record"
        ],
        "application_steps": [
            "School Headmasters submit student attendance and demographic records.",
            "Village / Ward Secretariat volunteers verify family income and residence.",
            "Provisional beneficiary list displayed for social audit at Village Secretariat.",
            "Final approved funds deposited directly into the mother's account."
        ],
        "official_url": "https://jaganannaammavodi.ap.gov.in/",
        "source_url": "https://www.myscheme.gov.in/schemes/jagananna-amma-vodi",
        "last_verified_at": "2025-01-22",
        "status": "Active"
    },
    {
        "id": "ts-rythu-bandhu",
        "name": "Rythu Bandhu (Agriculture Investment Support Scheme)",
        "description": "Government of Telangana initiative providing seasonal investment support to land-owning farmers for purchasing inputs like seeds, fertilizers, and field preparation.",
        "government_level": "State",
        "state_code": "TG",
        "department": "Department of Agriculture, Government of Telangana",
        "categories": ["Agriculture", "Farmers"],
        "eligibility_rules": {
            "min_age": 18,
            "max_age": None,
            "state_only": "TG",
            "farmer_only": True,
            "student_only": False,
            "max_income": None,
            "gender": None,
            "target_groups": ["Farmers"],
            "notes": "Farmer must own agricultural land in Telangana registered with Pattadar Dharani passbook."
        },
        "benefits": {
            "summary": "₹10,000 per acre per year (₹5,000 per acre each for Kharif and Rabi seasons) directly paid to farmer bank accounts.",
            "mode": "Direct Benefit Transfer"
        },
        "required_documents": [
            "Pattadar Passbook / Dharani Record",
            "Aadhaar Card",
            "Active Aadhaar-linked Bank Account details",
            "Mobile number registered with Dharani"
        ],
        "application_steps": [
            "Verify agricultural land registration on Dharani portal.",
            "Submit bank details to Agriculture Extension Officer (AEO) of the revenue cluster.",
            "Data verified and uploaded to Treasury portal.",
            "Amount credited directly to farmer's bank account before sowing seasons."
        ],
        "official_url": "https://rythubandhu.telangana.gov.in/",
        "source_url": "https://telangana.gov.in/services/rythu-bandhu/",
        "last_verified_at": "2025-01-19",
        "status": "Active"
    },
    {
        "id": "sukanya-samriddhi",
        "name": "Sukanya Samriddhi Yojana (SSY)",
        "description": "Government-backed high-interest savings scheme under Beti Bachao Beti Padhao campaign ensuring financial independence and funding higher education/marriage for girl children.",
        "government_level": "Central",
        "state_code": "ALL",
        "department": "Department of Economic Affairs, Ministry of Finance",
        "categories": ["Women & Child", "Financial Inclusion", "Education"],
        "eligibility_rules": {
            "min_age": 0,
            "max_age": 10,
            "farmer_only": False,
            "student_only": False,
            "max_income": None,
            "gender": "Female",
            "target_groups": ["Women", "Girl Child"],
            "notes": "Account opened by biological parents or legal guardians for a girl child aged 10 or below (maximum 2 accounts per family)."
        },
        "benefits": {
            "summary": "High guaranteed compounding interest (~8.2% p.a.), exempt under Section 80C with full tax exemption on maturity proceeds (EEE tax status).",
            "mode": "Post Office / Bank Savings"
        },
        "required_documents": [
            "Birth Certificate of the girl child",
            "Identity Proof of Parent / Guardian (Aadhaar / PAN)",
            "Address Proof of Parent / Guardian",
            "Passport size photos of child and guardian"
        ],
        "application_steps": [
            "Collect SSY account opening form at nearest Post Office or participating bank.",
            "Fill applicant details and attach child birth certificate and guardian KYC.",
            "Deposit initial account opening amount (minimum ₹250).",
            "Receive passbook with account number."
        ],
        "official_url": "https://www.indiapost.gov.in/Financial/Pages/Content/SSY.aspx",
        "source_url": "https://www.myscheme.gov.in/schemes/ssy",
        "last_verified_at": "2025-01-25",
        "status": "Active"
    }
]

# Database Access Layer
class DatabaseManager:
    """Manages connection to Supabase or falls back cleanly to verified Demo Dataset."""
    def __init__(self):
        self.supabase_client = None
        self.mode = "demo"
        if SUPABASE_URL and SUPABASE_KEY:
            try:
                from supabase import create_client
                self.supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
                self.mode = "supabase"
                logger.info("Connected to Supabase PostgreSQL database.")
            except Exception as e:
                logger.warning(f"Failed to initialize Supabase client: {e}. Falling back to Demo Mode.")
                self.mode = "demo"
        else:
            logger.info("Supabase credentials not configured. Running in high-fidelity Demo Mode.")

    def get_all_schemes(self) -> List[Dict[str, Any]]:
        if self.mode == "supabase" and self.supabase_client:
            try:
                response = self.supabase_client.table("schemes").select("*").eq("status", "Active").execute()
                if response.data and len(response.data) > 0:
                    return response.data
            except Exception as e:
                logger.error(f"Error querying Supabase: {e}. Falling back to local demo dataset.")
        return DEMO_SCHEMES

    def get_scheme_by_id(self, scheme_id: str) -> Optional[Dict[str, Any]]:
        schemes = self.get_all_schemes()
        for s in schemes:
            if s.get("id") == scheme_id:
                return s
        return None

db_manager = DatabaseManager()

# Helper Response Formatter
def api_response(data: Any = None, message: str = "Request completed successfully", success: bool = True, status_code: int = 200):
    return jsonify({
        "success": success,
        "message": message,
        "data": data if data is not None else []
    }), status_code

# Error Handlers
@app.errorhandler(400)
def bad_request(error):
    return api_response(data=None, message=str(error.description) if hasattr(error, "description") else "Bad request", success=False, status_code=400)

@app.errorhandler(404)
def not_found(error):
    return api_response(data=None, message="Requested resource was not found", success=False, status_code=404)

@app.errorhandler(405)
def method_not_allowed(error):
    return api_response(data=None, message="Method not allowed on this endpoint", success=False, status_code=405)

@app.errorhandler(413)
def request_entity_too_large(error):
    return api_response(data=None, message="Payload exceeds size limit (max 1MB)", success=False, status_code=413)

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return api_response(data=None, message="An internal server error occurred. Please try again later.", success=False, status_code=500)

# Routes

@app.route("/", methods=["GET"])
def serve_frontend_index():
    """Serves the frontend single-page application when deployed together."""
    return send_from_directory(".", "index.html")

@app.route("/<path:path>", methods=["GET"])
def serve_frontend_assets(path):
    """Serves frontend static assets (CSS, JS, etc.)."""
    if os.path.exists(path) and not path.startswith("server.py") and not path.startswith(".env"):
        return send_from_directory(".", path)
    return send_from_directory(".", "index.html")

@app.route("/api/health", methods=["GET"])
def health_check():
    """System health check and diagnostic information."""
    return api_response(
        data={
            "status": "healthy",
            "service": "SchemeSathi AI",
            "version": "1.0.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "database_mode": db_manager.mode,
            "ai_configured": bool(AI_API_KEY),
            "total_schemes": len(db_manager.get_all_schemes())
        },
        message="System operating normally"
    )

@app.route("/api/categories", methods=["GET"])
def get_categories():
    """Returns available categories with scheme counts."""
    schemes = db_manager.get_all_schemes()
    cat_counts: Dict[str, int] = {}
    for c in CATEGORIES_MASTER:
        cat_counts[c] = 0

    for s in schemes:
        cats = s.get("categories", [])
        if isinstance(cats, list):
            for c in cats:
                cat_counts[c] = cat_counts.get(c, 0) + 1

    result = [{"name": cat, "count": count} for cat, count in sorted(cat_counts.items(), key=lambda x: -x[1])]
    return api_response(data=result, message="Categories retrieved successfully")

@app.route("/api/states", methods=["GET"])
def get_states():
    """Returns list of supported Indian States and Union Territories."""
    return api_response(data=INDIAN_STATES, message="States retrieved successfully")

@app.route("/api/schemes", methods=["GET"])
def get_schemes():
    """
    Search and filter schemes by query, category, state, level, and beneficiary group.
    Filtering performed on backend.
    """
    q = request.args.get("q", "").strip().lower()
    category = request.args.get("category", "").strip().lower()
    state = request.args.get("state", "").strip().upper()
    level = request.args.get("level", "").strip().capitalize()
    beneficiary = request.args.get("beneficiary", "").strip().lower()

    schemes = db_manager.get_all_schemes()
    filtered: List[Dict[str, Any]] = []

    for s in schemes:
        # Search query matching (name, description, department, categories)
        if q:
            name = s.get("name", "").lower()
            desc = s.get("description", "").lower()
            dept = s.get("department", "").lower()
            cats = " ".join([c.lower() for c in s.get("categories", [])])
            if q not in name and q not in desc and q not in dept and q not in cats:
                continue

        # Level filter (Central / State)
        if level and level in ["Central", "State"]:
            if s.get("government_level") != level:
                continue

        # State filter
        if state and state != "ALL":
            # State-specific schemes must match the state; central schemes apply nationwide
            s_state = s.get("state_code", "ALL")
            if s_state != "ALL" and s_state != state:
                continue

        # Category filter
        if category:
            cats = [c.lower() for c in s.get("categories", [])]
            if not any(category in c for c in cats):
                continue

        # Beneficiary filter
        if beneficiary:
            target_groups = [g.lower() for g in s.get("eligibility_rules", {}).get("target_groups", [])]
            cats = [c.lower() for c in s.get("categories", [])]
            if not any(beneficiary in g for g in target_groups) and not any(beneficiary in c for c in cats):
                continue

        filtered.append(s)

    return api_response(
        data=filtered,
        message=f"Found {len(filtered)} scheme(s) matching your criteria"
    )

@app.route("/api/schemes/<scheme_id>", methods=["GET"])
def get_scheme_detail(scheme_id: str):
    """Returns complete verified details for a specific scheme."""
    scheme = db_manager.get_scheme_by_id(scheme_id)
    if not scheme:
        return api_response(
            data=None,
            message=f"Scheme with ID '{scheme_id}' was not found",
            success=False,
            status_code=404
        )
    return api_response(data=scheme, message="Scheme details retrieved successfully")

@app.route("/api/eligibility", methods=["POST"])
def evaluate_eligibility():
    """
    Evaluates applicant inputs against verified scheme rules.
    Explains which criteria match, which are not satisfied, and which remain unknown.
    Distinguishes:
    - 'Potentially eligible'
    - 'Not eligible based on available rules'
    - 'Insufficient information'
    Never guarantees government approval.
    """
    if not request.is_json:
        return api_response(data=None, message="Request payload must be valid JSON", success=False, status_code=400)

    body = request.get_json() or {}

    # Validate inputs
    age_raw = body.get("age")
    income_raw = body.get("income")
    state = str(body.get("state", "ALL")).strip().upper()
    gender = body.get("gender")
    is_student = body.get("is_student")
    is_farmer = body.get("is_farmer")
    category = body.get("beneficiary_category")
    occupation = body.get("occupation", "").strip().lower()

    age: Optional[int] = None
    if age_raw is not None and str(age_raw).strip() != "":
        try:
            age = int(age_raw)
            if age < 0 or age > 125:
                return api_response(data=None, message="Age must be between 0 and 125 years", success=False, status_code=400)
        except ValueError:
            return api_response(data=None, message="Invalid age format. Please provide a whole number.", success=False, status_code=400)

    income: Optional[float] = None
    if income_raw is not None and str(income_raw).strip() != "":
        try:
            income = float(income_raw)
            if income < 0:
                return api_response(data=None, message="Annual income cannot be negative", success=False, status_code=400)
        except ValueError:
            return api_response(data=None, message="Invalid annual income format.", success=False, status_code=400)

    schemes = db_manager.get_all_schemes()
    evaluations: List[Dict[str, Any]] = []

    for s in schemes:
        rules = s.get("eligibility_rules", {})
        matched_criteria: List[str] = []
        unmet_criteria: List[str] = []
        unknown_criteria: List[str] = []

        # 1. State jurisdiction check
        scheme_state = s.get("state_code", "ALL")
        if scheme_state != "ALL":
            if state and state != "ALL":
                if scheme_state == state:
                    matched_criteria.append(f"State residency in {state} matches scheme jurisdiction.")
                else:
                    unmet_criteria.append(f"Scheme is restricted to residents of {scheme_state}, whereas applicant state is {state}.")
            else:
                unknown_criteria.append(f"Scheme is only available in state code '{scheme_state}'. State was not specified.")
        else:
            matched_criteria.append("Available across all States and Union Territories (Central Scheme).")

        # 2. Age criteria check
        min_age = rules.get("min_age")
        max_age = rules.get("max_age")
        if min_age is not None or max_age is not None:
            if age is not None:
                if min_age is not None and age < min_age:
                    unmet_criteria.append(f"Minimum age required is {min_age} years (applicant is {age}).")
                elif max_age is not None and age > max_age:
                    unmet_criteria.append(f"Maximum age limit is {max_age} years (applicant is {age}).")
                else:
                    matched_criteria.append(f"Age {age} fulfills scheme age criteria.")
            else:
                req_str = f"between {min_age or 0} and {max_age or 'any'} years"
                unknown_criteria.append(f"Age requirement ({req_str}) could not be verified because age was not provided.")

        # 3. Income limit check
        max_income = rules.get("max_income")
        if max_income is not None:
            if income is not None:
                if income <= max_income:
                    matched_criteria.append(f"Annual income ₹{income:,.0f} is within the maximum limit of ₹{max_income:,.0f}.")
                else:
                    unmet_criteria.append(f"Annual income ₹{income:,.0f} exceeds the scheme threshold of ₹{max_income:,.0f}.")
            else:
                unknown_criteria.append(f"Income threshold of ₹{max_income:,.0f} could not be verified because income was not provided.")

        # 4. Gender check
        req_gender = rules.get("gender")
        if req_gender:
            if gender:
                if str(gender).strip().lower() == req_gender.lower():
                    matched_criteria.append(f"Gender criteria ({req_gender}) satisfied.")
                else:
                    unmet_criteria.append(f"Scheme is dedicated for {req_gender} beneficiaries.")
            else:
                unknown_criteria.append(f"Scheme requires {req_gender} applicant; gender was not specified.")

        # 5. Farmer criteria
        if rules.get("farmer_only"):
            if is_farmer is True or (isinstance(is_farmer, str) and is_farmer.lower() in ["true", "yes"]):
                matched_criteria.append("Farmer status confirmed.")
            elif is_farmer is False or (isinstance(is_farmer, str) and is_farmer.lower() in ["false", "no"]):
                unmet_criteria.append("Scheme requires landholding farmer status.")
            elif occupation == "farmer":
                matched_criteria.append("Occupation indicated as Farmer.")
            else:
                unknown_criteria.append("Farmer / agricultural landholding status was not specified.")

        # 6. Student criteria
        if rules.get("student_only"):
            if is_student is True or (isinstance(is_student, str) and is_student.lower() in ["true", "yes"]):
                matched_criteria.append("Enrolled student status confirmed.")
            elif is_student is False or (isinstance(is_student, str) and is_student.lower() in ["false", "no"]):
                unmet_criteria.append("Scheme requires active student enrollment.")
            elif occupation == "student":
                matched_criteria.append("Occupation indicated as Student.")
            else:
                unknown_criteria.append("Student enrollment status was not specified.")

        # 7. Target beneficiary group check
        target_groups = rules.get("target_groups", [])
        if category and target_groups:
            if any(str(category).lower() in tg.lower() for tg in target_groups):
                matched_criteria.append(f"Beneficiary category ({category}) matches targeted groups.")

        # Determine overall eligibility status
        if unmet_criteria:
            status = "Not eligible based on available rules"
            badge = "danger"
            summary_reason = "One or more verified eligibility conditions are not satisfied."
        elif len(unknown_criteria) > len(matched_criteria):
            status = "Insufficient information"
            badge = "warning"
            summary_reason = "Crucial criteria could not be verified with the provided details."
        else:
            status = "Potentially eligible"
            badge = "success"
            summary_reason = "You appear to fulfill the basic criteria based on available rules. Official verification is required."

        evaluations.append({
            "scheme_id": s.get("id"),
            "scheme_name": s.get("name"),
            "government_level": s.get("government_level"),
            "department": s.get("department"),
            "official_url": s.get("official_url"),
            "status": status,
            "badge": badge,
            "summary_reason": summary_reason,
            "matched_criteria": matched_criteria,
            "unmet_criteria": unmet_criteria,
            "unknown_criteria": unknown_criteria,
            "required_documents": s.get("required_documents", []),
            "notes": rules.get("notes")
        })

    # Sort evaluations: Potentially eligible first, then Insufficient info, then Not eligible
    priority_map = {
        "Potentially eligible": 0,
        "Insufficient information": 1,
        "Not eligible based on available rules": 2
    }
    evaluations.sort(key=lambda x: priority_map.get(x["status"], 3))

    return api_response(
        data={
            "evaluations": evaluations,
            "total_evaluated": len(evaluations),
            "potentially_eligible_count": sum(1 for e in evaluations if e["status"] == "Potentially eligible"),
            "disclaimer": "SchemeSathi AI evaluates eligibility based on published program parameters. Final approval is subject to statutory document verification by relevant Government authorities. Never make financial commitments based solely on automated tools."
        },
        message="Eligibility evaluation completed"
    )

@app.route("/api/assistant", methods=["POST"])
def assistant_chat():
    """
    RAG-powered conversational assistant.
    1. Validates user prompt.
    2. Retrieves relevant scheme records as context.
    3. Feeds context to AI provider or uses high-fidelity grounded template if AI is not configured.
    4. Cites official URLs and highlights uncertainties.
    """
    if not request.is_json:
        return api_response(data=None, message="Request payload must be valid JSON", success=False, status_code=400)

    body = request.get_json() or {}
    user_query = str(body.get("query", "")).strip()

    if not user_query:
        return api_response(data=None, message="Please ask a question about government schemes.", success=False, status_code=400)

    if len(user_query) > 1000:
        return api_response(data=None, message="Your query is too long. Please summarize your question under 1,000 characters.", success=False, status_code=400)

    # Step 1: Scheme retrieval (RAG step)
    schemes = db_manager.get_all_schemes()
    query_lower = user_query.lower()
    matched_schemes: List[Dict[str, Any]] = []

    for s in schemes:
        name = s.get("name", "").lower()
        desc = s.get("description", "").lower()
        dept = s.get("department", "").lower()
        cats = [c.lower() for c in s.get("categories", [])]
        groups = [g.lower() for g in s.get("eligibility_rules", {}).get("target_groups", [])]

        score = 0
        tokens = [t for t in query_lower.replace("?", " ").replace(",", " ").split() if len(t) > 2]
        for token in tokens:
            if token in name:
                score += 3
            if token in desc:
                score += 1
            if token in dept:
                score += 2
            if any(token in c for c in cats):
                score += 2
            if any(token in g for g in groups):
                score += 2

        if score > 0:
            matched_schemes.append((score, s))

    matched_schemes.sort(key=lambda x: -x[0])
    selected_schemes = [item[1] for item in matched_schemes[:4]]

    # If no specific match, include 3 prominent diverse schemes for helpful context
    if not selected_schemes:
        selected_schemes = schemes[:3]

    # Build Grounding Context
    context_blocks = []
    citations = []
    for s in selected_schemes:
        citations.append({
            "name": s["name"],
            "url": s["official_url"],
            "level": s["government_level"],
            "department": s["department"]
        })
        context_blocks.append(
            f"Scheme: {s['name']}\n"
            f"Level: {s['government_level']} | State Code: {s['state_code']}\n"
            f"Department: {s['department']}\n"
            f"Description: {s['description']}\n"
            f"Benefits: {s.get('benefits', {}).get('summary', 'Refer to portal')}\n"
            f"Key Eligibility: {s.get('eligibility_rules', {}).get('notes', 'Standard criteria apply')}\n"
            f"Required Documents: {', '.join(s.get('required_documents', []))}\n"
            f"Official Link: {s['official_url']}"
        )

    context_str = "\n\n---\n\n".join(context_blocks)

    # Step 2: Formulate AI Answer
    if AI_API_KEY:
        try:
            system_prompt = (
                "You are SchemeSathi AI, an expert, objective Indian Government Scheme Assistant.\n"
                "Your objective is to provide truthful, respectful, and strictly grounded answers to citizens looking for government support.\n"
                "RULES YOU MUST NEVER BREAK:\n"
                "1. Answer ONLY using the facts from the verified context provided below.\n"
                "2. If the user asks about a scheme not in the context or if specific information (like deadlines or exact quota) is missing, explicitly state: 'Information for this query is not fully verified in our database. Please check the official government portal.'\n"
                "3. Never fabricate or invent scheme names, monetary amounts, rules, or URLs.\n"
                "4. Always include the official portal link for the schemes you mention.\n"
                "5. Remind users that SchemeSathi AI is an independent guide and final eligibility is subject to government verification."
            )

            user_message = (
                f"VERIFIED SCHEMES CONTEXT:\n{context_str}\n\n"
                f"CITIZEN QUESTION:\n{user_query}\n\n"
                "Please provide a clear, empathetic, well-structured answer with bullet points for benefits, eligibility, and required documents. Include official URLs."
            )

            # Call AI Provider (compatible with OpenAI/Groq REST standard)
            headers = {
                "Authorization": f"Bearer {AI_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": AI_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "temperature": 0.2,
                "max_tokens": 800
            }

            api_endpoint = f"{AI_API_BASE_URL.rstrip('/')}/chat/completions"
            ai_res = requests.post(api_endpoint, headers=headers, json=payload, timeout=20)

            if ai_res.status_code == 200:
                ai_data = ai_res.json()
                answer = ai_data["choices"][0]["message"]["content"]
                return api_response(
                    data={
                        "answer": answer,
                        "citations": citations,
                        "provider": "ai",
                        "model": AI_MODEL
                    },
                    message="Assistant response generated"
                )
            else:
                logger.warning(f"AI API returned status {ai_res.status_code}: {ai_res.text}")
                # Fallback to grounded rule-based answer
        except Exception as e:
            logger.error(f"Error calling AI provider: {e}")
            # Graceful fallback continues below

    # Grounded Deterministic Fallback Assistant (when AI_API_KEY is not configured or unavailable)
    fallback_parts = [
        f"Based on verified government records related to your inquiry about **'{user_query}'**, here are the most relevant official schemes:",
        ""
    ]

    for s in selected_schemes[:2]:
        benefits = s.get("benefits", {}).get("summary", "Official financial/welfare support")
        rules = s.get("eligibility_rules", {}).get("notes", "Specific eligibility criteria apply")
        docs = ", ".join(s.get("required_documents", [])[:3])
        fallback_parts.append(f"### 🏛️ {s['name']}")
        fallback_parts.append(f"- **Authority**: {s['department']} ({s['government_level']} Government)")
        fallback_parts.append(f"- **Primary Benefits**: {benefits}")
        fallback_parts.append(f"- **Eligibility Summary**: {rules}")
        if docs:
            fallback_parts.append(f"- **Key Documents**: {docs}")
        fallback_parts.append(f"- **Official Portal**: [{s['official_url']}]({s['official_url']})")
        fallback_parts.append("")

    fallback_parts.append("---")
    fallback_parts.append("💡 *Note: To enable live generative chat responses, configure `AI_API_KEY` in your `.env` file. SchemeSathi AI is an independent guide; always verify current deadlines and application guidelines on the official portal.*")

    return api_response(
        data={
            "answer": "\n".join(fallback_parts),
            "citations": citations,
            "provider": "rule_based_grounded",
            "model": "verified_records_engine"
        },
        message="Assistant response generated from verified scheme database"
    )

if __name__ == "__main__":
    logger.info(f"Starting SchemeSathi AI Server on port {PORT}...")
    app.run(host="0.0.0.0", port=PORT, debug=False)
