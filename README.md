# FinPilot — AI-Based Personal Finance Management System

**Academic Mini-Project / Capstone Implementation**  
*Local-First, Privacy-Preserving Intelligent Personal Financial Planning, Statistical Forecasting & Decision Simulation Platform.*

---

## 1. Project Introduction
**FinPilot** is a production-grade, local-first personal financial management web application developed to empower individuals with actionable financial intelligence, real-time guardrails, and deterministic cash-flow simulation. Built using Python, Streamlit, and Scikit-learn, FinPilot prioritizes user privacy by storing all sensitive records inside a local, embedded SQLite database—eliminating the need for third-party cloud data transmission or paid external API subscriptions.

FinPilot bridges the gap between conventional static expense trackers and advanced computational intelligence by combining deterministic financial mathematics (Safe-to-Spend pacing, recurring bill scheduling, scenario stress-testing) with chronologically validated statistical and machine-learning models (time-series baseline evaluation, TF-IDF + Random Forest categorization, multi-feature anomaly audit, and K-Means behavioral clustering).

---

## 2. Problem Statement
Modern personal financial management poses critical behavioral and computational challenges for working professionals and students:
1. **The "Illusion of Wealth" Dilemma:** A user's raw bank checking balance is deceptive. It fails to account for upcoming unpaid bills, essential safety cushions, or monthly savings commitments, leading to month-end deficits.
2. **Impulse Decisions & Lack of Forward Visibility:** Individuals frequently make major discretionary purchases (e.g. gadgets, travel) without understanding the impact on their month-end cash flow or category budget caps.
3. **Black-Box AI & Data Privacy Risks:** Cloud-based financial apps routinely harvest private transaction data, sell aggregated financial profiles, or fabricate unsubstantiated "AI advice" without empirical evidence.
4. **Static Expense Recording:** Most budgeting tools simply show historical pie charts without predictive time-series modeling, anomaly screening, or interactive "What-If" decision stress tests.

---

## 3. Project Objectives
- **Local-First Data Sovereignity:** Guarantee 100% data privacy by keeping all financial operations, SQL queries, and ML training pipelines local.
- **Deterministic Safe-to-Spend Engine:** Formulate an unassailable mathematical spending ceiling that protects unpaid bills, safety reserve floors, and savings targets without double-counting expenses.
- **Chronologically Validated Forecasting:** Implement and benchmark time-series expense forecasting models (Linear Regression vs. 3-Month Moving Average vs. Naive baseline) strictly on historical holdouts with zero lookahead data leakage.
- **Explainable Hybrid Categorization:** Deploy a TF-IDF + Random Forest pipeline with model persistence and evaluation metrics, supplemented by deterministic keyword fallback rules.
- **Multi-Feature Anomaly Auditing:** Detect abnormal transactions using robust category z-scores, vendor deviation, and velocity spikes, framed with ethical non-fraud terminology.
- **Interactive What-If Scenario Simulator:** Empower users to stress-test major purchases, category spending cuts, income reduction shocks, and systematic savings plans before committing real capital.
- **Automated Recurring Commitments:** Idempotently generate recurring bill schedules upon payment confirmation.

---

## 4. Technology Stack

### Frontend (Modern React Client)
- **Framework:** React 19 + Vite 5 (Fast build, modern JSX runtime)
- **Styling:** Tailwind CSS v3 + PostCSS (Deep navy `#0A192F`, emerald teal `#0D9488`, clean cards)
- **Visualizations:** Recharts (Responsive financial area, bar, and pie charts)
- **Icons:** Lucide React
- **State & Routing:** Context API (`AuthContext`, `FinanceContext`), Hash-friendly SPA routing
- **HTTP Client:** Native `fetch` with HttpOnly cookie credentials and automatic CSRF header injection

### Backend (FastAPI Application Server)
- **Framework:** FastAPI + Pydantic v2 (Strict request/response schema validation)
- **Server:** Uvicorn ASGI server with WAL SQLite connection mode
- **Security & Authentication:**
  - Password Hashing: Native `bcrypt` with salt rounds and strict 72-byte truncation guarantee
  - Session Store: Server-side SQLite `sessions` table (7-day sliding expiry, 30-day max)
  - Cookies: `HttpOnly`, `SameSite=Lax`, secure path `/` (no JWTs or tokens in localStorage)
  - CSRF Defense: Cryptographic double-submit `X-CSRF-Token` required on state-mutating requests
  - Brute-Force Rate Limiting: 5 attempts per 15-minute window with automated lockout
  - Multi-User Isolation: Strict `user_id` scoping across all transactions, budgets, bills, and settings
