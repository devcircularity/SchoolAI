SchoolOps AI — Alpha 1 (FastAPI + PostgreSQL + Ollama)

Chat‑first school management backend for Kenyan CBC schools. Multi‑tenant (per‑school isolation via Postgres RLS), with helpers to bootstrap fee structures, GL accounts, and CBC grade levels. Alpha scope covers: Schools, Classes, Students (+Guardians), Fee Structures & Invoices, Payments (with minimal GL), Notifications, and a chat interface powered by Ollama.

⸻

Tech Stack
	•	API: FastAPI (Python 3.11+)
	•	DB: PostgreSQL + SQLAlchemy 2.0 + Alembic
	•	Auth: JWT (HS256)
	•	Tenancy: Single DB, Row‑Level Security per school_id
	•	AI: Ollama (local LLM), simple intent router + tool calls
	•	Other: Pydantic v2, httpx, passlib(bcrypt)

⸻

File Structure (Alpha 1)

school-ai-backend/
├── app/
│   ├── api/
│   │   ├── deps/
│   │   │   ├── auth.py                # JWT auth dependency + RLS context
│   │   │   └── tenancy.py             # X-School-ID resolver + membership check
│   │   └── routers/
│   │       ├── auth.py                # register/login
│   │       ├── schools.py             # create school + bootstrap helper
│   │       ├── classes.py             # classes CRUD (alpha: create + list)
│   │       ├── guardians.py           # guardians CRUD (alpha: create + list)
│   │       ├── students.py            # students (create, list, patch class/status)
│   │       ├── fees.py                # list fee structures
│   │       ├── invoices.py            # generate, list, lines
│   │       ├── payments.py            # create + list payments
│   │       ├── notifications.py       # queue/send (IN_APP)
│   │       └── chats.py               # chat sessions + messages
│   ├── core/
│   │   ├── config.py                  # env settings
│   │   ├── db.py                      # engine/session + set_config(...) for RLS
│   │   └── security.py                # hashing + JWT encode/decode
│   ├── models/
│   │   ├── base.py
│   │   ├── user.py                    # basic user + roles_csv
│   │   ├── school.py                  # School, SchoolMember
│   │   ├── class.py                   # Class
│   │   ├── guardian.py                # Guardian
│   │   ├── student.py                 # Student
│   │   ├── student_guardian.py        # link table
│   │   ├── fee.py                     # FeeStructure, FeeItem
│   │   ├── payment.py                 # Invoice, InvoiceLine, Payment
│   │   ├── accounting.py              # GLAccount, JournalEntry, JournalLine
│   │   ├── notification.py            # Notification
│   │   └── chat.py                    # ChatSession, ChatMessage
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── school.py
│   │   ├── class.py
│   │   ├── guardian.py
│   │   ├── student.py                 # StudentCreate, StudentUpdate, StudentOut
│   │   ├── fee.py
│   │   ├── invoice.py
│   │   ├── payment.py
│   │   ├── notification.py
│   │   └── chat.py
│   ├── services/
│   │   ├── helpers/
│   │   │   ├── bootstrap_school.py    # GL + CBC levels + default fee template
│   │   │   └── cbc.py                 # (reserved for grade metadata)
│   │   ├── fees.py                    # invoice generation from fee structures
│   │   ├── payments.py                # payment posting + GL
│   │   ├── notifications.py           # queue + deliver (IN_APP)
│   │   └── ai/
│   │       ├── ollama_client.py       # /api/generate wrapper
│   │       ├── prompt_templates.py    # system prompt + intent keywords
│   │       └── orchestrator.py        # intent routing + tool calls
│   ├── main.py                        # FastAPI app factory + routers
│   └── __init__.py
├── migrations/                        # Alembic env + versions
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── .env.example
├── alembic.ini
├── pyproject.toml
├── requirements.txt                   # optional freeze
└── README.md


⸻

Setup
	1.	Python & venv

python -m venv .venv && source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt  # or: pip install fastapi "uvicorn[standard]" sqlalchemy psycopg[binary] alembic pydantic pydantic-settings passlib[bcrypt] PyJWT python-multipart httpx


	2.	Environment

cp .env.example .env
# Edit DB + JWT secret + Ollama settings

.env.example (excerpt):

