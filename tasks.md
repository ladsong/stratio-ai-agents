
Build Plan

Phase 0 — Repo intake, decisions, and target shape (0.5–1 day)

Goal: Fork Nanobot, freeze a baseline, and decide what gets kept vs replaced.

Tasks
	1.	Fork HKUDS/nanobot and create a new repo: nanobot-backend (or your product name).  ￼
	2.	Add a docs/ARCHITECTURE.md with the target components:
	•	gateway (Nanobot-derived control plane)
	•	runtime (LangGraph)
	•	worker (async jobs)
	•	postgres, redis (compose services)
	3.	Define the MVP API contract (endpoints list) in docs/openapi-draft.md.
	4.	Decide the “source of truth”: Postgres (threads/events/runs/artifacts/tool_calls).

Deliverables
	•	Forked repo
	•	docs/ARCHITECTURE.md
	•	docs/openapi-draft.md

⸻

Phase 1 — Monorepo restructure + bootable Docker Compose (1–2 days)

Goal: Make the project boot locally in Compose with placeholders for each service.

Tasks
	1.	Restructure into:

apps/gateway
apps/runtime
apps/worker
packages/core
infra/
docker-compose.yml
.env.example
Makefile


	2.	Create Dockerfiles for:
	•	apps/gateway/Dockerfile
	•	apps/runtime/Dockerfile
	•	apps/worker/Dockerfile
	3.	Create docker-compose.yml with services:
	•	postgres (enable pgvector)
	•	redis
	•	gateway
	•	runtime
	•	worker
	4.	Add healthchecks and dependency ordering.
	5.	Add Makefile targets: up, down, logs, ps.

Notes
	•	Nanobot already ships Docker Compose in-repo; use it as a starting point but rewire services around your new split.  ￼
	•	Compose is the right tool for this multi-container local stack.  ￼

Deliverables
	•	docker-compose.yml boots all services
	•	Health endpoints stubbed: GET /health, GET /ready in gateway

⸻

Phase 2 — Core DB layer + migrations (Postgres as source of truth) (1–2 days)

Goal: Implement DB schema + migrations + repositories in packages/core.

Tasks
	1.	Add SQLAlchemy + Alembic (or your preferred migration tool).
	2.	Create initial tables:
	•	threads, events, runs, run_approvals, artifacts, tool_calls
	•	knowledge_documents, knowledge_chunks (with pgvector vector column)
	•	graph_registry, tool_registry
	3.	Add packages/core/db/ (engine, session management, settings).
	4.	Add minimal seed script: creates one thread and one graph/tool registry entry.

Notes
	•	Enable pgvector for embeddings inside Postgres (keep retrieval simple first).  ￼

Deliverables
	•	alembic configured + initial migration
	•	make migrate, make seed working

⸻

Phase 3 — Gateway API (Lovable-facing contract) (2–3 days)

Goal: Implement the REST API your Lovable app will call.

Tasks
	1.	Build FastAPI app in apps/gateway.
	2.	Implement endpoints (MVP):
	•	Threads: POST /api/v1/threads, GET /api/v1/threads/{id}
	•	Events: POST/GET /api/v1/threads/{id}/events (idempotency key)
	•	Runs: POST /api/v1/runs, GET /api/v1/runs/{id}, GET /api/v1/runs/{id}/state
	•	Approval: POST /api/v1/runs/{id}/approve|reject|resume
	•	Artifacts: GET /api/v1/artifacts/{id}
	•	Registry: GET /api/v1/tools, GET /api/v1/graphs
	3.	Add auth (MVP): static bearer token from env.
	4.	Add CORS config from env (Lovable will call it).
	5.	Add structured logging with correlation/request id.

Notes
	•	Lovable supports connecting to external APIs and MCP servers; your MVP should be API-first.  ￼

Deliverables
	•	Gateway OpenAPI published at /docs
	•	All endpoints wired to DB repositories
	•	Basic auth + CORS

⸻

Phase 4 — LangGraph Runtime service (durable execution + interrupts) (2–4 days)

Goal: Implement the workflow “brain” in a separate service.

Tasks
	1.	Create apps/runtime service that:
	•	registers graphs by name (from code + graph_registry)
	•	can start a run for thread_id
	•	persists checkpoints/state
	2.	Implement at least one end-to-end graph:
	•	conversation_router_graph → routes to strategy_synthesis_graph
	•	strategy_synthesis_graph → creates an artifact
	3.	Implement interrupt-based approval:
	•	a node calls interrupt(payload) when approval is needed
	•	runtime persists state and returns “waiting_approval”
	•	gateway approve/resume sends the response back to resume execution