- **Data Access:** SQLite3 (WAL mode, parameterized queries, unique multi-user constraints)
- **Machine Learning & Analytics:** Scikit-learn, Joblib, Pandas, NumPy

### Fallback Frontend (Streamlit)
- **Framework:** Streamlit (Runs concurrently on legacy `user_id = 0` data)
- **Visualizations:** Plotly Graph Objects & Express

---

## 5. System Architecture
FinPilot follows a decoupled, layered microservice architecture supporting both modern React clients and the Streamlit desktop fallback:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   PRESENTATION CLIENT LAYER (React SPA)                │
│  React 19 · Vite · Tailwind CSS · Recharts · Lucide · AuthContext      │
│  Pages: Dashboard · Transactions · Budgets · Coach · Simulator · ML    │
│  Auth: Sign In · Sign Up · Session Manager (HttpOnly + CSRF Protected) │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │ JSON / Cookies (REST API)
┌────────────────────────────────────▼───────────────────────────────────┐
│                    API GATEWAY & AUTH LAYER (FastAPI)                  │
│  FastAPI · Uvicorn · Pydantic V2 · CORS · Rate Limiter (Brute-Force)   │
│  Session Dependency (get_current_user) · Double-Submit CSRF Validator  │
│  Routers: /api/auth · /api/overview · /api/transactions · /api/budgets │
│           /api/coach · /api/simulator · /api/insights · /api/settings  │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │ User-Scoped Function Calls
┌────────────────────────────────────▼───────────────────────────────────┐
│                     BUSINESS LOGIC & SERVICES LAYER                    │
│  safespending.py        · simulator.py          · coach.py             │
│  budget_service.py      · csv_service.py        · transaction_service.py│
└──────────────────┬─────────────────────────────────┬───────────────────┘
                   │                                 │
┌──────────────────▼──────────────────┐ ┌────────────▼───────────────────┐
│     MACHINE LEARNING LAYER (src/ml) │ │       DATA PERSISTENCE LAYER   │
│  forecasting.py   (Time-Series)     │ │  src/database.py (WAL Mode)    │
│  categorization.py (TF-IDF + RF)    │ │  SQLite3 tables: users,        │
│  anomaly.py       (Multi-Feature)   │ │  sessions, auth_attempts,      │
│  clustering.py    (K-Means & Ratio) │ │  transactions, budgets, bills, │
│  models/category_model.joblib       │ │  user_settings (user_id scoped)│
└─────────────────────────────────────┘ └───────────────────────────────┘
                                     ▲
┌────────────────────────────────────┴───────────────────────────────────┐
│                   STREAMLIT FALLBACK DASHBOARD (app.py)                │
│  Legacy direct desktop UI reading legacy user_id = 0 records           │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Application Features
1. **Executive Overview Dashboard:** Real-time liquid cash balance, total inflows/outflows, dynamic Safe-to-Spend ceiling, daily/weekly pacing allowance, category spending pie charts, and monthly trend tracking.
2. **Transaction Management:** Full CRUD operations (Add, Edit, Safe Delete with confirmation), real-time search, multi-criteria filtering (Type, Category, Date range, Amount min/max), and CSV bulk import/export with duplicate rejection.
3. **Budgets & Recurring Bills:** Monthly category budget limits with percentage utilization progress bars; upcoming bill scheduling with automatic chronological due-date rollover upon payment.
4. **AI Money Coach:** Evidence-backed diagnostic recommendations analyzing overspending, unbudgeted outflows, category surges, bill reminders, 50/30/20 savings gap analysis, and recurring subscription review.
5. **What-If Financial Decision Simulator:** Interactive simulation of:
   - *Major Purchase Impact:* Affordability verdicts, remaining liquidity, and budget overrun alerts.
   - *Category Expense Reduction:* Projected monthly and cumulative 3/6/12-month savings.
   - *Income Reduction Shock:* Runway sustainability analysis and deficit warnings.
   - *Monthly Savings Accelerator:* Wealth accumulation trajectories without treating savings transfers as losses.