ENV=dev
API_HOST=0.0.0.0
API_PORT=8000
DATABASE_URL=postgresql+psycopg://school_user:school_pass@localhost:5432/school_ai
JWT_SECRET=change_me
JWT_ALG=HS256
JWT_EXPIRES_MINUTES=60
REFRESH_EXPIRES_DAYS=7
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b


	3.	Database & Migrations (run these last when adding new scripts)

alembic upgrade head


	4.	Run API

uvicorn app.main:app --reload --port 8000


	5.	Ollama (optional for chat)

ollama serve
ollama pull llama3.1:8b
# Ensure OLLAMA_BASE_URL and OLLAMA_MODEL match your setup



⸻

Multi‑Tenancy & RLS
	•	Every table stores school_id.
	•	On each request we set transaction‑local variables using:

SELECT set_config('app.current_user_id', :id, true);
SELECT set_config('app.current_school_id', :id, true);


	•	RLS policies restrict all CRUD to rows with school_id = current_setting('app.current_school_id', true).

Important header: all tenant‑scoped routes require
X-School-ID: <your-school-id>

⸻

Bootstrap on School Creation

When you POST /schools, we automatically:
	•	Create minimal GL accounts: 1000 Cash & Bank, 1100 Accounts Receivable, 2000 Unearned Revenue, 4000+ income heads, 5000+ expenses.
	•	Preload CBC grade levels: PP1, PP2, Grade 1–6, JSS 7–9, Senior 10–12.
	•	Create a default fee structure (Term 1, editable): Tuition, Activity Fee, Exam Fee (+ optional Lunch, Transport).

⸻

Auth
	•	POST /auth/register → returns access_token (JWT)
	•	POST /auth/login → returns access_token
	•	Bearer: Authorization: Bearer <token>

JWT claims include sub (user id), roles, and optional active_school_id.

⸻

Core Endpoints (Alpha)

Schools
	•	POST /schools → create school + bootstrap (requires auth)
	•	GET /schools/my (optional in later versions)

Classes
	•	POST /classes (X‑School‑ID)
	•	GET /classes (X‑School‑ID)

Guardians
	•	POST /guardians (X‑School‑ID)
	•	GET /guardians (X‑School‑ID)

Students
	•	POST /students (X‑School‑ID) — can inline create primary guardian
	•	GET /students (X‑School‑ID)
	•	PATCH /students/{id} (X‑School‑ID) — assign class, update status

Fees & Invoices
	•	GET /fees/structures (X‑School‑ID)
	•	POST /invoices/generate (X‑School‑ID) — by student_id or class_id
	•	GET /invoices (X‑School‑ID)
	•	GET /invoices/{invoice_id}/lines (X‑School‑ID)

Payments
	•	POST /payments (X‑School‑ID) — records payment + GL posting
	•	GET /payments (X‑School‑ID)

Notifications
	•	POST /notifications/send (X‑School‑ID) — IN_APP (immediate SENT), EMAIL (queued)
	•	GET /notifications (X‑School‑ID)

Chat (AI)
	•	POST /chats (X‑School‑ID) → create session
	•	GET /chats/{id}/messages (X‑School‑ID) → history
	•	POST /chats/{id}/messages (X‑School‑ID) → send message; routes intents:
	•	“generate invoices for class …”
	•	“record payment …”
	•	“notify guardians about fee balances”
	•	falls back to Ollama for general replies
	•	(Optional convenience) POST /chat if you added the one‑shot endpoint.

⸻

Quick Start (Smoke Test)

# 1) Register and capture token
TOKEN=$(curl -sX POST http://localhost:8000/auth/register \
  -H "content-type: application/json" \
  -d '{"email":"owner@example.com","full_name":"Owner","password":"pass123"}' \
  | jq -r .access_token)

# 2) Create a school (bootstraps GL + CBC + fee template)
SCHOOL=$(curl -sX POST http://localhost:8000/schools \
  -H "Authorization: Bearer $TOKEN" \
  -H "content-type: application/json" \
  -d '{"name":"Imara Academy","address":"Nairobi","contact":"+2547..."}')
SCHOOL_ID=$(jq -r .id <<< "$SCHOOL")

# 3) Create a class
CLASS_ID=$(curl -sX POST http://localhost:8000/classes \
  -H "Authorization: Bearer $TOKEN" -H "X-School-ID: $SCHOOL_ID" \
  -H "content-type: application/json" \
  -d '{"name":"Grade 4 East","level":"Grade 4","academic_year":"2025","stream":"East"}' | jq -r .id)

