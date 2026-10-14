# B.Tech Project & Resume Deliverables
## AI-Powered Smart College Complaint & Maintenance Management System

This document contains professional content tailored for your resume, project submissions, presentations, and interviews.

---

## 1. Resume Description (2-Line Summary)
Developed a full-stack, AI-powered facilities ticketing platform utilizing a decoupled React and Flask-RESTful architecture to streamline campus maintenance. Features an intelligent hybrid NLP routing classifier and a support chatbot that automates category classification, priority assignment, and student query resolution.

---

## 2. Strong Resume Bullet Points
- **Architected Full-Stack SaaS Application**: Built a production-quality, role-based maintenance management platform using **React.js (Vite)** and **Flask (Python)**, enabling secure access control for 1000+ student users, estates staff, and administrators.
- **Implemented Hybrid AI Ticketing Pipeline**: Integrated **Google Gemini API** with a local **TF-IDF & Cosine Similarity** NLP fallback model to automatically classify complaints into 10 categories, predict priority levels, and route tickets with $>85\%$ classification confidence.
- **Engineered Conversational AI Assistant**: Created **CollegeAssist AI**, a custom FAQ matching chatbot using vector space math (Cosine Similarity) in pure Python, resolving student inquiries on transport, library, and hostel guidelines.
- **Aggregated Real-time Analytics Metrics**: Developed administrative telemetry charts using **Recharts (SVG)**, providing analytics on repair velocity trends, satisfaction indices, and category workloads to optimize resource allocation.
- **Implemented Secure RBAC & Sessions**: Enforced secure password hashing, file uploads validations (UUID naming & MIME verification), CORS configurations, and token-based authentication via **Flask-JWT-Extended**.

---

## 3. Technologies Used
- **Frontend**: React.js, Vite, Axios, React Router, Recharts, Lucide Icons, HTML5, Vanilla CSS3 (Custom Glassmorphic Dark Theme).
- **Backend**: Python, Flask, Flask-SQLAlchemy, Flask-JWT-Extended, Flask-Cors, PyMySQL, Cryptography.
- **Database**: MySQL.
- **AI/ML**: Natural Language Processing (NLP), TF-IDF Tokenizer, Vector Space Cosine Similarity, Google Gemini Pro LLM API.

---

## 4. AI Features Implemented
1. **Automated Ticket Classification**: Computes TF-IDF similarity vectors between incoming complaint descriptions and category corpora, identifying the best category (e.g. Electrical, Plumbing).
2. **Urgency Priority Estimation**: Parses descriptions for specific safety and operational keywords (e.g., spark, shock, leak) to assign priority status (Low, Medium, High, Urgent).
3. **Suggested Department Routing**: Auto-routes tickets to respective maintenance departments based on category mappings.
4. **Duplicate Ticket Detection**: Computes cosine text similarity between new and active complaints, flagging items with $>0.75$ similarity score to reduce redundant workloads.
5. **Conversational Assistant (CollegeAssist AI)**: Matches student questions to campus policy databases using NLP similarity, with standard stubs fallback.
6. **Ticket Summarization**: Converts verbose status logs and histories into concise, two-sentence administrator cards using Gemini prompts.

---

## 5. Project Presentation/PPT Slide Content

### Slide 1: Title
- **Title**: AI-Powered Smart College Complaint & Maintenance Management System
- **Subtitle**: Automated Estates Management & AI Routing Platform
- **Presenter**: [Your Name], B.Tech Computer Science & Engineering

### Slide 2: The Problem
- Manual ticketing leads to slow dispatching and unresolved bottlenecks.
- Critical safety issues (electrical sparking, gas leak) get queued behind minor problems (dusty tables).
- Lack of audit trails, verification logs, and satisfaction trackers for students.

### Slide 3: The Solution (CampusCare)
- A decoupled, responsive full-stack platform with custom portals for Students, Staff, and Admins.
- Hybrid AI service combining local NLP similarity vectors with Google Gemini APIs.
- Integrated photo attachments, notifications, and satisfaction rating loops.

### Slide 4: System Architecture
- **Client**: React SPA, Recharts Dashboard, JWT Interceptors.
- **Server**: Flask REST API, Role-Based Access Control (RBAC), SQLAlchemy ORM.
- **Database**: MySQL schemas.
- **AI Engine**: TF-IDF similarity vector models and LLM API wrappers.

### Slide 5: AI Engine Deep Dive
- **Local Fallback**: Zero-dependency TF-IDF vectorizer + Cosine Similarity mapping.
- **LLM Prompting**: JSON-schema responses using structured prompts on `gemini-1.5-flash`.
- **Department Routing**: Automatic specialization assignments.

### Slide 6: Database Entity Design
- 11 relational tables: `users`, `students`, `staff`, `admins`, `complaint_categories`, `complaints`, `complaint_assignments`, `complaint_history`, `notifications`, `feedback`, `chatbot_messages`.
- Proper constraints, indexes, timestamps, and cascade updates.

