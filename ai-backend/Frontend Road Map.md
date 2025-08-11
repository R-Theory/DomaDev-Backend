---

kanban-plugin: board

---

## Ready

- [ ] 


## Blocked

- [ ] 


## Now — Phase 2.5: Local Chat Storage Integration

- [ ] [P1][M] Replace Zustand persist with server sync: offline-first with conflict resolution #Storage
- [ ] [P1][S] Chat sync UI: loading states, sync indicators, conflict resolution dialogs #Storage
- [ ] [P1][S] Conversation list sync: real-time updates when conversations change on server #Storage
- [ ] [P1][S] Message sync: incremental loading of conversation history from server #Storage
- [ ] [P1][S] Offline mode: queue messages when offline, sync when reconnected #Storage
- [ ] [P1][S] Migration UI: migrate existing local conversations to server storage #Storage


## Definition of Done — Phase 2.5

- [ ] Conversations persist on server and sync across browser sessions
- [ ] Offline mode works with message queuing and sync on reconnect
- [ ] Migration from local storage to server storage is seamless
- [ ] No data loss during sync conflicts


## Phase 3: Models & Spaces UI

- [ ] [P1][S] Model selector bound to `/api/models` list with sources/latency #Models
- [ ] [P1][M] Model Profiles CRUD UI (name, system prompt, default model, params) #Models
- [ ] [P1][M] Spaces CRUD UI (name/description) and link to Model Profiles #Spaces
- [ ] [P1][S] Per‑conversation runtime config UI: model, temperature, system prompt override #Chat
- [ ] [P1][S] Model allowlist UI: gray out blocked models, explain why #Models #Gateway


## Phase 4: Flow Canvas UI

- [ ] [P2][M] React Flow canvas scaffold (node/edge basic types) #Flow
- [ ] [P2][M] Node types: Agent node, Tool node, Model node (placeholders) #Flow
- [ ] [P2][S] Flow save/load UI: export/import JSON, save to server #Flow
- [ ] [P2][S] Flow execution UI: run button, progress indicators, results display #Flow


## Phase 5: Data Manager UI

- [ ] [P2][M] Local embeddings selection UI (small model) #RAG
- [ ] [P2][L] Vector store management UI: index status, document counts #RAG
- [ ] [P2][L] Document ingestion UI: drag-drop, progress bars, file type support #RAG
- [ ] [P2][M] Retrieval config UI: k-value, filters, attach to chat as context #RAG #Chat
- [ ] [P2][M] File system browser UI: safe sandbox, read-only initially #Drive


## Phase 6: Training UI

- [ ] [P3][M] Tuning job runner UI: queue with pause/resume, job status #Training
- [ ] [P3][L] PEFT/LoRA workflow UI: parameter config, checkpoint management #Training
- [ ] [P3][M] Evaluation UI: BLEU/ROUGE metrics, comparison views #Training
- [ ] [P3][S] Model registry UI: register tuned artifacts for selection #Models


## Done

- [x] Phase 1: Foundation & Architecture ✅
- [x] Phase 2: Chat Excellence (Streaming, UX, Reliability) ✅


%% kanban:settings
```
{"kanban-plugin":"board","list-collapse":[false,false,false,false,false,false,false,false]}
```
%%