6. **AI Insights & Machine Learning:** Comprehensive evaluation diagnostics:
   - Model comparison table (Holdout MAE/RMSE for Linear Regression, Moving Average, Naive baseline).
   - Time-series plot with 95% statistical prediction intervals.
   - Categorization evaluation diagnostics (Accuracy, Precision, Recall, F1, Confusion matrix).
   - Live interactive categorization testing sandbox.
   - Multi-feature anomaly audit table with robust z-scores and explainable reasons.
   - K-Means spending archetypes (with Needs vs. Wants ratio and category volatility fallbacks).
7. **Settings & Data Management:** Baseline planning parameters configuration, 12-month synthetic demo data generator, CSV database backup download, and one-click database reset.

---

## 7. Database Design
Stored in `data/finance.db` with SQLite foreign keys enabled:

### Schema Overview:
1. `transactions`
   - `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
   - `txn_date` (TEXT NOT NULL, ISO YYYY-MM-DD)
   - `txn_type` (TEXT CHECK in 'Income', 'Expense')
   - `description` (TEXT NOT NULL)
   - `amount` (REAL NOT NULL CHECK > 0)
   - `category` (TEXT NOT NULL)
   - `notes` (TEXT DEFAULT '')
   - `created_at` (TEXT DEFAULT CURRENT_TIMESTAMP)
   - *Indexes:* `idx_txn_date`, `idx_txn_type`, `idx_txn_category`
2. `budgets`
   - `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
   - `month` (TEXT NOT NULL, YYYY-MM)
   - `category` (TEXT NOT NULL)
   - `limit_amount` (REAL NOT NULL CHECK >= 0)
   - *Constraint:* `UNIQUE(month, category)`
   - *Index:* `idx_budgets_month`
3. `bills`
   - `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
   - `description` (TEXT NOT NULL)
   - `amount` (REAL NOT NULL CHECK > 0)
   - `due_date` (TEXT NOT NULL, YYYY-MM-DD)
   - `paid` (INTEGER DEFAULT 0 CHECK in 0, 1)
   - `frequency` (TEXT DEFAULT 'One-time' CHECK in 'One-time', 'Weekly', 'Monthly', 'Yearly')
   - `next_due_date` (TEXT DEFAULT '')
   - *Index:* `idx_bills_due`
4. `settings`
   - `setting_key` (TEXT PRIMARY KEY)
   - `setting_value` (TEXT NOT NULL)

---

## 8. Machine-Learning Algorithms & Mathematical Formulation

### A. Chronological Expense Forecasting
- **Candidate Models:**
  1. *Linear Regression:* $\hat{y}_t = \beta_0 + \beta_1 t$ fitted on chronological month index $t$.
  2. *3-Month Moving Average:* $\hat{y}_t = \frac{1}{3}\sum_{i=1}^3 y_{t-i}$.
  3. *Naive Baseline:* $\hat{y}_t = y_{t-1}$.
- **Chronological Holdout Validation (No Lookahead Leakage):**
  Given $N$ months, models are trained strictly on months $0 \dots (N - H - 1)$ and tested on holdout months $(N - H) \dots (N - 1)$ where $H = \min(3, \max(1, N - 3))$.
- **Evaluation Metrics:**
  $$\text{MAE} = \frac{1}{H}\sum_{k=1}^H |y_k - \hat{y}_k|, \quad \text{RMSE} = \sqrt{\frac{1}{H}\sum_{k=1}^H (y_k - \hat{y}_k)^2}$$
- **Prediction Uncertainty Intervals:**
  Standard error of forecast at next month $x^* = N$:
  $$SE_{pred} = s_e \sqrt{1 + \frac{1}{N} + \frac{(x^* - \bar{x})^2}{\sum (x_i - \bar{x})^2}}, \quad s_e = \sqrt{\frac{\sum (y_i - \hat{y}_i)^2}{N - 2}}$$
  - **80% Prediction Interval:** $[\max(0, \hat{y} - 1.282 \cdot SE_{pred}), \hat{y} + 1.282 \cdot SE_{pred}]$
  - **95% Prediction Interval:** $[\max(0, \hat{y} - 1.960 \cdot SE_{pred}), \hat{y} + 1.960 \cdot SE_{pred}]$

### B. Transaction Categorization Pipeline
- **Vectorization:** `TfidfVectorizer(ngram_range=(1, 2), min_df=1, max_features=3000, sublinear_tf=True)`
- **Classifier:** `RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')`
- **Evaluation:** Evaluated on an 80/20 stratified holdout for Accuracy, Precision (Weighted), Recall (Weighted), and F1-Score (Weighted).
- **Persistence & Caching:** Saved to `models/category_model.joblib` with dataset hash validation to eliminate repeated training latency.
- **Inference with Keyword Fallback:** Predicts category with class probability $P(c|x)$. If $\max_c P(c|x) < 0.35$ or the transaction is Income, automatically routes to deterministic keyword rules.

