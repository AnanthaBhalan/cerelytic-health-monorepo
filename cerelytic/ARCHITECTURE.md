# Architecture Overview: Cerelytic v1

## 1. High-Level Strategy
**Goal:** A scalable, secure SaaS platform for analyzing medical bills against PM-JAY and insurance compliance standards.
**Philosophy:** "Clean separation of Product UI and ML Core."
**Infrastructure:** Cloud-agnostic containerized services (Docker), currently targeting AWS/GCP (Cloud Run/ECS).

## 2. System Components

### A. Frontend (The Product)
* **Stack:** Next.js 15 (App Router), TypeScript, TailwindCSS, shadcn/ui.
* **Responsibility:**
    * Landing pages (SEO).
    * User Dashboard (Client Components).
    * File upload handling (Direct-to-storage via signed URLs).
    * Result visualization (Red/Green flags, cost breakdowns).
* **Hosting:** Vercel (MVP) or Docker container.

### B. Service 1: Application API (The Manager)
* **Stack:** Python (FastAPI).
* **Responsibility:**
    * **Orchestration:** Manages user sessions, billing logic, and analysis requests.
    * **Data Integrity:** Enforces RBAC (User vs. Admin).
    * **Integration:** Provides REST endpoints for external partners.
* **Key Pattern:** Does *not* perform OCR. It dispatches jobs to the Queue.

### C. Service 2: ML & OCR Engine (The Worker)
* **Stack:** Python (FastAPI wrapper for endpoints, but primarily a Worker process).
* **Libraries:** `pytesseract` / `pdfplumber` (OCR), `LangChain` / `LiteLLM` (LLM Abstraction).
* **Responsibility:**
    * Listens for `analysis_jobs`.
    * Retrieves file from Blob Storage.
    * Performs OCR and Text Structuring.
    * Runs LLM compliance checks (PM-JAY rules).
    * Writes results back to Database.

### D. Data & Storage
* **Primary DB:** PostgreSQL (via Supabase).
* **Blob Storage:** S3-compatible (via Supabase Storage/AWS S3).
* **Queue/Broker:** Redis (for async communication between API and ML).

## 3. Data Model (Core Schemas)

| Table | Description | Key Fields |
| :--- | :--- | :--- |
| `users` | Auth & Profile | `id`, `email`, `role` (user/admin), `created_at` |
| `bills` | The core record | `id`, `user_id`, `status` (processing/completed/failed), `file_url`, `metadata` |
| `analyses` | ML Outputs | `id`, `bill_id`, `fraud_score`, `line_items` (JSONB), `compliance_flags` (JSONB) |
| `audit_logs` | Security/Compliance | `id`, `actor_id`, `action`, `timestamp`, `resource_id` |

## 4. Async Job Pattern

The system uses an asynchronous job processing pattern to handle bill analysis:

1. **Bill Creation:** `POST /bills` creates a bill record, enqueues an `analysis_job` in Redis, and returns the `billId`.
2. **Job Processing:** The Worker service pulls jobs from the Redis queue, performs OCR and analysis, and updates the database with results.
3. **Result Retrieval:** `GET /bills/{billId}` returns the current status and analysis results when ready.

This pattern ensures:
- Non-blocking API responses
- Scalable processing of resource-intensive OCR/ML tasks
- Retry mechanisms for failed jobs
- Clear separation between request handling and processing

## 5. Security & Compliance
* **Auth:** JWT via Supabase Auth.
* **RLS (Row Level Security):** Enforced at the Database level. Users can only `SELECT` rows where `user_id == auth.uid()`.
* **PII/PHI:** Files are stored with strict retention policies (TTL). PDF files are accessed via short-lived Signed URLs only.

## 6. Observability
* **Logs:** JSON structured logging (stdout/stderr).
* **Tracing:** OpenTelemetry (ready for Datadog/Grafana integration).
* **Health Checks:** `/healthz` endpoints on all services.

## 7. Development Workflow
* **Repo Structure:** Monorepo (recommended) or Polyrepo.
* **CI/CD:** GitHub Actions.
    * On PR: Lint, Type Check, Unit Test.
    * On Merge: Build Docker Image -> Push to Registry -> Deploy.