### Slide 7: E2E Demonstration Flow
- **Submit**: Student submits description, AI predicts priority/department.
- **Route**: Admin views analytics and assigns to specialized staff.
- **Resolve**: Staff accepts task, logs resolution details.
- **Review**: Student submits satisfaction ratings; ticket automatically closes.

### Slide 8: Future Scope & Enhancements
- WebSockets for push notifications.
- Preventive maintenance schedules based on ticket logs.
- Speech-to-text ticket submission for accessibility.

---

## 6. B.Tech Project Abstract
Effective facilities management is crucial for academic productivity and safety in university campuses. Traditional complaint logging processes are manual, slow, and lack transparency. This project presents the design and implementation of the **AI-Powered Smart College Complaint & Maintenance Management System**, a production-grade full-stack platform that automates the ticket lifecycle. 

The system leverages a hybrid AI model: utilizing a zero-dependency local NLP engine based on Term Frequency-Inverse Document Frequency (TF-IDF) and Cosine Similarity, with automated API fallbacks to large language models (LLMs) like Google Gemini. When a student lodges a complaint, the system automatically classifies the category, estimates its urgency level (Low to Urgent), and routes the ticket to the suggested department. Administrators can assign tasks to specialized maintenance engineers, who accept and mark repairs as resolved with work proof logs. Built with a React SPA frontend, a Flask REST API backend, and a MySQL relational database, this system improves resolution times, automates resource dispatching, and ensures campus maintenance issues are handled efficiently.

---

## 7. B.Tech Project Objectives
- To design a secure, role-based web application with separate dashboards for Students, Maintenance Staff, and Administrators.
- To implement an automated classification system that maps unstructured text descriptions to distinct maintenance categories.
- To build a priority estimation algorithm that flags safety hazards for immediate dispatch.
- To establish an intelligent chatbot interface to answer student concerns regarding university operations and transport schedules.
- To provide administrative analytics showing trend lines, workload distributions, and worker performance metrics.
- To enforce production-grade security standards including password hashing, JWT authorization, file upload sanitizations, and SQL injection protection.

---

## 8. Interview Explanation (Elevator Pitch)
"For my project, I built an **AI-Powered College Complaint and Maintenance Management System**. The goal was to solve campus operational delays by automating ticket routing. I used a decoupled architecture: React on the frontend and Python Flask on the backend, backed by MySQL. The core innovation is in the AI layer: I built a hybrid engine that automatically categorizes issues and sets priorities. If an external API like Gemini is available, it uses the LLM; otherwise, it falls back to a local NLP model I wrote using TF-IDF and Cosine Similarity. The system handles the entire lifecycle: students log tickets, admins route them to staff, staff resolve them with work logs, and students close them with feedback. I also integrated Recharts for administrative analytics and built an FAQ chatbot to handle campus queries."

---

## 9. Technical Q&A for Interviews

### Q1: Why did you choose a hybrid AI architecture instead of relying solely on an LLM API?
**Answer**: Relying solely on external APIs (like Gemini or OpenAI) introduces concerns around API limits, costs, network latency, and offline availability. By designing a hybrid engine, the system operates reliably out-of-the-box using the local TF-IDF Cosine Similarity model. If an API key is provided, it upgrades to use the LLM for advanced summarizations and semantic chat, showcasing production-quality modular design.

### Q2: How does your local NLP Classifier work?
**Answer**: The local NLP Classifier works in three steps:
1. **Tokenization**: It cleans the input text (lowering, removing punctuation) and splits it into keywords.
2. **Vector Space Mapping**: It computes the Term Frequency (TF) of these keywords and maps them against standard pre-defined category text templates.
3. **Similarity**: It calculates the Cosine Similarity between the query vector and category vectors. The category with the highest cosine score is selected. Priority is predicted using sentiment-urgency keyword matching.

### Q3: How did you implement secure file uploads on Windows?
**Answer**: I used Werkzeug's `secure_filename` to sanitize filenames, removing special characters that could lead to path traversal attacks. To prevent collisions, I generate a unique UUIDv4 string and append the original file extension. I also limit file sizes to 16MB and validate that the MIME type is an allowed image format (PNG, JPG, JPEG, GIF).

### Q4: How is Role-Based Access Control (RBAC) enforced on the backend?
**Answer**: It is enforced using JWT claims. When a user logs in, Flask-JWT-Extended generates a token containing additional claims (like the user's role: student, staff, admin). On protected routes, we use the `@jwt_required()` decorator and check the role claim in the token using `get_jwt().get('role')`. If the role is unauthorized for that endpoint, we return a 403 Forbidden response.

### Q5: What is the benefit of using React Context API for Authentication?
**Answer**: The React Context API (`AuthContext`) creates a global state provider for user authentication. This prevents "prop drilling," allowing any nested component (like navbars or dashboards) to access the logged-in user's details, role, and logout functions. It also handles local storage synchronization and JWT header injection automatically.