### C. Multi-Feature Anomaly Audit
- Evaluates 4 feature signals:
  1. *Category Robust Z-Score:* $z = \frac{x - \text{median}}{1.4826 \cdot \text{MAD}}$ (flags $z \ge 2.3$ and $x / \text{median} \ge 1.5$).
  2. *Merchant Median Deviation:* Flags charges $\ge 2.5\times$ typical merchant median ($x \ge ₹500$).
  3. *Velocity Bursts:* Flags days where daily transaction count exceeds historical baseline velocity ($\mu_{freq} + 2.5\sigma_{freq}$).
  4. *Multivariate Isolation Forest:* Screened on $[ \log(1+x), z_{cat}, \text{ratio}, \text{frequency} ]$ with $0.03$ contamination.
- **Ethical Disclaimer:** Flagged items represent statistical spending deviations for user review; never confirmed fraud.

### D. Spending Pattern Clustering
- **Data Sufficiency Rule:** Requires $N \ge 6$ calendar months to avoid small-sample underdetermination.
- **Model:** `StandardScaler()` + `KMeans(n_clusters=K, random_state=42)` ($K=2$ if $N<9$, else $K=3$).
- **Archetype Profiles:** Low-Spend / High-Savings Month, Balanced Routine Month, Peak Discretionary Month.
- **Statistical Fallbacks ($N < 6$):**
  1. *Needs vs. Wants Ratio:* Essential (Rent, Groceries, Utilities, Health, Transport) vs. Discretionary (Food, Shopping, Entertainment, Travel) benchmarked against the 50/30/20 guideline.
  2. *Category Volatility Analysis:* Coefficient of Variation ($CV = \sigma / \mu$) categorizing expenses into Fixed ($CV < 0.15$), Moderate ($0.15 \le CV \le 0.40$), and Volatile ($CV > 0.40$).

---

## 9. Methodology
1. **Stabilization & Foundation Hardening (Phase 1):** Verified Python 3.11 virtual environment, established automated SQLite backups with integrity checks, created the modular `src/` directory.
2. **Core Data & Services Hardening (Phase 2):** Built resilient transaction services, advanced filtering, row-level CSV validation with duplicate prevention, and recurring bill scheduling.
3. **Deterministic Simulator & AI Coach (Phase 3):** Developed the 4-scenario What-If simulator engine and evidence-backed AI Money Coach diagnostics.
4. **Fintech Design System (Phase 4):** Standardized visual tokens (Navy, Teal, Clean Cards, typography) and upgraded Plotly charts.
5. **Machine Learning & Evaluation (Phase 5):** Replaced simplistic ML routines with chronological holdout validation, baseline benchmarking, prediction intervals, TF-IDF + Random Forest persistence, multi-feature anomaly screening, and K-Means sufficiency checks.
6. **Final Quality Assurance & Readiness (Phase 6):** Executed comprehensive boundary condition audits, 59 automated unit tests, and prepared this complete distribution package.

---

## 10. Installation Instructions

### Prerequisites
- Python 3.11 or higher installed on your system.
- Git (optional, for cloning).

### Steps

#### Option A: Modern React + FastAPI Stack (Recommended)
1. **Backend Environment Setup:**
   ```powershell
   py -3.11 -m venv .venv_backend
   .\.venv_backend\Scripts\Activate.ps1
   pip install -r backend_requirements.txt
   ```
2. **Frontend Environment Setup:**
   ```powershell
   cd frontend
   npm install
   cd ..
   ```

#### Option B: Streamlit Fallback Stack
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## 11. How to Run the Project

### Running the Modern React + FastAPI Web Application (Recommended)