Notes
	•	LangGraph durable execution: resume without redoing completed steps.  ￼
	•	LangGraph interrupts: pause indefinitely, persist state, resume later.  ￼

Deliverables
	•	runtime container runs graphs
	•	One graph completes end-to-end
	•	One graph pauses for approval and resumes correctly

⸻

Phase 5 — Worker + async execution (queue-backed runs) (2–3 days)

Goal: Make runs async so the gateway returns quickly and the run completes in background.

Tasks
	1.	Introduce Redis-backed job queue (Celery/Dramatiq/RQ—pick one).
	2.	Gateway POST /runs:
	•	creates run row in DB
	•	enqueues job
	•	returns run_id immediately
	3.	Worker consumes queue:
	•	calls runtime to execute graph
	•	updates run status and artifacts
	4.	Add polling endpoints already defined in Phase 3.

Notes
	•	For “must-run” background jobs, you want a real worker/queue rather than relying on in-process background tasks.  ￼

Deliverables
	•	Runs execute asynchronously
	•	Gateway remains responsive
	•	Worker logs show run lifecycle clearly

⸻

Phase 6 — Tool Registry (curated tools + tool_calls logging) (2–4 days)

Goal: Replace “open skills” with a controlled tool system.

Tasks
	1.	Implement tool_registry table + config loader.
	2.	Define tool interface:
	•	name, schema, timeout, retries, permission tag
	3.	Create MVP tools:
	•	postgres_query_tool, vector_search_tool, document_lookup_tool
	•	artifact_writer_tool (writes artifact record)
	•	mock_browser_research_tool (stub)
	4.	Log every tool call into tool_calls with timings + error.

Deliverables
	•	Tools listed at GET /api/v1/tools
	•	Tool calls visible per run
	•	Failure paths recorded

⸻

Phase 7 — Knowledge ingestion (minimal, then expand) (2–4 days)

Goal: Support your “RAG later” without overbuilding now.

Tasks
	1.	Add endpoint (optional MVP): POST /api/v1/knowledge/documents
	•	accepts raw text (or file metadata only)
	•	stores knowledge_documents
	2.	Add chunking job:
	•	splits document into chunks
	•	stores knowledge_chunks
	3.	Add embedding job (optional in MVP; can be stubbed):
	•	writes embedding vector to pgvector column

Deliverables
	•	Basic document ingestion + chunk storage
	•	Vector search tool can query chunks when embeddings exist

⸻

Phase 8 — Lovable integration checklist (1 day)

Goal: Make it trivial to connect the Lovable frontend.

Tasks
	1.	Document API usage with sample requests in docs/LOVABLE_INTEGRATION.md
	2.	Provide:
	•	base URL
	•	auth header format
	•	example flows: create thread → post event → create run → poll → approve → fetch artifact
	3.	Add CORS examples for Lovable domains.

Notes
	•	Lovable docs emphasize connecting apps to external APIs and MCP servers securely.  ￼

Deliverables
	•	Copy/paste integration guide for Lovable
	•	Sample JSON payloads and response shapes

⸻

Phase 9 — Tests, DX polish, and “production-ish” hardening (ongoing; 2–5 days initial)

Goal: Ensure the backend is stable enough to iterate quickly.

Tasks
	1.	Unit tests:
	•	repositories
	•	tool wrappers
	•	graph nodes
	2.	Integration tests:
	•	thread → event → run → artifact
	•	interrupt → approve → resume → artifact
	3.	Add make test, make lint, make format.
	4.	Add observability basics:
	•	structured logs
	•	run status transitions
	•	error traces in DB

Deliverables
	•	CI-ready test suite
	•	Clear README for bring-up

⸻

What you should implement first (the “fast path”)

If you want to see value quickly:
	1.	Phase 1 (Compose boots)
	2.	Phase 2 (DB + migrations)
	3.	Phase 3 (Gateway endpoints)
	4.	Phase 4 (One LangGraph workflow + interrupt/resume)

That gives you the full “OpenClaw-like shape” (gateway + state + workflow + approvals) with minimal surface area, using LangGraph’s durable execution and interrupts for the exact HITL behavior you want.  ￼

⸻

Optional: MCP interface (later)

Once the API integration is solid, you can optionally expose parts of the backend as an MCP server so Lovable can treat it as a “personal connector,” but I’d do this after the REST API is stable. Lovable supports MCP servers as connectors.  ￼

⸻

If you want, paste the exact Nanobot commit/tag you plan to fork (or the repo URL you forked), and I’ll convert this plan into a Windsurf task file (checklist + file map + incremental prompts per phase) so it generates code in smaller, safer chunks.