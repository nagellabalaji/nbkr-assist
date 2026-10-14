# AI-Powered Smart College Complaint & Maintenance Management System

An advanced, production-grade automated facilities management platform designed to streamline student complaint lifecycles. The system uses a hybrid AI routing engine to automatically classify incoming complaints, estimate priority levels, allocate specialized estates staff, and interact with students via a conversational chatbot interface.

---

## 📖 Table of Contents
1. [Problem Statement](#-problem-statement)
2. [Objectives](#-objectives)
3. [Technology Stack](#-technology-stack)
4. [System & AI Architecture](#-system--ai-architecture)
5. [Database Architecture](#-database-architecture)
6. [API Documentation](#-api-documentation)
7. [Installation & Setup](#-installation--setup)
8. [Demo Credentials](#-demo-credentials)
9. [Future Enhancements](#-future-enhancements)

---

## 🚨 Problem Statement

Traditional university campus maintenance workflows rely on manual ticketing, email-based logs, or paper entries. This introduces major operational bottlenecks:
- **Delayed Routing**: Complaints (e.g. electrical breakdowns, classroom projector failures, pipe leakages) are manually sorted, delaying critical dispatches.
- **Priority Mismatch**: Urgent hazards (e.g., exposed sparking wiring) are often queued behind low-priority queries (e.g., dusty tables).
- **Communication Gaps**: Students have no clear visibility on assignment status, and maintenance engineers struggle to log progress notes or work proofs.

---

## 🎯 Objectives

- Create a responsive, unified platform with distinct interfaces for **Students**, **Estates Engineers (Staff)**, and **Administrators**.
- Implement automatic classification of tickets into 10 categories and predict priority levels using local NLP fallback vectors and Gemini LLM prompts.
- Establish an intelligent, 24/7 campus support bot (**CollegeAssist AI**) to resolve FAQ queries.
- Build interactive analytics for admins to monitor repair velocities, satisfaction indices, and seasonal workloads.

---

## 💻 Technology Stack

### Frontend
- **React.js (v18)** - Component-based SPA framework
- **Vite** - High-speed module bundling
- **CSS3 / Vanilla CSS** - Tailored dark-mode glassmorphic theme styling
- **Recharts** - SVG-based data visualizations for analytics
- **Lucide React** - High-quality vector iconography
- **Axios** - Interceptor-equipped REST API client

### Backend
- **Python (v3.10+)** - Backend language
- **Flask (v3.0)** - Lightweight micro-framework
- **Flask-JWT-Extended** - Secure token-based user sessions and role permissions
- **Flask-SQLAlchemy** - MySQL Object-Relational Mapper (ORM)
- **Flask-CORS** - Cross-origin resources configuration
- **PyMySQL** - Pure-python MySQL connector

### AI / NLP
- **Vector Space Modeler** - Local Python TF-IDF and Cosine Similarity equations
- **Google Gemini Generative AI** - Context-aware structuring prompts using `google-genai` SDK

---

## ⚙️ System & AI Architecture

The application implements a hybrid AI workflow. Incoming complaints trigger the AI Service:
1. **API Check**: If `GEMINI_API_KEY` is present in the `.env` configuration, the backend sends structured JSON-generation prompts to the `gemini-1.5-flash` model.
2. **Local NLP Fallback**: If the API key is absent, the backend invokes a local text similarity algorithm. It tokenizes descriptions, computes TF-IDF weights, and runs Cosine Similarity against pre-seeded category vocabularies. Priority is predicted using sentiment-urgency keyword matching.

```
                      +-----------------------------+
                      |     AI Dispatcher Service   |
                      +--------------+--------------+
                                     |
             +-----------------------+-----------------------+
             |                                               |
             v                                               v
  Has API key in .env?                            No API key present
             |                                               |
             v                                               v
+----------------------------+                 +----------------------------+
|    LLM Wrapper Service     |                 |  Local Rule-Based & NLP    |
| (Gemini/OpenAI API Call)   |                 | (Cosine/TF-IDF Similarity) |
+----------------------------+                 +----------------------------+
```

---

## 🔒 Secure Real-time Email OTP Verification System

This application implements a production-grade multi-factor authentication (MFA) flow using real-time email OTP verification:

### Flows Implemented:
1. **Registration Flow**:
   - Students enter academic details and click **Send OTP**.
   - The backend checks for duplicates and dispatches a cryptographically secure 6-digit code.
   - Once validated, the user profile is created.
2. **Login Flow**:
   - Users enter username/email and password.
   - On successful credentials check, the backend sends a 6-digit code to their email.
   - The user inputs the code to receive their final access JWT token.
3. **Forgot Password Flow**:
   - Users request password resets to their email, verify the OTP, and update their passwords.

### Security Features:
- **Hashed OTPs**: Stored securely using SHA-256 in the `otp_verifications` table.
- **Expiry Bounds**: All codes expire in exactly 5 minutes.
- **Brute Force Lock**: Verification fails and locks after 5 wrong attempts.
- **Cooldown Interval**: Prevents multiple sends within 60 seconds (Rate Limiting).
- **One-Time Use**: OTPs are marked invalid immediately after verification.

### Local Development / Testing OTP:
- If `EMAIL_API_KEY` is not provided in `.env`, the system automatically prints the generated OTP to the **Flask Server Console Output** in development mode, allowing you to test the flow offline.

---

## 🗄️ Database Architecture

The relational database is structured in MySQL. It enforces foreign key constraints, unique indexing, and cascade deletions:

- `users`: Core authentication record (Admin, Staff, Student).
- `students`: Academic profile links (Roll number, Hostel details, Contact).
- `staff`: Maintenance profiles (Department, Specialization, Availability).
- `admins`: Administrative profiles.
- `complaint_categories`: Category directory mapping (Electrical, Plumbing, etc.).
- `complaints`: Ticket logs, status, AI metrics, location, and uploaded image paths.
- `complaint_assignments`: Work allocation timelines linking admins, tickets, and engineers.
- `complaint_history`: Full audit trail of ticket updates.
- `notifications`: User-specific notification logs.
- `feedback`: Resolution satisfaction rating indices (1 to 5 stars).
- `chatbot_messages`: Conversation transcripts for bot sessions.

---

## 🔌 API Documentation

All request payloads expect JSON, and responses adhere to standard formats:

### Authentication
- `POST /api/auth/register` - Create Student or Staff profile.
- `POST /api/auth/login` - Validate credentials, return JWT access token with role claims.
- `POST /api/auth/logout` - Invalidate session token.
- `GET /api/auth/profile` - Retrieve current profile details.
- `PUT /api/auth/profile` - Modify contact numbers, room details, or specialization.

### Complaint Operations
- `POST /api/complaints` - Log a new complaint. (Supports `multipart/form-data` for file uploads). Automatically triggers AI classifier.
- `GET /api/complaints` - Filter complaints (Students see owned, Staff see assigned, Admins see all).
- `GET /api/complaints/:id` - Fetch complaint logs, assignments, and audit history.
- `PUT /api/complaints/:id` - Update work notes (Staff) or adjust priority/categories (Admin).
- `DELETE /api/complaints/:id` - Admin only: Permanently remove ticket.
- `POST /api/complaints/:id/assign` - Admin only: Allocate ticket to staff member.
- `PUT /api/complaints/:id/status` - Transition ticket state.
- `POST /api/complaints/:id/feedback` - Student only: Record star rating and comments.

### AI Interactions
- `POST /api/ai/classify` - Dry-run complaint categorization testing.
- `POST /api/ai/chat` - Chat with CollegeAssist AI chatbot.
- `POST /api/ai/summarize` - Summarize log history in 2 sentences.

### Analytics
- `GET /api/admin/analytics` - Fetch metrics, category distributions, and daily trends.

---

## 🚀 Installation & Setup

### Prerequisites
- Node.js (v18+)
- Python (v3.10+)
- MySQL Server

### 1. Database Setup
Start your MySQL server. Open phpMyAdmin or your MySQL CLI and run:
```sql
CREATE DATABASE college_complaints;
```
Import the schema:
```bash
mysql -u root -p college_complaints < database/schema.sql
```

### 2. Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   # On Windows (PowerShell):
   .\venv\Scripts\Activate.ps1
   # On macOS/Linux:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy the environment template:
   ```bash
   cp .env.example .env
   ```
   Modify `.env` database URLs and add your optional `GEMINI_API_KEY`.
5. Seed the database with sample data:
   ```bash
   python seed.py
   ```
6. Run the Flask development server:
   ```bash
   python run.py
   ```
   The backend API will run on `http://localhost:5000`.

### 3. Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd ../frontend
   ```
2. Install npm packages:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
   Open your browser and visit `http://localhost:5173`.

---

## 🔑 Demo Credentials

Test the platform instantly using these pre-seeded accounts (password is same for all roles):

| Role | Username | Password | Notes |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin1` | `admin123` | Can allocate tickets, view charts, and freeze users |
| **Staff** | `staff1` | `staff123` | Specialization: Electrical Repairs |
| **Staff** | `staff2` | `staff223` | Specialization: Plumbing Repairs (modify password to staff123 in seed if customized) |
| **Student**| `student1`| `student123` | File tickets, chat with bot, rate resolution |

*Note: All pre-seeded passwords are set to `admin123`, `staff123`, or `student123` respectively for testing convenience.*

---

## 🔮 Future Enhancements
- **Push Notification integration**: Send real-time alerts via WebSockets.
- **Multilingual Support**: Allow students to submit issues in local vernaculars, translated instantly by the LLM layer.
- **Predictive Asset Scheduling**: Use long-term complaint history logs to schedule preventive maintenance on aging HVACs or pumps before failures occur.