1. **Start the FastAPI Backend:**
   In Terminal 1 (from repository root):
   ```powershell
   .\.venv_backend\Scripts\uvicorn.exe backend.main:app --port 8000 --reload
   ```
   Backend will be running at `http://127.0.0.1:8000` (Swagger docs at `/docs`).

2. **Start the React Frontend:**
   In Terminal 2:
   ```powershell
   cd frontend
   npm run dev
   ```
   Open your browser at `http://localhost:5173`.
   - Register a new account or sign in with your credentials.
   - All transactions, budgets, bills, and settings are strictly isolated to your user profile.
   - Session authentication is managed via secure, HttpOnly, SameSite cookies with CSRF validation.

---

### Running the Streamlit Application (Fallback / Direct Desktop UI)

To run the original Streamlit application:
```powershell
.\.venv\Scripts\streamlit.exe run app.py
```
Open your browser at `http://localhost:8501`.
- The Streamlit application operates concurrently on the database and accesses legacy `user_id = 0` records.

---

## 12. How to Execute Tests

### 1. Run Complete API & Authentication Test Suite (30 Tests)
```powershell
.\.venv_backend\Scripts\python.exe -m pytest tests/test_api.py -v
```
Verifies health, summary, transactions CRUD, auto-categorization, budgets, bills, coach recommendations, all 4 simulator scenarios, ML forecasts, anomalies, clustering, session authentication, cookie persistence, and multi-user data isolation.

### 2. Run Core Service & Machine Learning Tests (59 Tests)
```powershell
.\.venv_backend\Scripts\python.exe -m pytest tests/ -k "not test_api" -v
```
Verifies safe-spending math, CSV import validation, recurring bills, simulator calculations, ML model pipelines, and edge cases.

### 3. Run All 89 Automated Tests
```powershell
.\.venv_backend\Scripts\python.exe -m pytest tests/ -v
```
Expected output: **89 passed** in ~15 seconds.

---

## 13. Screens and Page Descriptions
1. **Overview Dashboard:** Executive summary cards (Available Balance, Lifetime Inflows/Outflows, Safe-to-Spend Ceiling, Daily Pacing Allowance), commitment breakdowns, category pie chart, and monthly spend trajectory.
2. **Transactions:** Transaction entry form with real-time category auto-detection, CSV drag-and-drop import with preview/duplicate reporting, full-text description search, multi-parameter filters, transaction edit/delete modal, and CSV export.
3. **Budgets & Bills:** Category monthly budget setup with percentage progress meters, upcoming bill tracker, payment status toggle, and recurring bill scheduling.
4. **AI Money Coach:** Diagnostic insight cards highlighting spending surges, unbudgeted outflows, upcoming bill liquidity warnings, 50/30/20 savings gap analysis, and recurring subscription review.
5. **What-If Simulator:** Interactive sliders and inputs testing Major Purchases, Expense Reductions, Income Shocks, and Monthly Savings Accrual with immediate side-by-side impact tables.
6. **AI Insights & ML:** 4 dedicated analytics tabs:
   - *Expense Forecasting & Baselines:* Model comparison table, best performer badge, 95% prediction interval error band chart, and category forecasts.
   - *Categorization Engine:* Holdout accuracy, weighted precision/recall/F1 metrics, confusion matrix diagnostics, and real-time interactive testing sandbox.
   - *Anomaly Audit:* Multi-feature deviation table, robust z-scores, and non-fraud audit notice.
   - *Spending Archetypes:* K-Means cluster profiles, scatter visual, Needs vs. Wants breakdown, and Category Volatility ($CV$) table.
7. **Settings & Data:** Financial planning assumptions (Opening Balance, Safety Reserve, Savings Target), 12-month synthetic demo loader, CSV database backup download, and database reset button.

---

## 14. College Faculty Viva & Demonstration Guide

To deliver an impactful, professional project demonstration to your college evaluators, follow this exact 7-step sequence:

### Step 1: Initialization & Demonstration Data
1. Navigate to **Settings & Data** (sidebar).
2. Click **"Load 12 Months of Synthetic Demo Records"**.
3. Point out that the system loads 12 full calendar months of realistic, multi-category transactions, demo budgets, and recurring bills, explicitly marked as synthetic for ethical integrity.

### Step 2: The Executive Overview & Safe-to-Spend Formula
1. Navigate to **Overview**.
2. Show the **Hero Banner** and the 4 summary metrics.
3. **Key Concept to Explain:** Emphasize that *Safe-to-Spend is NOT an AI guess*; it is an exact mathematical guardrail that protects liquid cash after reserving unpaid bills, the safety reserve floor, and monthly savings targets.

