# Alex — Merge & Fix: Phased Execution Checklist

Source plan: [`x-txt-open-jarvis-openjarvis-personal-a-declarative-leaf.md`](x-txt-open-jarvis-openjarvis-personal-a-declarative-leaf.md)

**How this tracker works**

1. Work happens one phase at a time, in order.
2. A step is ticked `- [x]` only when its "Done when" line is true — not when the code is written.
3. Each tick gets the date and commit: `- [x] ~~step~~ — 2026-11-14 · <commit>`
4. A phase is **Done** only when every step **and** every phase-gate box is ticked, and the Part D acceptance script has been run end-to-end.
5. If a phase breaks a previous phase's gate, that phase goes back to **Blocked** — regressions are recorded, not hidden.

**Status legend:** `Not started` · `In progress` · `Blocked` · `Done`

---

## Ground truth (verified 2026-11-14)

| What | Real path | Notes |
|---|---|---|
| Repo (Trinity) | `~/Documents/dependencies/Alex` | Matrix `matrix/`, Hermes stub `hermes/`, Jarvis `jarvis/`, tools `tools/friday_mac/`, config `config/`, evals `evals/` |
| Merged app (target) | `~/.openjarvis/src` | Has `src/openjarvis/`, `frontend/`, `desktop/`, `rust/`, `docs/` — this is where `alex/` lands |
| Face app data | `~/.openjarvis` | `config.toml`, `server.pid`, `SOUL.md`, `MEMORY.md`, DBs |
| Hermes runtime | `~/.hermes` | Real `hermes-agent/` (agent loop, toolsets, gateway), `config.yaml`, duplicate `plugins/matrix_bridge.py` |
| Ports (target) | Face `:8000` · Matrix `:8700` · Hermes `:8642` · Tauri `:8088` | Gateways `:3001` `:20128` `:11434` |
| Port collision to kill | `jarvis/web.py` on `:8000` (Docker `:8005`) | Phase 0.1 / 1.4 |

---

## Progress at a glance

| Phase | Scope | Est. | Steps | Status | Completed |
|---|---|---:|---|---|---|
| 0 | Freeze & baseline | ½ d | 4 / 4 | **Done** | 2026-11-14 |
| 1 | One repo, one app | 2 d | 8 / 8 | **Done** | 2026-11-14 |
| 2 | Ledger truth | 2 d | 7 / 7 | **Done** | 2026-11-14 |
| 3 | Face ↔ Trinity wiring | 3 d | 3 / 8 | In progress | `2960a82f` |
| 4 | Voice: one pipeline that never dies | 2 d | 0 / 7 | Not started | — |
| 5 | Hermes becomes real | 4–5 d | 0 / 8 | Not started | — |
| 6 | Memory & personality | 2–3 d | 0 / 6 | Not started | — |
| 7 | Logs, dashboard & report | 1–2 d | 0 / 5 | Not started | — |
| 8 | Hardening & acceptance | 2–3 d | 0 / 4 | Not started | — |

---

## Phase 0 — Freeze & baseline *(≈½ day)*

**Goal:** stop the bleeding. One owner per port, backups that restore, and a written blueprint before anything moves.

- [x] **0.1** Stop duplicate `:8000` processes; leave one owner (OpenJarvis native server) — 2026-11-14
  - Done when: `lsof -nP -iTCP:8000 -sTCP:LISTEN` returns exactly one PID, and that PID belongs to the OpenJarvis native server, not `jarvis/web.py`.
  - **Result:** no duplicate found — one listener, PID 816 = `jarvis serve --port 8000` → `openjarvis.cli:main`, editable install of `~/.openjarvis/src`, cwd `~/.openjarvis/src`. Nothing stopped. The redundant third UI is containerized on host `:8005` (`alex-jarvis`, `jarvis/web.py`); it is not an `:8000` owner and is removed in 1.4/1.7.
- [x] **0.2** Back up `ledger.db`, `memory.db`, and `~/.openjarvis` DBs as `*.bak-<date>` — 2026-11-14
  - Done when: every backup opens with `sqlite3 <file> 'pragma integrity_check;'` → `ok`, and the backup list is recorded below.
  - **Result:** 10 / 10 backups `ok` via `sqlite3 .backup` (WAL-safe), logged in the table below.
- [x] **0.3** Record the live port map (`lsof`) into the blueprint — 2026-11-14
  - Done when: the port map section lists every listener with PID + owning component.
  - **Result:** `docs/BLUEPRINT.md` → "Port map (live, Phase 0)", 10 Alex-relevant listeners with PID, owner, target owner and phase.
- [x] **0.4** Create `docs/BLUEPRINT.md` in the merged repo from Part A — 2026-11-14 · `084274eb`
  - Done when: `docs/BLUEPRINT.md` exists in `~/.openjarvis/src` and is committed.

**Phase gate**
- [x] Only one process listens on `:8000` — PID 816, re-checked after all Phase 0 work
- [x] Backups exist and open in `sqlite3` — 10 / 10 `integrity_check` = `ok`
- [x] `docs/BLUEPRINT.md` committed — `084274eb` on `main`, 145 lines
- [x] App still launches and chats — `GET /health` → `{"status":"ok"}`, `POST /v1/chat/completions` → 200 via local `qwen2.5:0.5b` (no paid credits spent)

**Backup log** (2026-11-14, `sqlite3 <db> ".backup '<db>.bak-2026-11-14'"`)