# 4) Create guardian
GUARDIAN_ID=$(curl -sX POST http://localhost:8000/guardians \
  -H "Authorization: Bearer $TOKEN" -H "X-School-ID: $SCHOOL_ID" \
  -H "content-type: application/json" \
  -d '{"first_name":"Jane","last_name":"Doe","email":"jane@example.com","phone":"+254712345678","relationship":"Mother"}' | jq -r .id)

# 5) Enroll student + set class
STUDENT_ID=$(curl -sX POST http://localhost:8000/students \
  -H "Authorization: Bearer $TOKEN" -H "X-School-ID: $SCHOOL_ID" \
  -H "content-type: application/json" \
  -d '{"admission_no":"ADM-2025-001","first_name":"John","last_name":"Doe","gender":"Male","primary_guardian_id":"'"$GUARDIAN_ID"'"}' | jq -r .id)

curl -sX PATCH http://localhost:8000/students/$STUDENT_ID \
  -H "Authorization: Bearer $TOKEN" -H "X-School-ID: $SCHOOL_ID" \
  -H "content-type: application/json" -d '{"class_id":"'"$CLASS_ID"'"}' | jq

# 6) Generate invoice for class (Term 1)
curl -sX POST http://localhost:8000/invoices/generate \
  -H "Authorization: Bearer $TOKEN" -H "X-School-ID: $SCHOOL_ID" \
  -H "content-type: application/json" \
  -d '{"class_id":"'"$CLASS_ID"'","term":1,"year":2025,"include_optional":{"Lunch":true,"Transport":false}}' | jq

# 7) Record a payment
INVOICE_ID=$(curl -s http://localhost:8000/invoices -H "Authorization: Bearer $TOKEN" -H "X-School-ID: $SCHOOL_ID" | jq -r '.[0].id')
curl -sX POST http://localhost:8000/payments \
  -H "Authorization: Bearer $TOKEN" -H "X-School-ID: $SCHOOL_ID" \
  -H "content-type: application/json" \
  -d '{"invoice_id":"'"$INVOICE_ID"'","amount":10000,"method":"MPESA","txn_ref":"MPESA-DEMO-001"}' | jq

# 8) Notifications (in-app)
curl -sX POST http://localhost:8000/notifications/send \
  -H "Authorization: Bearer $TOKEN" -H "X-School-ID: $SCHOOL_ID" \
  -H "content-type: application/json" \
  -d '{"type":"IN_APP","subject":"Reminder","body":"Fees due next week"}' | jq

# 9) Chat (session + message)
SESSION_ID=$(curl -sX POST http://localhost:8000/chats \
  -H "Authorization: Bearer $TOKEN" -H "X-School-ID: $SCHOOL_ID" \
  -H "content-type: application/json" \
  -d '{"title":"Ops Desk"}' | jq -r .id)

curl -sX POST http://localhost:8000/chats/$SESSION_ID/messages \
  -H "Authorization: Bearer $TOKEN" -H "X-School-ID: $SCHOOL_ID" \
  -H "content-type: application/json" \
  -d '{"content":"Generate invoices for class Grade 4 East"}' | jq


⸻

Accounting (Alpha rules)
	•	Issue invoice: DR Accounts Receivable (1100) / CR Income (per fee items) — (Rudimentary in alpha; recognition summarized into invoice totals)
	•	Record payment: DR Cash & Bank (1000) / CR Accounts Receivable (1100)
	•	All journal rows scoped by school_id.

⸻

Common Gotchas
	•	“Invalid token” / 401 — ensure you pass Authorization: Bearer <token>.
	•	“School not selected” / 400 — you must send X-School-ID for tenant routes.
	•	RLS/permission returning empty — your user must be a member of the school (created automatically as OWNER on POST /schools).
	•	SET LOCAL ... parameter error — we use set_config() (already patched).
	•	“relation … does not exist” — run alembic upgrade head.

⸻

Roadmap (Post‑Alpha)
	•	AI tool calls that persist from natural language (create class/student, targeted invoices/payments).
	•	Guardian portal + payment links (M‑Pesa/Pesapal webhooks).
	•	Background worker for notifications and heavy AI tasks.
	•	Audit logs, importers, and richer accounting.

⸻

License

TBD (choose one: MIT/Apache‑2.0).