### Step 3: Transaction Management & CSV Hardening
1. Navigate to **Transactions**.
2. Type an expense description (e.g. *"Uber trip to airport"*) and show how the **Auto-detect** feature identifies the category.
3. Show the **Filters & Search** (filter by Date range, Amount min/max, or search *"Swiggy"*).
4. Download the CSV template, or upload the provided `sample_data/sample_transactions.csv` to showcase the row-level validation and duplicate detection preview.

### Step 4: Budgets & Recurring Bills Automation
1. Navigate to **Budgets & Bills**.
2. Show the monthly category progress meters (On Track vs. Warning vs. Exceeded).
3. Demonstrate clicking the **"Paid"** checkbox on a recurring monthly bill (e.g. Electricity Bill) and show the instant notification indicating that the next month's bill was generated idempotently.

### Step 5: What-If Decision Simulation
1. Navigate to **What-If Simulator**.
2. **Scenario A (Major Purchase):** Enter a ₹50,000 purchase under *Shopping*. Show how the engine immediately flags the deficit warning, recalculates post-purchase cash, and explains the impact on commitments.
3. **Scenario B (Expense Reduction):** Show that reducing *Food* by 20% projects realistic cumulative 3-month and 12-month savings based on actual historical monthly baselines.

### Step 6: AI Insights & Rigorous ML Evaluation (Faculty High-Impact Section)
1. Navigate to **AI Insights**:
2. **Tab 1 (Forecasting):** Show the **Model Evaluation Table**. Explain why the *3-Month Moving Average achieved lower holdout MAE than Linear Regression* on this dataset, and explain that the shaded ribbon is a **95% Prediction Interval**, not an invented figure.
3. **Tab 2 (Categorization):** Show the *Holdout F1-Score, Precision, and Recall*. Use the **Interactive Categorization Sandbox** at the bottom: type *"Apollo pharmacy medicines"* and watch the Random Forest model predict *Health* with its confidence score.
4. **Tab 3 (Anomaly Audit):** Highlight the non-fraud audit notice and explain the 4 feature signals (Category robust z-score, merchant deviation, velocity bursts, and multivariate Isolation Forest).
5. **Tab 4 (Spending Archetypes):** Show the 3 K-Means archetypes (*Low-Spend*, *Balanced*, *Peak Discretionary*), followed by the *Needs vs. Wants* ratio and *Category Volatility ($CV$)* stability table.

### Step 7: Automated Test Suite Proof
1. Switch to your terminal and run:
   ```powershell
   .\.venv_backend\Scripts\python.exe -m pytest tests/ -v
   ```
2. Show all **89 automated tests passing** — 30 API & authentication tests (FastAPI) + 59 unit & service tests (ML models, calculators, edge cases) — in under 15 seconds as proof of full-stack software engineering rigor.

---

## 15. Limitations
1. **Local-First Scope:** Designed as a local personal finance app; production deployment would require HTTPS, an external secrets manager, and proper reverse proxy configuration.
2. **Manual & CSV Ingestion:** Relies on manual entry and CSV bank statement uploads; there is no live Open Banking API integration due to regulatory and licensing constraints.
3. **Unsupervised Outlier Screening:** Anomaly screening flags statistical deviations relative to personal history; it cannot provide legal or forensic confirmation of financial fraud.
4. **Short-History Cold Start:** Advanced statistical clustering requires at least 6 months of data, and Random Forest requires at least 25 labelled records. Robust fallbacks (Needs vs. Wants, keyword rules) handle this cold-start period.

---

## 16. Future Enhancements
- Account Aggregator (AA) framework integration for automated real-time Indian bank statement sync via RBI-regulated NBFC AA protocols.
- Multi-currency conversion support with real-time foreign exchange rate caches.
- Tax optimization module estimating income tax deductions (Section 80C, 80D) under Old vs. New Indian tax regimes.
- Investment portfolio allocation module tracking mutual funds, equities, and fixed deposits alongside cash flow.
- Mobile companion application via Progressive Web App (PWA) standards.
- Production Docker deployment with Nginx reverse proxy, HTTPS via Let's Encrypt, and PostgreSQL migration.