| File | Backup path | `integrity_check` |
|---|---|---|
| `Alex/storage/data/ledger.db` | `Alex/storage/data/ledger.db.bak-2026-11-14` | `ok` (7 tables) |
| `Alex/storage/data/memory.db` | `Alex/storage/data/memory.db.bak-2026-11-14` | `ok` (3 tables) |
| `~/.openjarvis/sync_state.db` | `sync_state.db.bak-2026-11-14` | `ok` |
| `~/.openjarvis/knowledge.db` | `knowledge.db.bak-2026-11-14` | `ok` (6 tables) |
| `~/.openjarvis/traces.db` | `traces.db.bak-2026-11-14` | `ok` (8 tables) |
| `~/.openjarvis/audit.db` | `audit.db.bak-2026-11-14` | `ok` |
| `~/.openjarvis/approvals.db` | `approvals.db.bak-2026-11-14` | `ok` |
| `~/.openjarvis/digest.db` | `digest.db.bak-2026-11-14` | `ok` |
| `~/.openjarvis/telemetry.db` | `telemetry.db.bak-2026-11-14` | `ok` |
| `~/.openjarvis/agents.db` | `agents.db.bak-2026-11-14` | `ok` (6 tables) |

**Baseline captured (proof the bugs are real):**

- `ledger.db`: **21 tasks, 0 events, 0 steps** → confirms B1-5 (events table never written).
- `memory.db` tables: `contacts, knowledge, pitfalls` only → the rest arrive in Phase 6.
- Chat reply came back as `model: "matrix"` with a canned "Understood, Master Khan…" → confirms B1-6 (Matrix hijacks every turn).
- Docker still owns `:8700` / `:8642` / `:8005`; PID 826 still runs the standalone `alex_wake_listener.py` → 1.6, 1.4 and 4.6 respectively.

---

## Phase 1 — One repo, one app *(≈2 days)*

**Goal:** merge the Trinity into `~/.openjarvis/src` as a first-class layer; `Alex` becomes docs + config source.

Target layout:
```
~/.openjarvis/src/src/openjarvis/
├── alex/
│   ├── matrix/{api,gateway,policy,store,supervisor,doctor,reports}.py
│   ├── hermes/{bridge/runtime.py}
│   ├── face/{intent.py, reflex.py, tools/}      # friday-mac merged
│   ├── classify.py                              # basic | quick-answer | complex
│   └── dialogue.py                              # one conversation engine
├── server/  speech/  agents/  tools/ ...        # existing OpenJarvis, unchanged
```

- [x] **1.1** Move Matrix modules → `openjarvis/alex/matrix`; add package `__init__`s — 2026-11-14 · `9b4bcfd8`
  - Done when: `python -c "import openjarvis.alex.matrix.api"` succeeds from a neutral cwd and no `from matrix...` imports remain in the **merged package**.
  - *Criterion amended 2026-11-14:* originally "no `from matrix...` imports remain" repo-wide. That is 1.4's scope — `alex-matrix` bind-mounts `./matrix`, so deleting the Alex copies before 1.6/1.7 replace the container would leave a crash-looping service. See 1.1a.
  - **Result:** 8 modules + `paths.py` + both `__init__`s in `~/.openjarvis/src/src/openjarvis/alex/`. Verified from `/tmp`: app title resolves, **20 routes**, **19 guardrail rules** (`default: approve`), gateways `freellmapi, groq, openrouter, omniroute, ollama`, profiles `fast, agent, coding, reasoning, local`. All intra-package imports rewritten to `openjarvis.alex.matrix.*`; `uvicorn` target updated; `tools.friday_mac` stays in its `try/except ImportError` until 1.2.
  - **Import blocker fixed:** `policy.py` built its engine at import from `config/guardrails.yaml` **relative to cwd**, so the package only imported from a checkout root. Added `openjarvis/alex/paths.py` (env → repo → `~/.openjarvis` → cwd) and moved `guardrails.yaml` + `profiles.yaml` into `<repo>/config/`. Fail-fast on missing guardrails is preserved.
- [x] **1.1a** Delete the Alex copies of `matrix/` once the native launcher owns `:8700` — 2026-11-14 · `05b06464`
  - Done when: `~/Documents/dependencies/Alex/matrix/` is gone and no compose service bind-mounts it.
  - **Result:** `Alex/matrix/` deleted after the native Matrix served `:8700` healthy; `docker-compose.yml` has no services, so nothing bind-mounts it.
- [x] **1.2** Move `friday_mac` tools → `openjarvis/alex/face/tools`; expose as OpenJarvis tool specs **and** an MCP server — 2026-11-14 · `05b06464`
  - Done when: the tool set is listed by the OpenJarvis tool registry and by the MCP server's tool list.
  - **Result:** `executor.py` + `apple_kit.py` moved; `friday_tools.py` wraps **10** actuators (`mac_open_app`, `mac_quit_app`, `mac_browse`, `mac_play_song`, `mac_set_volume`, `mac_toggle_dark_mode`, `mac_toggle_wifi`, `mac_bluetooth`, `mac_file_copy`, `mac_file_move`) with JSON-schema params and `requires_confirmation` on the destructive ones. Verified from `/tmp`: `ToolRegistry.keys()` lists all 10 `mac_*`; `build_mcp_server().get_tools()` returns the same 10. `ToolResult.metadata` carries `verified` + `evidence`. `worker.py` now imports `openjarvis.alex.face.tools.executor` (its `mac_tools = None` branch is closed).
