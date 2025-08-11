---

kanban-plugin: board

---

## Ready

- [ ] 


## Blocked

- [ ] 


## Now — Phase 2.5: Chat Storage & Persistence

- [x] [P1][M] SQLite schema design: conversations, messages, metadata tables #Storage
- [x] [P1][M] Chat API endpoints: `/api/conversations` (CRUD), `/api/conversations/{id}/messages` #Storage
- [ ] [P1][S] Database migrations: version control, upgrade scripts, rollback support #Storage
- [x] [P1][M] Extensible storage layer: abstract interface for SQLite/PostgreSQL/cloud backends #Storage
- [x] [P1][S] Backup/restore API: export conversations to JSON, import with deduplication #Storage (export/import MVP)
- [x] [P1][S] Performance optimization: pagination, indexing, lazy loading for large conversations #Storage (indexes, pagination)
- [x] [P1][M] Full-text search (FTS5) over messages #Storage


## Definition of Done — Phase 2.5

- [x] Conversations persist in database and survive server restarts
- [x] API endpoints support full CRUD operations for conversations and messages
- [ ] Migration system handles schema upgrades without data loss
- [x] Performance scales to thousands of conversations and messages (FTS + indexing)


## Phase 3: Models & Spaces API

- [ ] [P1][M] Model Profiles API: `/api/model-profiles` (CRUD operations) #Models
- [ ] [P1][M] Spaces API: `/api/spaces` (CRUD operations) #Spaces
- [ ] [P1][S] Profile ↔ Space association endpoints: link models to spaces #Spaces #Models
- [ ] [P1][S] Model allowlist enforcement: validate models against allowed list #Models #Gateway
- [ ] [P1][S] Model metadata API: sources, latency, capabilities, quantization info #Models


## Phase 4: Flow Execution Engine

- [ ] [P2][M] Flow execution runtime: parse and execute flow definitions #Flow
- [ ] [P2][M] Node execution engine: Agent, Tool, Model node handlers #Flow
- [ ] [P2][S] Flow persistence API: save/load flows to database #Flow
- [ ] [P2][S] Flow execution API: run flows, track progress, return results #Flow
- [ ] [P2][S] Flow validation: check flow integrity, detect cycles, validate connections #Flow


## Phase 5: RAG & Vector Storage

- [ ] [P2][M] Vector store integration: SQLite + sqlite-vss or qdrant-lite #RAG
- [ ] [P2][L] Embeddings API: local model selection, text embedding endpoints #RAG
- [ ] [P2][L] Document ingestion API: process .md, .txt, .pdf, .json with progress #RAG
- [ ] [P2][M] Retrieval API: semantic search, k-nearest neighbors, filtering #RAG
- [ ] [P2][M] File system sandbox API: safe read access to user-selected directories #Drive


## Phase 6: Training Infrastructure

- [ ] [P3][M] Training job queue: job management, pause/resume, status tracking #Training
- [ ] [P3][L] PEFT/LoRA training API: parameter config, checkpoint management #Training
- [ ] [P3][M] Evaluation API: BLEU/ROUGE metrics, comparison endpoints #Training
- [ ] [P3][S] Model registry API: register and manage tuned model artifacts #Models


## Phase 1: Gateway & Routing (Existing)

- [x] [P0][S] Configure multi‑model routes: `MODEL_ROUTE_<KEY>` and defaults #Gateway
- [x] [P0][S] Routing behavior: support `modelKey`; 409 on ambiguity when omitted #Gateway
- [x] [P0][S] Allowlist (`ALLOWED_MODELS`) enforcement with descriptive errors #Gateway
- [ ] [P1][S] SSE heartbeats tuned via `SSE_HEARTBEAT_SECONDS` #Gateway
- [ ] [P1][S] Timeouts and retries (`CONNECT/READ/WRITE/TOTAL_TIMEOUT_SECONDS`) defaults #Gateway
- [ ] [P1][M] Prometheus `/metrics` enabled; basic RED + tokens/sec dashboards #Observability
- [ ] [P1][M] Optional Redis rate limiting (`USE_REDIS`, `RATE_LIMIT_PER_MIN`) #Gateway


## Infrastructure & DevEx

- [ ] [P0][S] Scripts for local bootstrap (frontend+gateway) with single command #DevEx
- [ ] [P0][S] Env templates and validation for frontend and backend (`.env.example`) #DevEx
- [ ] [P0][S] ADRs for major design decisions (routing strategy, SSE, storage) #Decision
- [ ] [P0][S] Minimal tests: API endpoints, database operations, error handling #DevEx
- [ ] [P0][S] Observability doc: using `/metrics`, common failure modes #Observability


## Done

- [x] Basic chat endpoints: `/api/chat`, `/api/chat/stream` ✅
- [x] Basic models endpoint: `/api/models` ✅
- [x] Basic routing and API key authentication ✅


%% kanban:settings
```
{"kanban-plugin":"board","list-collapse":[false,false,false,false,false,false,false,false,false,false]}
```
%%