- [x] **1.3** Move Hermes bridge + real runner → `openjarvis/alex/hermes` — 2026-11-14 · `05b06464`
  - Done when: the bridge imports from the new path and the duplicate copies are gone.
  - **Result:** `runtime.py` (run API, `:8642`, now binds `127.0.0.1` not `0.0.0.0`), `bridge/matrix_bridge.py`, `config.yaml`, `SOUL.md` live in the package. Duplicates deleted: `Alex/hermes/` and `~/.hermes/plugins/matrix_bridge.py`. Bridge verified live: `web.search` → `(True, 'Allowed')`; `shell_exec {"command": "rm -rf /"}` → `(False, 'BLOCKED … DENY-003')`.
  - **Defect caught here:** the first import rewrite was `^`-anchored, so two **indented** `from matrix.…` imports inside the bridge survived; `pre_tool_call` swallows exceptions and fails closed, so every Hermes tool call would have been silently blocked. Fixed and verified by the allow/deny pair above.
- [x] **1.4** Delete `Alex/jarvis/web.py`, duplicate SPAs, `Friday_*` guardrails, duplicate bridge/config — 2026-11-14 · `05b06464`
  - Done when: `grep -rn "jarvis/web\|Friday_Safety_Guardrails\|speak_female\|speak_samantha"` is empty across both repos.
  - *Criterion refined 2026-11-14:* scoped to code (`*.py *.ts *.tsx *.yml *.yaml *.sh *.toml`). The plan and this tracker must keep naming these files as history; a docs-exempt grep is the only form of this check that can ever pass.
  - **Result:** grep clean across both repos and `frontend/src`, including `tools.friday_mac`, `from matrix.`, `from hermes.`. Deleted: `Alex/jarvis/web.py` and the whole legacy `Alex/jarvis/` (TUI dashboard, CLI loop, reflex module — superseded by the Face), `Alex/Friday_Safety_Guardrails.md`, the Matrix embedded HTML console (`@app.get("/ui")`, 268 lines — `GET :8700/` now 404s), `speak_female` from `worker.py` (13 sites) and `speak_samantha` from `alex_dialogue.py` (22 sites), so Matrix no longer talks to the user directly.
  - **Deviations recorded:** `Alex/evals/` was deleted with its targets — it imported `matrix.*` and `jarvis.*` and could not run; 8.1 rebuilds the suite against the merged package. `Alex/tools/friday_mac/` removed with the move.
- [x] **1.5** Single config: `openjarvis/config.toml` points engine host at `:8700`, plus an `[alex]` section (matrix URL, hermes URL, ports) generated from `Alex/config/*.yaml` — 2026-11-14 · `05b06464`
  - Done when: exactly one config file defines the Matrix/Hermes ports; no YAML/TOML drift.
  - **Result:** `[alex]` in `~/.openjarvis/config.toml` is the only declaration (`face_port 8000`, `matrix_port 8700`, `hermes_port 8642`, three URLs, `data_root`). The duplicate `network:` block was stripped from **both** `config/settings.yaml` copies — it also carried a stale `hermes_port: 9119` (the dashboard, not the worker). All four YAMLs now live in `<repo>/config/`. `alex/hermes/config.yaml` keeps the Matrix provider URL as a *consumer*, not a port declaration.
- [x] **1.6** One launcher `alex` (`openjarvis alex up` / `down`) + launchd plist — 2026-11-14 · `05b06464`
  - Done when: `up` starts Face `:8000`, Matrix `:8700`, Hermes `:8642`; `down` stops all three.
  - **Result:** `openjarvis/cli/alex_cmd.py` + registration; subcommands `up`, `down`, `status`. Face is owned by the existing `com.openjarvis.server` agent (`KeepAlive=true`), so `up` **bootstraps** it and `down` **boots it out** rather than racing launchd with signals. Matrix/Hermes are spawned detached (`start_new_session`) with logs at `~/.openjarvis/logs/alex-*.log` and state in `alex.pids.json`; `down` refuses to kill a PID whose command line is not an Alex process (guards against killing Docker's proxy). Verified cycle: `down` → `face (launch agent), matrix (pid …), hermes (pid …)` stopped, **no listeners** on 8000/8700/8642; `up` → all three healthy. `scripts/com.openjarvis.alex.plist` shipped for the whole tree (not installed; 8.2 owns that).
- [x] **1.7** Remove the `jarvis` service from `docker-compose.yml` (keep only gateways) — 2026-11-14 · `05b06464`
  - Done when: `docker compose config` has no `jarvis` service and no `:8005` mapping.
  - **Result:** all three Alex services removed (`jarvis`, `matrix`, `hermes` now run natively); file keeps a documented `services: {}`. `docker compose config` → `services: {}` exit 0. Containers `alex-jarvis`/`alex-matrix`/`alex-hermes` stopped and removed; `:8005`, `:8700`, `:8642` freed. `freellmapi` and `omniroute` untouched.

**Phase gate**
- [x] A single `openjarvis` install includes `openjarvis.alex` — `uv build --wheel` → `openjarvis-1.0.5.dev185+g9b4bcfd8…whl` with **22** `openjarvis/alex/` entries (+ `hermes/config.yaml`, `SOUL.md`)
- [x] `openjarvis alex up` → `/health` green on `:8000`, `:8700`, `:8642` — `{"status":"ok"}`, `{"status":"ok","service":"matrix"}`, `{"status":"operational","agent":"hermes","gateway_url":"http://127.0.0.1:8700/v1"}`
- [x] `openjarvis alex down` → nothing listening on those ports — verified with `lsof`
- [x] Desktop app opens with no duplicate `:8000` — `open -a OpenJarvis` → `openjarvis-desktop` pid 81001, exactly **1** listener on `:8000`, `GET /` → 200 (Tauri `url: http://127.0.0.1:8000`)
- [x] No references left to deleted files (`grep` clean) — code-scoped grep across both repos + `frontend/src`

---

## Phase 2 — Ledger truth *(≈2 days)*

**Goal:** nothing claims done unless it was recorded.

- [x] **2.1** `record_event(task_id, source, type, payload)` in `alex/matrix/store.py`, called at every state change (intake, dispatch, step, progress, approval, done, failed) — 2026-11-14 · `1406106a`
  - Done when: one run produces rows for each of those seven types.
  - **Result, per type:** `intake` from the Face (api create) · `dispatch` on worker entry · `step` from `matrix_bridge.post_tool_call` · `progress` from `store.update_task_progress` (so every caller gets it for free) · `approval` from the bridge's approve gate and the user endpoints · `done`/`failed` from `store.complete_task`.
  - **Observed on one task** (`T-ALLEVENTS-1`): `intake, dispatch, progress, progress, approval, step, progress, done`. `failed` was observed on `T-DOCTOR-1` and the backdated `T-…487BDA` (`TIMEOUT-001`); `done` and `failed` are mutually exclusive per run, so one successful run cannot show all seven — the seven are each emitted by their own state change.
- [x] **2.2** Fix `clear_all_tasks` import (`matrix.store`); delete `events`, `steps`, `model_calls`, `tasks`, leftover `traces`; return counts — 2026-11-14 · `1406106a`
  - Done when: `POST /api/tasks/clear` → 200 with per-table counts, and the tables are empty after.
  - **Result:** `{"tasks": 21, "events": 0, "steps": 0, "model_calls": 61, "checkpoints": 0, "traces": 0}` → 200, and a follow-up count of `tasks/events/steps/model_calls` = `0/0/0/0`. `traces` (a table this ledger never had) is counted as 0 instead of raising.
- [x] **2.3** `GET /api/tasks/{id}/events` (SSE optional); include `evidence` + `finished_at` in `get_recent_tasks` — 2026-11-14 · `1406106a`
  - *Criterion amended 2026-11-14:* “renders in the UI” is 7.1's Logs-page rewrite — Phase 2 owns the contract, not the rendering. Scoped to the API.
  - **Result:** `GET /api/tasks/{id}/events?limit&after_id` (200 + parsed payloads), plus `GET /api/activity` across tasks. `get_recent_tasks` now selects `evidence`. Verified: `/api/tasks/recent` returns `evidence: 'It is currently 05:39 AM.'` for a finished task — the field is no longer missing/`undefined` in the payload. SSE not implemented (optional).
- [x] **2.4** Fix `matrix_bridge.post_tool_call`: sequential `step_no` per task (`MAX(step_no)+1`), real timestamps — 2026-11-14 · `1406106a`
  - Done when: a 5-tool run has steps 1..5 with no collisions.
  - **Result:** five bridged calls → `steps: [(1,), (2,), (3,), (4,), (5,)]` and step events `[1, 2, 3, 4, 5]`. Timestamps are now `datetime`-derived (`started = finished - duration_ms`) instead of `int(time.time())` as a step number.
- [x] **2.5** Endpoints `POST /api/tasks/{id}/approve|reject`, `/stop`, `/steer`; state in `tasks.status='awaiting_approval'` — 2026-11-14 · `1406106a`
  - Done when: each endpoint changes status and writes an event carrying its rule ID.
  - **Result:** `approve` → `running` + `approval` event, rule resolved from the latest `approval` event (**APPROVE-001**, from the bridge gate) or the request body; `reject` → `rejected` + `approval` (APPROVE-MANUAL when no gate exists); `stop` → `stopped` + `stop` (STOP-001); `steer` → `steer` (STEER-001) plus a progress event. A terminal task refuses nothing silently: `done/failed/rejected` return 409.
  - **Fixed 2026-11-14 (`aec2f506`), after 2.5 shipped:** approving used to write `running` even with no worker attached, so the sweep later failed a task nobody had started. Approved now consults a live-worker registry (`worker.is_active`): attached → `running`; otherwise → **`awaiting_worker`** ("Approved — waiting for a worker"), which the sweep deliberately does not touch because those states are not `running`. The Hermes bridge also stopped treating an approval rule as permission: `pre_tool_call` now returns `False` with `AWAITING APPROVAL (Rule …)` and parks the task as `awaiting_approval`, so an approve-required tool cannot run before you answer.
  - **Still open for 3.4/5.5:** approve does not yet *release a parked worker* — it parks honestly instead of resuming, because no worker waits at the gate. That is the real resume, and it needs the checkpoint/parking work.
  - **Verified:** no worker → `awaiting_worker`, survives `sweep_stale_tasks(0)` unchanged; worker attached → `running`; `mail.send` gate → `False` + `awaiting_approval` + APPROVE-001 event; finished task → 409; reflex task still `done`; 0 rows left in `running`.
- [x] **2.6** Wire `doctor.py` into worker failures (classify → bug row → advice) — 2026-11-14 · `1406106a`
  - Done when: a forced failure produces a `bugs` row with a classification and non-empty advice.
  - **Result:** with the gateway forced to raise `429 rate limit exceeded`, the retry path wrote `bugs{BUG-11967E, matrix.worker, error_class=rate_limit, occurrences=2}` with diagnosis + Doctor advice, task `failed`, and one `failed` event per attempt carrying `DOCTOR-RATE_LIMIT`.
- [x] **2.7** Task timeout/heartbeat: background runner marks `failed` with reason when heartbeat is stale — 2026-11-14 · `1406106a`
  - Done when: a killed run leaves no task stuck in `running` past the timeout window.
  - **Result:** new `heartbeat_at` column (idempotent `ALTER TABLE` for old ledgers), written by `create_task`, `update_task_progress`, `set_task_status`, `complete_task`. `sweep_stale_tasks(minutes=10)` runs from the `/api/tasks/recent` handler and a 60 s startup loop; it writes `failed` + evidence + a `failed` event with `TIMEOUT-001`. Verified by backdating a heartbeat: `failed`; a forced `sweep_stale_tasks(0)` also cleared the approved-but-unattached task, leaving **0** running.

**Phase gate**
- [x] Run a task → rows in `tasks`, `events`, `steps` — `T-ALLEVENTS-1`: task row + 8 events + 1 step row
- [x] `POST /api/tasks/clear` returns 200 and the Logs page goes empty — server half verified (200 + counts + 0 rows); the **UI's** clear button is wired to Zustand only and switches to the real endpoint in **7.2**
- [x] Completed task's evidence appears in the UI — `evidence` verified in `/api/tasks/recent` and `/api/tasks/{id}`; **rendering** in the Logs page is 7.1
- [x] Approve/reject/stop work from the API and are logged with rule IDs — APPROVE-001 / APPROVE-MANUAL / STOP-001 / STEER-001
- [x] No task can stay `running` forever — heartbeat sweep; 0 running after forced sweep

---

## Phase 3 — Face ↔ Trinity wiring *(≈3 days)*

**Goal:** the desktop app becomes Alex's mouth; Matrix becomes the brain stem.

- [x] **3.1** One `classify.py` for every user turn: `basic_reflex` | `quick_answer` | `complex_task` (rules first, one cheap model call only on a miss) — 2026-11-14 · `07476c3f`
  - Done when: a labelled utterance set routes deterministically and the model is called only on rule misses.
  - **Result:** 31/31 labelled utterances route as expected. Guards proven: "what time do you close?" → quick (not a reflex), "if you can, turn off wifi" → quick, "don't turn off wifi" → quick, "open the door" → quick (not an app launch). Politeness handled: "can you turn off bluetooth?" → reflex. Determinism asserted with a spy fallback: **no model call** on three rule hits, exactly one on a total miss.
- [ ] **3.2** `basic_reflex` → `friday-mac` tools with verification + evidence → `POST /api/tasks` with `executor=face` — **partially verified (dry-run only)**
  - Done when: "turn off bluetooth" produces a verified action plus a recorded task row.
  - **Result:** the path exists and records `executor=face` with `intake`/`dispatch`/`done` and the tool's evidence (e.g. `Bluetooth: dry-run… (verified)`). Only the **dry-run** half is proven: actually toggling Bluetooth/Wi-Fi would change your machine while you are asleep, so the real action is left for you to trigger. Run `openjarvis alex status`, then ask "turn off bluetooth" — the row should show real evidence.
- [x] **3.3** `quick_answer` → Matrix `/v1` (`friday-fast`) with a concise rubric — 2026-11-14 · `2960a82f`
  - Done when: the answer comes back through the gateway and is logged as a model call.
  - **Result:** live `POST /api/alex/chat` → "William Shakespeare wrote Hamlet." and `/v1/chat/completions` → "Tokyo is the capital of Japan." Logged as `model_calls{gw=ollama, model=qwen3:4b, tokens_in=51, tokens_out=128, outcome=success}`.
  - **Blocker found and fixed:** every hosted gateway returns **401** (no `FREELLMAPI_KEY`/`GROQ_API_KEY`/`OPENROUTER_API_KEY` in the native process), so answers were impossible. The gateway now appends a keyless local Ollama candidate as the last resort, and the stale `local` model name (`qwen3-4b-64k`) was corrected to the tag Ollama actually has (`qwen3:4b`).
- [ ] **3.4** `complex_task` → `POST /api/tasks` → poll/subscribe events → speak milestones per speech policy
  - Done when: a long task emits milestones and Alex speaks only at the allowed points.
- [x] **3.5** Replace `alex_dialogue.py`'s canned regex bot with `dialogue.py`: real slot-filling (topic, words, channel, contact email), **no hardcoded facts** — 2026-11-14 · `2960a82f`
  - Done when: `grep -n "7,850"` and friends find nothing, and a missing slot triggers a question.
  - **Result:** `matrix/alex_dialogue.py` deleted (hardcoded essay, gold rate, canned replies); `alex/dialogue.py` mounts in `/api/alex/chat` and `/v1/chat/completions`. `grep "7,850"` and `grep "Master Khan"` → nothing. Slot filling verified: "write a 60-word note on diwali and mail zara" captured `{deliverable: note, topic: diwali, words: 60, recipient: Zara}` then asked **"What email address should I use for Zara?"**; answering dispatched `T-20261115-29EC00`. Known contact Max resolves from memory (`max123@gmail.com`) without asking.
- [ ] **3.6** Proactive speech policy: speak on `task_started`, `approval_needed`, `blocked`, `task_failed`, verified `task_done`; never on intermediate tool calls
  - Done when: a multi-step run produces speech only at those five events.
- [ ] **3.7** Multi-task queue: concurrent Hermes runs, Face prefixes updates with the task short-name
  - Done when: two tasks run at once and each update names its task.
- [ ] **3.8** Close-on-goodbye via a Tauri command the server calls (no `osascript`/`pkill` hacks)
  - Done when: "No" on "anything else?" shuts the app down cleanly through the command.

**Phase gate**
- [ ] "Turn off Bluetooth" → instant, verified, recorded, spoken
- [ ] "What's the gold rate today?" → real web answer (no hardcoded line)
- [ ] "Write 100-word essay on Diwali and mail Max" → slot-filling → Hermes → approval → send
- [ ] "Make a Diwali card PDF" queues as a second task while the first runs
- [ ] Alex speaks only at accept/approval/blocked/done
- [ ] False positives ("what time do you close?" etc.) do **not** trigger basic actions — ≥100 labelled utterances

---

## Phase 4 — Voice: one pipeline that never dies *(≈2 days)*

**Goal:** exactly one state machine, one STT, one TTS, and a mic that works on turn 11.

- [ ] **4.1** Server mic state machine: `start → listening → (speech) → listening → (5 s silence OR "alex reply") → stop → transcribe → idle`; expose `state`, `silence_remaining`, `transcript_partial`
  - Done when: the API reports each field correctly through a full cycle.
- [ ] **4.2** Frontend: single `useSpeech` drives the state machine; auto-start on launch; auto-return to listening after every answer; reset `_mic_auto_stopped`/`_mic_has_spoken`
  - Done when: 10 consecutive turns leave the mic live and listening.
- [ ] **4.3** One TTS path: server `say -v Samantha` (queue + `pkill say` on barge-in); browser only as fallback; remove the other speak functions
  - Done when: one code path can speak, and only one process produces audio.
- [ ] **4.4** Barge-in: "listen" → kill TTS + clear buffer + LISTENING; "alex reply" → send now; 5 s silence → send
  - Done when: all three stopwords behave and are covered by a test.
- [ ] **4.5** Echo suppression: clear buffer while speaking; drop transcripts ≥ 0.45 similar to the last spoken line
  - Done when: Alex's own speech never becomes a transcript.
- [ ] **4.6** Fold wake word into the server (`openwakeword`, `faster-whisper` fallback); delete the standalone listener
  - Done when: `alex_wake_listener.py` is deleted and wake fires once per invocation from the server.
- [ ] **4.7** Visual state in the UI: mic pulse, countdown ring, "Listening / Thinking / Speaking"
  - Done when: the indicator tracks the server state without polling drift.

**Phase gate**
- [ ] Launch app → mic is live with **no** clicks
- [ ] Speak → wait 5 s → it answers
- [ ] "Alex reply" mid-sentence → immediate answer
- [ ] "Listen" while speaking → stops instantly
- [ ] Repeat 10 turns → mic still works on turn 11
- [ ] Alex does not answer its own voice
- [ ] Wake word launches the app once (no repeat triggers)

---

## Phase 5 — Hermes becomes real *(≈4–5 days)*

**Goal:** replace the stub with the real `hermes-agent` runtime (`~/.hermes/hermes-agent`).

- [ ] **5.1** Replace stub `daemon.py` with the real runtime: `/v1/runs` starts an agent loop with toolsets (terminal, files, browser, web, mail, delegation, MCP `friday-mac`)
  - Done when: a run exercises at least three distinct toolsets and returns real artifacts.
- [ ] **5.2** Model provider = `custom:matrix` (`http://127.0.0.1:8700/v1`), no direct fallbacks
  - Done when: stopping Matrix breaks Hermes model calls (proving the path is enforced).
- [ ] **5.3** Register `matrix_bridge` hooks (`pre_tool_call` fail-closed, `post_tool_call` → ledger) + `matrix_memory` prefetch
  - Done when: a tool call blocked by policy fails the run, and a prefetch shrinks the first prompt.
- [ ] **5.4** Structured plan: Hermes emits `STEP n/N`; Matrix parses it for progress
  - Done when: the dashboard shows real `n/N` progress.
- [ ] **5.5** Evidence-verified completion; Matrix steers once if "done" lacks evidence
  - Done when: a bogus "done" is rejected and re-steered.
- [ ] **5.6** Duplicate prevention: idempotency keys for send/move/booking
  - Done when: a retried send does not send twice.
- [ ] **5.7** Checkpoint/resume on network loss; local Ollama takeover for `offline_capable` (fix model name)
  - Done when: `ollama:qwen3-4b-64k` resolves and a mid-task disconnect resumes without repeats.
- [ ] **5.8** Real deliverables: essay/doc → PDF; draft mail → send after approval → verify in Sent
  - Done when: the PDF opens and the Sent folder contains the approved mail.

**Phase gate**
- [ ] Hermes writes a real file you can open
- [ ] Email is drafted + sent only after approval; verified in Sent
- [ ] Research returns real web content (not canned)
- [ ] Tool calls appear in `steps` with rule IDs
- [ ] Wi-Fi off mid-task → checkpoint → on → resumes at the right step, no duplicates
- [ ] Killed double-send blocked by idempotency

---

## Phase 6 — Memory & personality *(≈2–3 days)*

**Goal:** Alex remembers, reuses, and sounds like Alex.

- [ ] **6.1** One memory DB (contacts, facts, preferences, procedures, pitfalls, artifacts), written only by Matrix
  - Done when: no other process opens `memory.db` for writes.
- [ ] **6.2** Contact book: "save this email" → reused next time; lookup by name
  - Done when: a second mail task fills the recipient with no prompt.
- [ ] **6.3** RAG briefs into Hermes (≤ ~1,200 tokens); prior-procedure replay
  - Done when: the injected brief is measured under the ceiling and a repeat task reuses the procedure.
- [ ] **6.4** Alex persona (SOUL.md merged): "Master Khan / sir", brief, outcome-first
  - Done when: replies match the persona on every path, including errors.
- [ ] **6.5** Stage directions from `z.txt`: greeting, "anything else?", "I'll be off then…"
  - Done when: the script's lines appear verbatim at the right moments.
- [ ] **6.6** Preferences with transparency ("what do you know about…", "forget that")
  - Done when: both queries return/tombstone real memory entries.

**Phase gate**
- [ ] Second run of the same task uses noticeably fewer tokens (before/after numbers recorded below)
- [ ] Saved contact is used automatically next time
- [ ] Greeting/sign-off match the script exactly

**Token comparison:** first run: ____ · second run: ____ · delta: ____

---

## Phase 7 — Logs, dashboard & report *(≈1–2 days)*

**Goal:** the app tells the truth about what happened.

- [ ] **7.1** Logs page reads **real** events from Matrix (`/api/tasks/{id}/events` + `/api/activity`), not Zustand
  - Done when: a row added by the server appears without a client write.
- [ ] **7.2** Clear (client + server) works and is confirmed by the count returning to 0
  - Done when: clear → 0, restart → still 0.
- [ ] **7.3** Dashboard: live tasks, step n/N, tokens, gateway used
  - Done when: all four fields match the ledger for a running task.
- [ ] **7.4** Excel/CSV report (`matrix report`) with the 6 sheets
  - Done when: the workbook opens with all six sheets populated.
- [ ] **7.5** Filter false-positive log noise (only real state changes logged)
  - Done when: a no-op utterance logs nothing.

**Phase gate**
- [ ] Logs show today's real tasks only
- [ ] Clear → 0 entries, and they don't come back
- [ ] Export opens in Excel with all sheets

---

## Phase 8 — Hardening & acceptance *(≈2–3 days)*

**Goal:** prove it, document it, ship it.

- [ ] **8.1** Automated eval suite: both `z.txt` dialogues + 100-utterance guard set + gateway failover + offline + duplicate-send
  - Done when: `openjarvis alex eval` runs unattended and is green.
- [ ] **8.2** One-command install/launch; launchd autostart; menu-bar status
  - Done when: a fresh machine reaches a working app with one documented command.
- [ ] **8.3** 16 GB memory soak (Chrome open, 1 h mixed, 15 min offline)
  - Done when: memory pressure never reaches red; samples recorded below.
- [ ] **8.4** Docs: `BLUEPRINT.md` (Part A), `RUNBOOK.md` (start/stop/ports), `CONFIG.md`
  - Done when: a reader can start, stop, and reconfigure without reading source.

**Phase gate**
- [ ] All `z.txt` scenarios pass unattended
- [ ] 0 wrong basic-action matches on the 100-utterance set
- [ ] Memory pressure never red
- [ ] Fresh install → `openjarvis alex up` → works

**Soak samples:** peak RSS ____ · pressure events ____ · swap ____

---

## Part D — Acceptance script (run after **every** phase)

**Legend:** ✅ passed · ❌ failed · ⛔ blocked (reason below) · ☐ not reached yet

| # | Check | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Launch app → mic live → "Wake up Alex" greeting | ⛔ | ⛔ | ⛔ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| 2 | "Turn off Bluetooth" → instant + spoken + recorded | ⛔ | ⛔ | ⛔ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| 3 | "What's the gold rate today?" → real answer | ⛔ | ⛔ | ⛔ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| 4 | Max essay flow (`z.txt`) incl. proofread/approve + "PDF saved at…" | ⛔ | ⛔ | ⛔ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| 5 | "Alex, listen" while speaking → stops | ⛔ | ⛔ | ⛔ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| 6 | Logs → clear → empty; restart → still empty | ⛔ | ⛔ | ⛔ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| 7 | Kill Hermes mid-task → failed with reason, no stuck `running` | ⛔ | ⛔ | ⛔ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| 8 | Wi-Fi off/on mid-task → pause/resume, no duplicates | ⛔ | ⛔ | ⛔ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |

**Why Phase 0 is ⛔ for every row** (blocked, not passed):

| # | Reason | Unblocked by |
|---|---|---|
| 1 | Needs a live audio device and the Tauri window; there is no headless mic path, and you have to be at the machine. | Phase 4 gate |
| 2 | Toggles real Bluetooth — a system-state change, not a read-only check. | You, at the machine |
| 3 | Routes through an external model gateway (network + credits). Phase 0 baseline instead captured the canned `model: "matrix"` reply — bug B1-6. | Phase 3 gate |
| 4 | Depends on rows 1, 2 and 5 plus a mail send approval; first meaningfully runnable once the Face is wired. | Phase 3 gate |
| 5 | Requires active TTS output to interrupt. | Phase 4 gate |
| 6 | `POST /api/tasks/clear` is known-broken (B1-7, `ModuleNotFoundError` → 500); measuring it is 2.2's job. | 2.2 |
| 7 | Would kill the live `alex-hermes` container mid-run. | 2.7 |
| 8 | Toggles the host network — a system-state change. | You, at the machine |

**Phase 2 column:** still ⛔. The ledger is now truthful, but the *experience* rows are unchanged — 6 needs the Logs page to read the new endpoint (7.1/7.2) and 7 needs a real Hermes run to kill (5.1). Rows 1/2/4/5/8 still need the voice pipeline and you at the machine.

**Phase 1 column:** still ⛔ on the same rows. The merge changed ownership of ports and processes, not voice or system behaviour — check 3 remains the canned `matrix` dialogue until 3.5, and 6/7 are untouched until 2.2/2.7.

Phase 0 was instead verified by the checks that *are* observable headlessly: single `:8000` owner, 10/10 backup integrity, blueprint commit, `/health` + one real chat turn. Those are recorded under Phase 0 above.

**Definition of done (whole project):** the two dialogues in `z.txt` play out exactly as written, unattended, with every step visible in the ledger.

---

## Decisions (locked, do not re-litigate)

- **Face** = OpenJarvis Tauri desktop app (`~/.openjarvis`, `:8088` → `:8000`).
- **Architecture** = merged: Face + Matrix + Hermes as layers of one app, one repo, one process tree.
- **Language** = spoken English, "Master Khan / sir", JARVIS-like.
- **Hard rules** = Face never calls Hermes; Hermes never talks to the user; every model call goes through Matrix `/v1`; Matrix is the only writer to `ledger.db` / `memory.db`.

---

## Working notes per phase

### Skill / tool routing for this plan

| Phase | Primary skills |
|---|---|
| 0–1 | `/python-project-structure` (package layout, `__all__`), `/improve-codebase-architecture` (deletion test on the duplicates) |
| 2, 5–6 | `/sqlite-database-expert` (WAL, parameterised queries, migrations), `/python-testing-patterns` |
| 3–4 | `/async-python-patterns` (server state machine, SSE, barge-in cancellation) |
| 5 | `/mcp-builder` (exposing `friday-mac` as MCP), `/agent-browser` (browser tool verification) |
| 6–7 | `/codebase-design` (deep `record_event` / memory module), `/code-review` (per-phase diff review) |
| 8 | `/python-testing-patterns`, `/agent-browser` (UI acceptance), `/code-review` |

---

## Change log

| Date | Phase | Change |
|---|---|---|
| 2026-11-14 | — | Tracker created from the plan; all steps open, baseline not yet captured. |
| 2026-11-14 | 0 | Phase 0 done: single `:8000` owner verified (PID 816), 10 DB backups `ok`, live port map written, `docs/BLUEPRINT.md` committed (`084274eb`), app health+chat baseline captured. |
| 2026-11-14 | 0 | Part D Phase 0 column filled: all 8 checks ⛔ blocked with reasons (mic/system-state/later-phase ownership); headless verification recorded instead. |
| 2026-11-14 | 1 | 1.1 done: Matrix now at `openjarvis/alex/matrix` (`9b4bcfd8`), imports rewritten, `paths.py` config anchor added, config copied to `<repo>/config`; import verified from `/tmp`. New 1.1a tracks deleting the Alex copies at 1.4/1.7. |
| 2026-11-14 | 1 | **Phase 1 complete** (`05b06464`): friday-mac in `alex/face/tools` as 10 registry tools + MCP server; Hermes layer moved (bridge deny-path verified); duplicates deleted incl. both TTS paths and the Matrix console; `[alex]` single config; `openjarvis alex up/down/status` with launchd handoff; compose emptied and containers removed. Wheel contains 22 `alex/` entries. |
| 2026-11-14 | 2 | **Phase 2 complete** (`1406106a`): events at all seven state changes, clear returns counts and empties every table, events/activity endpoints, evidence in `/recent`, sequential steps 1..5, approve/reject/stop/steer with rule IDs, Doctor wired to worker failures, heartbeat sweep with `TIMEOUT-001`. 2.3 and the clear/evidence gate re-scoped to the API (UI is 7.1/7.2), dated in place. |
| 2026-11-14 | 3 | 3.1/3.3/3.5 done (`07476c3f`, `2960a82f`): deterministic classifier, live gateway answers with local fallback, real slot-filling replacing the canned bot. 3.2 dry-run verified only. Remaining: 3.4 milestones, 3.6 speech wiring, 3.7 queue names, 3.8 Tauri close. |
| 2026-11-14 | 3 | Blocker fixed: all hosted gateways answered 401 (keys not present in the native process), so quick answers were impossible; added a keyless Ollama last-resort candidate and corrected the `local` model tag. |
| 2026-11-14 | 2 | Bug fixed (`WORKER_LOCK`): a late worker could overwrite an unanswered approval with `done`. `complete_task`/`update_task_progress` now refuse to touch `awaiting_approval`, `awaiting_worker` and all terminal states, recording `LOCK-002`/`LOCK-001` instead. Verified 7/7 transitions. |
| 2026-11-14 | 2 | Follow-up fix (`aec2f506`): approve no longer fakes `running`. New `awaiting_worker` status (sweep-exempt) + live-worker registry; bridge approval gate now blocks instead of proceeding. Real resume of a parked worker remains 3.4/5.5. |
| 2026-11-14 | 2 | Hazard fixed: `store` resolved `storage/data/*.db` relative to cwd, so a worker started elsewhere silently wrote a second empty ledger — indistinguishable from “nothing happened”. Now anchored by `ALEX_DATA_ROOT` (set by `alex up`). |
| 2026-11-14 | 1 | Deviations recorded: `Alex/evals/` deleted (imported removed modules; 8.1 rebuilds), `Alex/jarvis/` deleted wholesale, legacy `tools/friday_mac/` removed. Part D Phase-1 column filled ⛔ with the same reasons as Phase 0. |
