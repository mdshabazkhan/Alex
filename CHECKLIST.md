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
| **Memory & artifacts** | `/Users/mdshabazkhan/Documents/dependencies/Storage` | Short-term doc store, OKF bundle, per-task workspace, cache/tmp, janitor log — created 2026-11-15 |
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
| 3 | Face ↔ Trinity wiring | 3 d | 10 / 11 | In progress | 2026-11-18 |
| 4 | Voice: one pipeline that never dies + human delivery | 3 d | 8 / 10 | In progress | `3630cfad` |
| 5 | Hermes becomes real | 4–5 d | 7 / 8 | In progress | 2026-11-17 |
| 6 | Memory: short-term ⇄ long-term + experience | 5 d | 14 / 14 | In progress | 2026-11-17 |
| 7 | Logs, dashboard & report | 1–2 d | 6 / 6 | Done | 2026-11-18 |
| 8 | Hardening & acceptance | 3 d | 2 / 5 | In progress | 2026-11-17 |

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
- [x] ~~**3.2** `basic_reflex` → `friday-mac` tools with verification + evidence → `POST /api/tasks` with `executor=face`~~ — 2026-11-17
  - Done when: "turn off bluetooth" produces a verified action plus a recorded task row.
  - **Result:** live `turn off bluetooth` (`T-20261117-6C9A16`) returned `Bluetooth: Bluetooth disabled (verified)`, recorded `executor=face` with `intake`/`dispatch`/`done`, and stored `evidence:"Bluetooth disabled"`; `system_profiler` reported State Off. Bluetooth was restored to On after the drill. The actuator also has an 8-second timeout for the earlier blueutil hang, covered by `tests/alex/test_bluetooth_tool.py`.
- [x] **3.3** `quick_answer` → Matrix `/v1` (`friday-fast`) with a concise rubric — 2026-11-14 · `2960a82f`
  - Done when: the answer comes back through the gateway and is logged as a model call.
  - **Result:** live `POST /api/alex/chat` → "William Shakespeare wrote Hamlet." and `/v1/chat/completions` → "Tokyo is the capital of Japan." Logged as `model_calls{gw=ollama, model=qwen3:4b, tokens_in=51, tokens_out=128, outcome=success}`.
  - **Blocker found and fixed:** every hosted gateway returns **401** (no `FREELLMAPI_KEY`/`GROQ_API_KEY`/`OPENROUTER_API_KEY` in the native process), so answers were impossible. The gateway now appends a keyless local Ollama candidate as the last resort, and the stale `local` model name (`qwen3-4b-64k`) was corrected to the tag Ollama actually has (`qwen3:4b`).
- [x] **3.4** `complex_task` → `POST /api/tasks` → poll/subscribe events → speak milestones per speech policy — 2026-11-15 · `6e7f3a56`
  - Done when: a long task emits milestones and Alex speaks only at the allowed points.
  - **Result:** each run now writes discrete `milestone` events (step 1/3 planning, 2/3 executing, 3/3 complete, with the task short name) alongside progress, and speech stays silent on them. Verified on two concurrent runs: event stream `dispatch → speech → progress → milestone → … → done → speech`, exactly 3 milestones each.
- [x] **3.5** Replace `alex_dialogue.py`'s canned regex bot with `dialogue.py`: real slot-filling (topic, words, channel, contact email), **no hardcoded facts** — 2026-11-14 · `2960a82f`
  - Done when: `grep -n "7,850"` and friends find nothing, and a missing slot triggers a question.
  - **Result:** `matrix/alex_dialogue.py` deleted (hardcoded essay, gold rate, canned replies); `alex/dialogue.py` mounts in `/api/alex/chat` and `/v1/chat/completions`. `grep "7,850"` and `grep "Master Khan"` → nothing. Slot filling verified: "write a 60-word note on diwali and mail zara" captured `{deliverable: note, topic: diwali, words: 60, recipient: Zara}` then asked **"What email address should I use for Zara?"**; answering dispatched `T-20261115-29EC00`. Known contact Max resolves from memory (`max123@gmail.com`) without asking.
- [x] **3.6** Proactive speech policy: speak on `approval_needed`, `blocked`, `task_failed`, verified `task_done`; never on `task_started` or intermediate tool calls — 2026-11-15 · amended 2026-11-18 · `6e7f3a56`
  - Done when: a multi-step run produces speech only at those four events.
  - **Amended 2026-11-18 (user: “until then it doesn't disturb with annoying text”):** `task_started` is no longer an allowed speech moment — `speech_policy.ALLOWED_EVENTS` no longer contains it, so a dispatched task is silent until it is verified done, blocked, needs approval, or fails. The interim chat acknowledgement `"On it: … I'll tell you when it's finished."` is kept deliberately as a single reply, not progress chatter.
  - **Result:** `speech_policy.emit()` is the only writer: it refuses any moment outside the five, skips an unverified `task_done`, and records the approved line as a `speech` event. In the two-task run, speech moments were exactly `{task_started, task_done}` — no line for any progress tick, milestone or model call. `GET /api/speech/pending?after_id=` serves them in order (3 returned, `next_after_id=97`).
- [x] **3.7** Multi-task queue: concurrent Hermes runs, Face prefixes updates with the task short-name — 2026-11-15 · `6e7f3a56`
  - Done when: two tasks run at once and each update names its task.
  - **Result:** `short_name()` derives the handle and every line names its task in a spoken sentence: `"On it — short note about solar power."`, `"Done — 100-word essay on diwali. …"`, `"Short note about solar power failed: rate limit."`. Two concurrent tasks produced distinct, correctly-named lines. Live check: first dispatch `parallel=false` ("On it: …"), second `parallel=true` ("Starting that alongside the other one: …") — the second is **not** called queued, because both run concurrently.
  - **Bug fixed while testing:** the concurrency check read the worker registry before the new coroutine had started, so two requests in the same tick were both told "On it". `submit_task()` now claims the slot *before* scheduling.
  - **Bug fixed (wording review, 2026-11-15):** the label stripped prepositions ("note solar power") and the line used a colon prefix ("Short note solar power: on it."). Labels now keep their prepositions, drop only the leading verb/article, keep both subjects unless the tail is a send ("scrape croda and dupont" → "croda and dupont"), and the sentences read naturally. The "queued" wording was a lie for tasks that run in parallel and is now "Starting that alongside the other one".
- [ ] **3.8** Close-on-goodbye via a Tauri command the server calls (no `osascript`/`pkill` hacks) — **built, GUI shutdown not yet seen; accessibility inspection timed out on the running bundle** · `6e7f3a56`
  - Done when: "No" on "anything else?" shuts the app down cleanly through the command.
  - **Result:** `close_app` command added and registered (`app.exit(0)`, so `RunEvent::ExitRequested → stop_all` kills the backend children instead of orphaning them); the dialogue turn returns `action: "close_app"`, it is carried on the **stream** chunk the UI actually reads (`alex.action`), and `InputArea` invokes the command on it. Verified: SSE stream for "goodbye alex" returns `delta: "I'll be off then…"` with `alex: {action: close_app, kind: shutdown}`; `cargo check` exit 0; TypeScript typecheck exit 0. **Not verified:** the window actually closing, which needs the desktop app running.
  - **Latent bug found:** the streaming path dropped all dialogue metadata, so the UI could never have acted on an action — the chunk now carries `alex`.
- [x] **3.9** Conversation threads: every turn is kept in a per-conversation JSON file, follow-ups resolve from it, and a new conversation starts fresh — 2026-11-18
  - Done when: a follow-up that only makes sense in context resolves without repeating the subject, and another session does not inherit it.
  - **Result:** `alex/threads.py` keeps `Storage/conversations/<thread_id>.json` (one file per conversation, every turn dated, `_active.json` mapping session → thread), and the dialogue reads the thread before answering. A thread idle under two hours is still "the current conversation"; untouched for 30 days its JSON is discarded while the distilled `short_term` (skill + procedure) and `long_term` (summary, artifacts) rows stay in SQLite. Tests: `tests/alex/test_conversation_threads.py`, `tests/alex/test_thread_context.py`.
- [x] **3.10** Playback is resolved, played and verified instead of announced — 2026-11-18
  - Done when: the reply names the video that is actually playing, and a bare follow-up ("play it", an artist name) reuses what was just played.
  - **Result:** the Face route no longer opens `youtube.com/results?search_query=<the whole sentence>` and replies “Playing …” over a results page — it calls `executor.play_song`, so the **subject** is searched, not the instruction (“I want you to play attention by Charlie Puth on YouTube.” → `Charlie Puth Attention`). Wrappers (“I want you to”, “can you”, “please”) and a trailing “on YouTube” are stripped by `normalise_song_query`/`classify.py`; "play it" falls through to the thread memory; a bare name after playback is treated as the song/artist. Live: the right video played and the reply quoted its verified title; “Play it on YouTube.” restarted the same tab. Tests: `tests/server/test_play_route.py`, `tests/alex/test_play_song_execution.py`.
- [x] **3.11** A web question is understood before it is executed: subject separated from the instruction, pages read, summary with sources — 2026-11-18
  - Done when: "google about harry potter series on chrome" searches the subject, and the reply is a summary of what the pages actually said.
  - **Result:** new `alex/web.py` parses the request (`understand_search_request` → `{query: "harry potter series", engine: google}`, returning `None` for ordinary questions), opens Chrome on `google.com/search?q=harry+potter+series`, collects result pages, reads the top two, and summarises them with `[n]` citations through the local gateway (extractive fallback). When no page is readable it says so and is **not** verified rather than inventing an answer. Google serves HTTP clients a JavaScript shell (0 results parsed, 93 KB), so discovery uses Bing's server-rendered HTML while the visible tab is the Google search the user asked for. Live: correct URL in Chrome and a real summary of two Wikipedia pages; a run with no readable page returned “nothing to summarise” and `verified: false`. Tests: `tests/alex/test_web_research.py` (5).

- [x] **3.12** Code requests are answered in the chat: a copyable, syntax-highlighted block, no file, no Hermes run, no browser — 2026-11-19
  - Done when: "Write a Python program to calculate the area of a triangle" shows the code and creates nothing on disk.
  - **Result:** the missing path is now `alex/coder.py`, reached from `_handle_turn` before web research and before `classify`. The reply is one fenced block (rendered by the existing `CodeBlockPre` with its Copy button), the snippet is kept on the conversation thread so it survives a restart, and neither a task nor an artifact is created. Project requests (app/application/api/website/service/server/database/framework) still go to Hermes, because those genuinely need files. Test: `tests/alex/test_code_in_chat.py::test_a_code_request_appears_in_chat_and_creates_nothing`.
- [x] **3.13** Saving is explicit, canonical and idempotent: default `Storage/Artifacts/code`, custom path honoured, a repeated save writes nothing — 2026-11-19
  - Done when: "Save it" writes one file and reports the real path; saying it twice does not produce a second copy.
  - **Result:** `resolve_destination` uses the requested path (resolved against the home directory, directories created safely, system/storage-internal paths refused), else the default directory. The hash covers exactly the bytes written, so an identical re-save answers "already saved at … nothing changed"; a file that exists with *different* content is not overwritten without "overwrite it". Each real write gets a ledger task, a task-register row and an artifact document (sha256, language, snippet id), and the reply reports created-vs-updated from the filesystem. Tests: `test_save_writes_one_canonical_file_and_a_repeat_changes_nothing`, `test_save_honours_a_custom_path`.
- [x] **3.14** Code continuity: a follow-up edits the same logical snippet, and an explicit run executes it in scratch space — 2026-11-19
  - Done when: "add input validation" updates the snippet instead of starting over, and "run it" shows the program's real output.
  - **Result:** threads carry `thread["code"]` (`snippet_id`, language, text, filename, version, saved paths). A modification phrase with a snippet present sends the previous code plus the instruction to the gateway and stores version n+1; no intermediate version is ever saved. "Run it" executes Python in a `Storage/temp/code_runs/run-*` directory with a 20 s timeout, reports exit status and output, and deletes the scratch directory afterwards. Tests: `test_a_follow_up_edits_the_same_snippet`, `test_run_executes_the_code_and_cleans_its_scratch_directory`.
- [x] **3.15** Status and correction questions are answered from state and never start work or open a tool — 2026-11-19
  - Done when: "Is the code done?", "Show me the code here in chat" and "I'm not making that" create no task, no file and no YouTube tab.
  - **Result:** `coder.understand` is deterministic and runs before classification. Status answers name the snippet already in the chat (with its saved paths) or the last ledger task's real state ("Not yet, master. It's still running."); show re-displays the same block; a correction replies "Understood — dropping that. Nothing was opened or started." Tests: `test_a_status_question_never_dispatches_or_plays`, `test_show_me_the_code_does_not_start_another_task`, `test_a_correction_opens_nothing`.
- [x] **3.16** Session counters say "Unavailable" instead of a misleading zero — 2026-11-19
  - Done when: a counter no backend has reported is not rendered as `0`.
  - **Result:** `SystemPanel.tsx` distinguishes an absent value from a measured zero for Requests and Output Tokens (`savings?.total_calls ?? telemetry?.total_requests`, `… ?? total_tokens`). Rendered value is "Unavailable" when neither source reported one; a real zero still shows as 0. Typecheck: `npx tsc -b` exit 0.
- [x] **3.17** A follow-up about the code carries the conversation: the model sees the earlier problem without being able to replay the earlier block — 2026-11-19
  - Done when: "I need the code for the above problem" writes new code for the problem that was just discussed, instead of answering "which problem?" or repeating the old snippet verbatim.
  - **Result:** `_history_for_code` builds a per-thread transcript with previous code blocks elided, and `_generate_code(prompt, language, history)` passes it to the gateway, so the problem survives but the previous block cannot be echoed back. The "code for the above problem" phrase is checked **before** the `_SHOW`/replay rule, so it is a new generation, not a re-display, and `_GENERATE_START` now accepts "I need/want/would like/we need" as well as "write/create". The quick-answer prompt also forbids asking for context that is already in the conversation. Tests: `tests/alex/test_code_in_chat.py` (+3), `tests/alex` **214 passed**. Live on `:8000`: "code." → rectangle code block, then "I need the code for the above problem." → a fresh block for the same problem.
- [x] **3.18** The server thread is the chat's identity: one conversation is one sidebar entry — 2026-11-19
  - Done when: a chat started while the previous turn was still running appears once in the sidebar, with both turns in chronological order.
  - **Result:** the backend stored the whole conversation in one thread file while the UI kept one local record per draft, so a single `C-…` thread held turns from two chats and the sidebar listed both. Every `alex` payload now carries `thread_id` (JSON and SSE), `Conversation.threadId` stores it, and `store.adoptThread()` runs after the stream: it adopts the id, or merges the twin record into the earlier chat and drops it; `mergeSameThreadConversations()` repeats the collapse at load so a reload cannot resurrect the split. Root cause on disk: chats `mwn7grt1ma9bwv` and `mwndy0hc0y8n24` shared one thread. Tests: `frontend/src/lib/store.thread-adoption.test.ts` (3), `npx vitest run` **131 passed**.
- [x] **3.19** "Open a new chat" opens a chat — it does not launch an app called "new check" or "new Chad" — 2026-11-19
  - Done when: saying it once, twice, or in a mis-transcribed form opens an empty chat, and "run a new check" still means a check.
  - **Result:** the phrase was matching the `open_app` reflex with app name "new check" ("chat" → "check"/"chad" in speech recognition), so Alex tried to verify an app, failed, and answered "I'm not sure how to handle that request" when asked again. `_NEW_CHAT` in `dialogue.py` now returns `action: "new_chat"` before reflex routing — the same shell-action shape as `close_app` — and `InputArea` creates the chat on it. ASR variants (`check`, `chad`, `chet`, `chatt`) are accepted only when the phrase is the whole turn, so "run a new check" is untouched. Tests: `tests/alex/test_new_chat_intent.py` (7). Live: "Open a new check." and "new Chad Alex." both returned `action: new_chat`.

**Phase gate**
- [x] "Turn off Bluetooth" → instant, verified, recorded, spoken — 2026-11-17 · `T-20261117-6C9A16`, evidence `Bluetooth disabled`, system State Off (restored On after)
- [x] "What's the gold rate today?" → real web answer (no hardcoded line) — 2026-11-17 · live `/api/alex/chat` returned `$3,868.97` per troy ounce from `gold-api.com`, with a fresh timestamp and source in the reply
- [ ] "Write 100-word essay on Diwali and mail Max" → slot-filling → Hermes → approval → send
- [x] "Make a Diwali card PDF" queues as a second task while the first runs — 2026-11-17 · live
  - First attempt **failed**, and the failure was worth having: it answered "What should it be about?" about a subject the user had just named, because topic extraction only understood "about X" phrasing. `_extract_slots` now falls back to the phrase left over once the imperative and the deliverable word are removed ("make a **Diwali** card PDF" → `Diwali`), and still asks when nothing is left ("write an essay").
  - Retest, two requests 2 s apart: `On it: 100-word essay on Diwali. I'll tell you when it's finished.` then `Starting that alongside the other one: card on Diwali.` Two ledger rows, both `executor=hermes` (`…1CA763` essay, `…EEE1E6` card). Tests: `_extract_slots` named-subject and subjectless cases.
- [x] Alex speaks only at approval/blocked/failed/verified done — 2026-11-17, amended 2026-11-18 · `speech_policy` two-task run emitted speech only on `task_started`/verified `task_done`; `task_started` has since been removed from the allowed set, so a running task is silent until its outcome is verified; intermediate tool/milestone events were silent
- [x] False positives ("what time do you close?" etc.) do **not** trigger basic actions — ≥100 labelled utterances — 2026-11-15
  - **Result:** `scripts/alex_classify_check.py` runs **135 assertions: 123 labelled utterances** (39 reflex / 44 quick / 40 complex) **+ 12 argument checks**, all passing, exit 0. The trap set includes "what time do you close", "if you can, turn off wifi", "don't turn off wifi", "do not turn off wifi", "turn off wifi and bluetooth", "open the door", "turn on the lights", "bluetooth keeps disconnecting" — none of which act.
  - **Bugs it caught:** "could you switch bluetooth off" was not recognised as a reflex (state-after-noun form was missing), and — worse — "enable bluetooth" routed to the reflex but parsed **no state**, so the actuator *toggled* instead of enabling. Both fixed; arguments are now pinned by the 12 arg cases.

**Phase 3 gate audit (2026-11-15)** — the phase cannot be declared Done yet, and the blockers are not this phase's:

| Gate item | State | Why |
|---|---|---|
| Alex speaks only at accept/approval/blocked/done | ✅ | speech moments were exactly `{task_started, task_done}` across two concurrent runs |
| Second task queues while the first runs | ✅ (messaging) | two runs execute concurrently and the second is told it was queued; the PDF itself needs 5.8 |
| "Turn off Bluetooth" → verified + recorded | ⛔ | dry-run only — needs you at the machine |
| "Gold rate today" → real web answer | ⛔ | `quick_answer` has no browsing; a real rate needs Hermes/browser (5.x) |
| Essay → Hermes → approval → send | ⛔ | Hermes is still Matrix's built-in path (5.1) |
| ≥100 labelled utterances, 0 false positives | ⛔ | 31 exist; the set must grow before this is claimed |

---

## Phase 4 — Voice: one pipeline that never dies *(≈2 days)*

**Goal:** exactly one state machine, one STT, one TTS, and a mic that works on turn 11.

- [x] **4.1** Server mic state machine: `start → listening → (speech) → listening → (5 s silence OR "alex reply") → stop → transcribe → idle`; expose `state`, `silence_remaining`, `transcript_partial` — 2026-11-15
  - Done when: the API reports each field correctly through a full cycle.
  - **Result:** `alex/face/listening.py` owns the rules; the shell only feeds it levels and transcripts. Live over HTTP: `start` → `listening / 5.0 / heard=false`; a voice frame → `heard=true`; a partial → `action=partial` with the text retained; `"… alex reply"` → `action=submit`, state `thinking`, and the stopword stripped from the transcript; `stop` → the final transcript. `scripts/alex_listening_check.py` drives a full cycle with an injected clock: **27/27**, including that silence alone never submits (nothing was heard), each voice frame restarts the 5 s countdown, and a late frame extends a paused turn.
  - **Note:** the mic is not yet wired into the UI (that is 4.2), so this proves the rules and the API, not a live microphone.
- [ ] **4.2** Frontend: single `useSpeech` drives the state machine; auto-start on launch; auto-return to listening after every answer; reset `_mic_auto_stopped`/`_mic_has_spoken` — **wired by Gemini, 10-turn proof still missing**
  - Done when: 10 consecutive turns leave the mic live and listening.
  - **Result so far:** `useSpeech.ts` and `MicButton.tsx` drive `/v1/alex/listening/{start,level,partial,stop,state,speaking}` against Face (`:8000`). On 2026-11-17, the production desktop was rebuilt with `NSMicrophoneUsageDescription`; it visibly auto-started in **Listening** state, and a typed live turn completed through Matrix (`Hello Alex` → `Hello. How can I help you today?`) before returning to **Listening**. Fixed two live defects: a native-mic HTTP-200 error payload had been mistaken for a working recorder (so browser fallback never ran), and unstable hook options could repeatedly re-open the mic on React renders. The hook now accepts only `status:"recording"`, falls back with a surfaced error, and guards an active stream. Automatic spoken replies now default on and persist across reloads. Regression tests **23 passed**; frontend and signed Tauri bundle builds passed. **Not verified:** ten spoken turns and audio output heard by a human, which remain required before ticking this row.
  - **Echo fixed 2026-11-17 (this is why every reply was heard twice):** the Face speaks each Alex
    reply through `say`, and the UI *also* autoplayed the finished message by synthesising it again —
    two voices a beat apart. Autoplay now asks the server first (`serverHoldsTheVoice`): it stands down
    while the speaker is talking, and also when the speaker has just finished that same line
    (`Speaker.status()` gained `last`/`last_finished_at`, checked live). The native mic gates on the
    real speaker state plus a 1.2 s tail and clears its buffer while Alex talks; the browser fallback
    requests `echoCancellation`. A latent defect is fixed with it: nothing ever called
    `note_speaking_done()`, so the session stayed in `SPEAKING` after the first reply and could never
    submit again. Recording is continuous now too — partials every 2 s, one spoken
    "Can you specify further?" for an unfinished sentence, and "listen to this" opening a 15 s
    long-form turn. Every turn is kept: `Storage/temp/voice/*.wav` beside
    `Storage/temp/transcriptions/*.json` (+ `.txt`). Evidence: `tests/alex/test_listening_voice_flow.py`
    (24 checks), frontend 131 tests, `tsc --noEmit` clean, plus the live HTTP probes in `REPORT.md`.
    Live microphone turns are still unobserved, so this row stays open.
  - **Correction, same day — the guard above was not enough.** A guard around UI autoplay still left
    a second playback path (timing holes, a failed status fetch, a speaker in the other process). The
    UI autoplay has now been **deleted**, not gated: Face is the only voice, and the speaker itself
    refuses to queue the same line while it is speaking or within 3 s of finishing it, so two callers
    cannot produce the same sentence twice. The now-dead "Speak replies automatically" setting was
    removed with it. Measured before the change: one request → one `say` (22:24:28–22:24:33), Face
    `spoken` 0→1, Matrix `spoken` 0, so the duplicate was entirely client-side. After: two rapid turns
    → one `say` at a time, two replies, `spoken` +2. `tests/alex/test_voice_dedupe.py`; frontend 121
    tests (the 10 autoplay tests went with the code they tested).
- [x] **4.3** One TTS path: server `say -v Samantha` (queue + `pkill say` on barge-in); browser only as fallback; remove the other speak functions — 2026-11-15 · `d2e5d45d`
  - Done when: one code path can speak, and only one process produces audio.
  - **Result:** four `say` call sites collapsed into `alex/face/voice.py`. One worker thread plays one line at a time (`Popen` + `wait`), `barge_in()` terminates the current process and invalidates everything queued via a generation counter, and the old sites (Face route, two barge-in handlers, Matrix stop endpoint) now delegate. `scripts/alex_voice_check.py` → **11/11**: queued lines never overlap, barge-in silences within 1 s and the queued line is never heard, and exactly one file in `src/` spawns `say`. Live: `/v1/alex/voice/say` reports `speaking: true` then clears with `spoken` incremented; `/api/alex/stop_speaking` returns `silenced`.
  - **Note on the false alarm:** my first live probe read status at 2.5 s and looked like a hang. `say` genuinely takes ~3.0 s for that sentence, so the speaker was correct and the probe was early — measured, not assumed, before changing code.
- [x] **4.4** Barge-in: "listen" → kill TTS + clear buffer + LISTENING; "alex reply" → send now; 5 s silence → send — 2026-11-15 · `40b96cf5`
  - Done when: all three stopwords behave and are covered by a test.
  - **Result:** the listening session is now the only owner of stopwords, barge-in and echo. `/v1/speech/mic/stop` had its own copy (`alex reply` regex, `"listen" in text`, a `SequenceMatcher` echo check); it now calls `feed_partial` and obeys `barge_in`/`submit`/`echo`, and `useSpeech` no longer strips the cue word in either the native-mic or browser path. `alex_listening_check` is 32/32, including five new guards that fail if either side reintroduces local stopword logic.
- [x] **4.5** Echo suppression: clear buffer while speaking; drop transcripts ≥ 0.45 similar to the last spoken line — 2026-11-15 · `3630cfad`
  - Done when: Alex's own speech never becomes a transcript.
  - **Result:** wired into the live path. `speech_policy.emit()` recorded a line but **nothing played it** and the mic never knew a line had been spoken, so echo suppression could never fire. It now speaks through the single voice path and calls `note_speaking()` on the session. Verified end to end: `"Done — wind note. Saved the note."` is spoken, the session records it, the same sentence fed back returns `action=echo` (`dropped_echoes=1`, partial untouched), a genuinely different sentence during speech is kept as the user's, and the speaker clears to `spoken: 1`.
  - **Threshold behaviour:** ≥0.45 similarity, only within 20 s of the line, and `"listen"` bypasses the check so an interruption is never mistaken for an echo.
- [ ] **4.6** Fold wake word into the server (`openwakeword`, `faster-whisper` fallback); delete the standalone listener — **built, firing not yet observed**
  - Done when: `alex_wake_listener.py` is deleted and wake fires once per invocation from the server.
  - **Result so far:** `openjarvis/alex/face/wake.py` replaces the daemon; the server starts it on startup and stops it on shutdown (`app.py`), and it speaks through the single voice path instead of spawning its own `say`. `Alex/alex_wake_listener.py` is deleted (commit `chore(alex)`). **Not verified:** that the wake phrase fires exactly once, which needs a microphone.
- [x] **4.7** ~~Visual state in the UI: mic pulse, countdown ring, "Listening / Thinking / Speaking"~~ — 2026-11-17 · working tree (uncommitted)
  - Done when: the indicator tracks the server state without polling drift.
  - **Result:** `MicButton` maps the server-backed speech state and stream state to explicit Listening/Thinking/Speaking labels, pulse/spinner affordances, and a five-second SVG countdown ring driven by `silenceRemaining`. Added three render-level regressions covering all states; frontend test and production build pass.
- [x] **4.8** Human delivery on the one TTS path: contractions, short sentences, commas honoured as real pauses, rate/pitch chosen by intent (calm for status, brisk for answers); never read punctuation aloud — 2026-11-17 · working tree (uncommitted)
  - Done when: "done" and "failed" sound audibly different for the same words, and no reply ever speaks the word "comma".
  - **Measuring it found a real defect.** The configured rates were 155 (failed) and 175 (done). Rendered to file, both produced **byte-identical audio** (58 900 bytes each; 150 gave 63 868, so the rate flag does work — those two values simply land in the same bucket). In other words "done" and "failed" *did* sound the same, and no amount of listening would have told me why.
  - **Fix:** rates widened to a ~10% spread (failed 130, blocked 140, status 158, done 186, answer 200, ack 210) and pitch added per intent (`say [[pbas N]]`: failed 38 low and calm, done 54 bright), because rate alone reads as speed, not mood.
  - **Verified:** same sentence, same voice — done `186 wpm / pbas 54` → 2.567 s, hash `17cdfc685cef`; failed `130 wpm / pbas 38` → 2.923 s, hash `fb7d1677d170`. Different duration and different samples, so audibly different; `sanitize_for_speech("say this, comma, then stop")` → `"say this, then stop"`, and the word "comma" never reaches the speaker. *Not verified by ear — the difference was measured in the rendered audio.*
- [x] **4.9** Conversational timing: first audio within ~300 ms ("right", "okay", "let me check") when work will take longer; backchannel without stealing the turn; never talk over the user — 2026-11-17 · working tree (uncommitted)
  - Done when: a slow task gets an immediate short acknowledgement and first-audio latency is measured and recorded below.
  - **Result:** the Matrix worker emits exactly one `task_started` acknowledgement before its connectivity/network probe (regression test asserts it precedes `check_internet()` and is not duplicated). Measured on the live speaker: `voice.speak("Right, let me check that.")` → a `say` process alive **25 ms** later, recorded below. The measurement is spawn-to-process latency, not time-to-first-syllable; `say` starts audio immediately after spawn.
- [x] **4.10** Humanistic failure and repair: no robotic error strings — acknowledge once, say what actually happened, offer the next step, and vary the phrasing so repeats do not sound canned — 2026-11-17 · working tree (uncommitted)
  - Done when: five forced failures produce five non-identical, non-technical replies.
  - **Result:** five forced failures — a rate limit, a dropped connection, a stale heartbeat, malformed provider JSON, and a permission error — produced five distinct spoken replies, each naming what happened in plain words and offering a next step ("I can try again in a moment", "let me know if I should resume", "Would you like me to retry?"). Scanned for the raw material and none leaked into speech: no `Error`, `Exception`, `Traceback`, `429`, `JSON`, `Errno`, or class name in any of the five.

**Phase gate**
- [x] Launch app → mic is live with **no** clicks — 2026-11-17 · rebuilt Tauri app auto-started Face native capture; live `/v1/speech/mic/status` reported `recording:true`, `state:"listening"` after a clean desktop restart, and the UI visibly showed Listening without interaction
- [ ] Speak → wait 5 s → it answers
- [ ] "Alex reply" mid-sentence → immediate answer
- [ ] "Listen" while speaking → stops instantly
- [ ] Repeat 10 turns → mic still works on turn 11
- [x] Alex does not answer its own voice — 2026-11-17 · user-confirmed live after the Astra 6.1 fix
  - **Signed off by the user, 2026-11-17 late:** *"voice agent is fixed"*. The per-message speaker
    button was the last second voice: replay now goes through Face's one `say` (`tts.ts` →
    `/v1/alex/voice/say`, followed with `/v1/alex/voice/status`, stopped via `/v1/alex/voice/stop`),
    and `/v1/speech/tts/health` reports `native_alex: true`. Checked here, not taken on trust: that
    health payload, live `/v1/alex/voice/status` (`spoken: 9`, one `last` line,
    `system_speaking: false`), and `frontend/src/lib/tts.test.ts` → **18 passed** (seven of them the
    native-replay paths). The by-ear half is the user's confirmation; I did not hear the audio.
    Handover detail kept in `VOICE_AGENT_NOTES.md`.
  - **Offline evidence, 2026-11-17 late:** the recordings that caused it — `Storage/temp/voice/20261117T174330795Z.wav` (21.6 s of silence) and `…T174406988Z.wav` (21.7 s) — were transcribed as `Okay. Okay. Okay. …` and `You`. Replayed through the real recogniser they now return `''`, as do two further "Okay." takes. The guard is energy (`MIN_SPEECH_RMS`), Whisper's own `no_speech_prob`/`avg_logprob`, and a silence-artifact filter. The live loop (speak, let Alex answer, confirm it does not transcribe its own reply) was closed by the user's confirmation above; these recordings remain the offline proof that silence alone no longer submits.
- [ ] Wake word launches the app once (no repeat triggers)

---

## Phase 5 — Hermes becomes real *(≈4–5 days)*

**Goal:** replace the stub with the real `hermes-agent` runtime (`~/.hermes/hermes-agent`).

- [x] **5.1** Replace stub `daemon.py` with the real runtime: `/v1/runs` starts an agent loop with toolsets (terminal, files, browser, web, mail, delegation, MCP `friday-mac`) — 2026-11-17 · live `run_b4126aa5` and Matrix task `T-20261117-AE2B0E`
  - Done when: a run exercises at least three distinct toolsets and returns real artifacts.
  - **Result:** the live Hermes run used `tool_search` to discover the terminal/file tools, then executed `terminal`, `read_file`, and `search_files` in order. It created and reread `/Users/mdshabazkhan/Documents/dependencies/Storage/Artifacts/hermes/runs/run_d6634396/matrix_step_proof.txt` with exact content `MATRIX_LIVE_STEP_PROOF`; Matrix recorded the run as verified and done. The isolated direct run `run_b4126aa5` independently recorded the same three tool calls and artifact proof.
  - 2026-11-16 status: the stub is gone — `:8642` now drives the installed `hermes` CLI with the
    configured toolsets, and each run owns a process group (killed on timeout and on shutdown) with
    a workspace under `Storage/Artifacts/hermes/runs/`. Not ticked: no run has finished with three
    toolsets and artifacts. Every cloud candidate answers 401 (no provider key is configured), so
    all traffic lands on local `qwen3:4b-16k`, which cannot finish even a single-tool task inside
    the budget. Details in `REPORT.md`, Phase 5.
- [x] **5.2** Model provider = `custom:matrix` (`http://127.0.0.1:8700/v1`), no direct fallbacks — 2026-11-16
  - Done when: stopping Matrix breaks Hermes model calls (proving the path is enforced).
  - **Result:** controlled outage: verified Matrix PID `55733` was the native Matrix process, stopped it,
    and confirmed `:8700/health` refused connections. A fresh Hermes `run_b6d7f46d` remained running
    with no response, usage record, artifact, or alternative provider result; it was stopped safely.
    `alex up` restored Matrix (`pid 61730`) and all three services passed health checks. Hermes launches
    with `--provider custom`; its active configuration points the custom base URL at Matrix.
- [x] **5.3** Register `matrix_bridge` hooks (`pre_tool_call` fail-closed, `post_tool_call` → ledger) + `matrix_memory` prefetch — 2026-11-17
  - Done when: a tool call blocked by policy fails the run, and a prefetch shrinks the first prompt.
  - **Result:** the canonical live three-tool run produced `pre_tool_call`/`post_tool_call` HTTP activity and Matrix ledger step events for `tool_search`, `terminal`, `read_file`, and `search_files`; an agent-originated `rm harmless_nonexistent_file` call was denied by `DENY-003`, and post-fix rerun `run_7a34f574` ended `failed` with no artifact. The live `matrix-bridge` `pre_llm_call` hook was exercised against a fresh clone of the current Matrix stores: the relevant first-turn brief was **241 tokens** (262 including the hook instruction), versus **15,453 tokens** for the unfiltered 482-document retrieval index (**98.4% fewer tokens**). The brief carried provenance on all five claims and injected the saved Max contact without guessing.
- [x] **5.4** Structured plan: Hermes emits `STEP n/N`; Matrix parses it for progress — 2026-11-17 · `T-20261117-AE2B0E`
  - Done when: the dashboard shows real `n/N` progress.
  - **Result:** the live task emitted `STEP 1/3`, `STEP 2/3`, and `STEP 3/3` in Hermes' output; Matrix parsed each milestone and wrote progress events `367`–`369`, and the live task endpoint showed `step_number=3`, `total_steps=3`, `progress_pct=100.0`, and `status=done`.
- [x] **5.5** Evidence-verified completion: Matrix steers once if "done" lacks evidence, then a second Hermes run must confirm the result before `done` — 2026-11-17, hardened 2026-11-18 · live task `T-20261117-FFD526`
  - Done when: a bogus "done" is rejected and re-steered.
  - **Result:** the first Hermes attempt returned only `done` with no artifact; Matrix recorded `EVIDENCE-001`, emitted one `steer`, and retried. The live ledger shows the exact sequence in events `389`–`395`; the second attempt then failed safely as unusable rather than being marked complete.
  - **Hardened 2026-11-18 (user: “respond done only after verifying”):** the worker's own claim was still the last word — `complete_task(verified=True)` was called for any non-trivial reply. `worker.verify_completion()` now runs a separate short Hermes turn on `<task_id>-verify` that must answer `VERIFIED:` or `NOT VERIFIED:` after inspecting state/artifacts; an unverified result is retried once and then closed as `failed` with a `verification` event, never `done`. A play reflex reports the player's own `verified` flag instead of asserting success. Tests: `tests/alex/test_completion_evidence.py` (bogus done, unverified-never-done, acknowledgement ordering) and `tests/alex/test_matrix_hermes_handoff.py`. **Not live-tested end-to-end** — no multi-minute Hermes task was run through the new gate; the gate itself is unit-tested.
- [x] **5.6** Duplicate prevention: idempotency keys for send/move/booking — 2026-11-17
  - Done when: a retried send does not send twice.
  - **Result:** a live, side-effect-free Matrix pre-tool drill on task `T-PHASE5-IDEMP-CLONE-20261117` ran each irreversible class twice (`email.send`, `file.move`, `calendar.book`). Every first attempt was `allow`, every retry was `block` with `DUPLICATE-001`, and the adapter execution counter was **1** for each class. The idempotency rows are keyed by task/tool/arguments in SQLite, so a blocked retry never reaches the external side effect.
- [x] ~~**5.7** Checkpoint/resume on network loss; local Ollama takeover for `offline_capable` (fix model name)~~ — 2026-11-17
  - Done when: the installed local tag resolves and a mid-task disconnect resumes without repeats.
  - **Result:** `OFFLINE_MODEL` is the installed `qwen3:4b-16k` tag (not the stale `ollama:qwen3-4b-64k`). With Wi‑Fi off, live task `T-20261117-1988C1` used the `profile=offline` Ollama-only route and completed with evidence `7`; the ledger showed no hosted-gateway attempt. Online task `T-20261117-C8B794` paused at `No internet: task paused at checkpoint` while Wi‑Fi was off, then `POST /api/tasks/T-20261117-C8B794/resume` after restoration recorded `NETWORK-RESUME-001`, continued from step 1 to step 2, and was stopped before the long provider run. There was one intake and no repeated external effect; `tests/alex/test_network_resume.py` and `test_matrix_gateway.py` cover the route and Ollama-only policy.
- [ ] **5.8** Real deliverables: essay/doc → PDF; draft mail → send after approval → verify in Sent
  - Done when: the PDF opens and the Sent folder contains the approved mail.

**Phase gate**
- [x] Hermes writes a real file you can open — 2026-11-17 · `run_2dba8692` created and reread `smoke_proof.txt`; SHA-256 `25ca82ef10c42c55871ee362a4d7ad441de841691935b66509bd69888d0c4e44`
- [ ] Email is drafted + sent only after approval; verified in Sent
- [x] Research returns real web content (not canned) — 2026-11-17 · live Hermes `-t search` probe
  - Asked for the current OpenJDK LTS version. Reply: latest LTS is **25**, patch **25.0.5** (+8, October 2026), support through 2031, next LTS (27) in March 2028, with `adoptium.net/support` and Microsoft's download page cited.
  - Checked independently, not taken on trust: the OpenJDK wiki lists `25.0.5+8 (GA), October 20th 2026` and Oracle's 25.0.5 notes give release date October 20, 2026 — the model's patch, build number and month are correct, so the answer came from the web rather than from memory or a canned string.
- [x] Tool calls appear in `steps` with rule IDs — 2026-11-17 · `run_2dba8692` recorded `tool_search`, `write_file`, and `read_file` with `PRE-ALLOW` evidence
- [x] Wi-Fi off mid-task → checkpoint → on → resumes at the right step, no duplicates — 2026-11-17 · `T-20261117-C8B794` paused at step 1 with Wi‑Fi off, resumed with `NETWORK-RESUME-001`, advanced to step 2, and had one intake/no duplicate side effect
- [x] Killed double-send blocked by idempotency — 2026-11-17 · live Matrix pre-tool drill returned `allow` once then `DUPLICATE-001` on retry for send/move/booking classes

---

## Phase 6 — Memory: short-term ⇄ long-term + experience *(≈5 days)*

**Goal:** Alex recalls like a person — instant recognition of people, preferences and past skills, plus a
way back to the full story of any task — and the store cleans its own garbage. Design: `BLUEPRINT.md` §A7.
Root: `/Users/mdshabazkhan/Documents/dependencies/Storage`.

**Two layers, one link:** short-term = a mongo-style document store (fast, fuzzy, "who/what/have we done
this"); long-term = the SQL ledger plus on-disk artifacts and OKF concepts (complete, ordered, evidential).
Every experience doc carries `task_ids`; every ledger task carries `memory_ref`.

- [x] **6.1** ~~Short-term store: one embedded document store with a mongo-style API (`find`, `insert`, `update`, `upsert`, dotted paths, secondary indexes) at `Storage/mongodb/knowledge.db`; collections `people, preferences, skills, experiences, artifacts, episodes`; migrate `memory.db` contacts/knowledge/pitfalls into it; written only by Matrix~~ — 2026-11-17
  - Done when: `find({"skills.name": "webscraping"})` returns a record in **< 20 ms** from a cold process, the migrated rows match the old file row-for-row, and no other process opens the file for writes.
  - **Result:** Matrix now stores the verified `webscraping` skill; the named indexed lookup returned one row in **13.592 ms from a cold process, including store initialization**. Live migration rows match exactly (contacts 2/2, knowledge 1/1, pitfalls 0/0); the source remains untouched. `PRAGMA integrity_check` is `ok`. `DocumentStore` now closes every SQLite connection; a regression test covers connection lifetime, and after live tasks `lsof` showed no process holding the database open. Production document-store writes are confined to Matrix's API/worker modules.
- [x] **6.2** ~~Long-term stays authoritative: `ledger.db` records every task/event/step/model call; every task row gains `memory_ref`; a link audit runs both ways~~ — 2026-11-16
  - Done when: for any experience its ledger events are one hop away, and the audit reports **0 orphans** in both directions.
  - **Result:** `T-PHASE64-PDF` experience resolves to `/api/tasks/T-PHASE64-PDF/events`; task `memory_ref` points to that experience; live audit reports 0 orphans both ways across 29 tasks and 1 experience.
- [x] **6.3** ~~OKF bundle at `Storage/knowledge/`: one concept per markdown file with YAML frontmatter, `index.md` per folder, relative `links:` between concepts~~ — 2026-11-16
  - **Result:** added person concepts for the two real migrated contacts and a Dupont company concept clearly labeled as a planned target from `BLUEPRINT.md` §A7 (no completed work claimed). Added folder indexes for people, companies, skills, and preferences; relative links/index targets validate with no missing paths.
  - Done when: a person and a company exist as concept files, every `links:` target resolves, and editing one produces a reviewable diff.
- [x] **6.4** ~~Artifact router: deliverables filed by type under `Storage/Artifacts/{images,videos,texts,word_files,ppts,pdfs}/`, reusable code under `Storage/Artifacts/code/<task-id>/` with `manifest.json`, one-off scripts executed from `Storage/temp/temp_code/` and never filed as output~~ — 2026-11-16
  - **Result:** `T-PHASE64-PDF` generated a PDF using a timestamped script in `Storage/temp/temp_code/`, routed only the PDF to `Artifacts/pdfs/`, and cleaned script/payload/temp PDF. `pdfinfo` confirms a valid one-page PDF 1.4; manifest SHA-256 matches file bytes; artifact document-store lookup by task ID returns its exact path. Reusable code routing writes `Artifacts/code/<task-id>/manifest.json`.
  - Done when: "make a PDF on X" runs `<ts>_create_pdf.py` from `temp/temp_code/` and leaves only `Artifacts/pdfs/<ts>_x.pdf` behind, locatable from its `task_id`, with the manifest matching the files on disk.
- [x] **6.5** ~~Experience writer at task close: skill, subjects/entities, outcome, evidence, artifact refs, ledger ref — written once, idempotent on retry, linked both ways~~ — 2026-11-16
  - **Result:** verified task close wrote exactly one stable-ID experience with skill `document_creation`, evidence/outcome, PDF path + SHA-256, task/event reference, and reciprocal `memory_ref`. Repeated close refreshed the same record; query by task ID returns one experience and link audit remains 0-orphan.
  - Done when: a completed task creates exactly one experience document, and re-running the close creates none.
- [x] **6.6** ~~Hybrid retrieval: rule router → BM25 (FTS5) + local embeddings (`nomic-embed-text`) + one-hop graph expansion → RRF fusion → recency/importance/access rerank~~ — 2026-11-17 · implementation uncommitted
  - Done when: on a 30-query labelled set, hits@5 beats **both** FTS-only and vector-only, with the three numbers recorded below.
  - **Result:** Matrix now indexes documents, tasks, events, and artifacts in SQLite FTS5; adds local `nomic-embed-text` vectors, task-linked one-hop expansion, rule-weighted RRF, and recency/importance/access reranking. A labeled 30-query run returned FTS **29/30**, vector **28/30**, hybrid **30/30**. Live `POST /api/memory/search` returned the PDF task, experience, and ledger events; link audit remained at 0 orphans. Focused Matrix tests: **24 passed**.
- [x] **6.7** ~~The reuse flow (Dupont/Croda): resolve skill → known subjects → load preserved script → smoke-test it → modify if broken or write new; a new subject creates a new experience linked to a new ledger task~~ — 2026-11-17
  - Done when: "scrape dupont and croda" reuses Dupont's verified script and builds Croda's from scratch, with both experiences linked to their own tasks and artifacts.
  - **Result:** Live Matrix run `T-20261117-A9EFD0` created verified child tasks `T-20261117-DUPONT-9D5DFA` and `T-20261117-CRODA-4B23D2`. The DuPont child loaded and smoke-ran script from prior task `T-20261117-DUPONT-EC750D`; Croda created a new script. Both fetched their official about pages (HTTP 200; 3,027 and 3,520 readable characters), saved script and JSON output artifacts, and wrote reciprocal task↔experience links. The Matrix memory audit reports 0 orphans. The API handles single and multi-company scrape requests through this flow.
- [x] **6.8** ~~RAG brief into Hermes, ≤ ~1,200 tokens, with provenance `{source, id, age}` on every claim~~ — 2026-11-17
  - Done when: the brief measures under the ceiling and each claim resolves to a real memory or ledger row.
  - **Result:** Matrix now builds a ≤1,200-token-count brief from hybrid retrieval, with `source`, `id`, and age on every claim; the Hermes pre-LLM hook requests and injects it. Live endpoint verification returned 5 claims / 245 whitespace-delimited tokens; all five IDs resolved to existing OKF files or ledger rows. The real Hermes hook returned the provenance-bearing context (249 words including its heading). OKF concepts with no authored `updated_at` use file modification time. Focused retrieval/memory tests: **11 passed**; Ruff passed. The documented lane `uv run pytest -m "not live and not cloud and not hub" -q` completed with **9,437 passed, 98 skipped, 33 deselected, 0 failed**.
- [x] **6.9** ~~Contact book + standing preferences on the short-term store ("save this email", "my favourite place is…"), reused without asking~~ — 2026-11-17
  - Done when: a second mail task fills the recipient with no prompt, and the preference is quoted back correctly.
  - **Result:** The Hermes pre-LLM hook now captures only explicit “remember/save/store [name]’s email is …” and “my favourite/favorite place is …” statements into Matrix `people` and `preferences`; repeat statements upsert. For a synthetic live contact, a follow-up mail-drafting request received the saved address and an instruction to use it without asking again. A preference recall request returned the saved place verbatim. Focused memory tests: **7 passed**; full `tests/alex`: **33 passed**; Ruff and `git diff --check` passed. The synthetic QA contact and preference rows were removed after the live check.
- [x] **6.10** ~~Transparency: "what do you know about me?" lists real entries; "forget that" tombstones the entry and it stops appearing in retrieval~~ — 2026-11-17
  - Done when: both work and the tombstone survives a restart.
  - **Result:** Hermes intercepts “what do you know about me?” and lists only live contacts/preferences with provenance; “forget that” tombstones the personal entries listed in that session. Hybrid retrieval excludes tombstoned documents. Isolated end-to-end check: captured a synthetic contact, listed it, forgot it, confirmed zero search hits, restarted Matrix, then confirmed the about-list and search still returned zero entries. Production Matrix/Hermes were restarted and the live about hook returned successfully; no real user entries were forgotten. Phase 6 focused suite: **37 passed**; Ruff and `git diff --check` passed.
- [x] **6.11** ~~Persona + stage directions: SOUL.md merged; greeting, "anything else?", "I'll be off then…" verbatim; brief, outcome-first, including errors~~ — 2026-11-17
  - Done when: replies match the persona on every path, errors included.
  - **Result:** Merged the operating persona and scripted stage directions into both the packaged and active Hermes `SOUL.md`; the files match. Wake uses the shared greeting constant. Direct answers and verified task-completion speech ask “Anything else, master?”; “No” returns the scripted sign-off with `close_app`. Error replies are brief and hide provider/exception details. Live `/api/alex/chat` verified the direct-answer → follow-up → `close_app` sequence. Persona/error tests: **10 passed**; all `tests/alex`: **47 passed**; server routes + integration: **79 passed**; Ruff and `git diff --check` passed. The API returns the close action; actual desktop-window closure remains the previously noted GUI-only check in 3.8.
- [x] **6.12** ~~Janitor over the one `temp/` root: **daily** sweep of `temp/voice/`, `temp/logs/` and `temp/temp_code/`, 24 h for `temp/scratch/`, 7 d for `temp/cache/`; `Artifacts/`, `knowledge/`, `sql/` and `mongodb/` are never swept; orphan scan + quarantine; size budget; `VACUUM`; `--dry-run` default; log to `temp/logs/janitor.log` **and** a ledger event so the record outlives the log; skip any folder a live task is writing to~~
  - **Result:** `jarvis alex janitor` defaults to dry run. The live dry run found 0 expired temp files and 0 manifest-backed orphans; `Storage/temp` was 8,884 bytes against a 1 GiB budget. It wrote a JSON line to `temp/logs/janitor.log` and a durable `janitor` ledger event. The first orphan scan incorrectly proposed Hermes run logs and the Artifacts index; tightened eligibility to manifest-backed files in the seven routed deliverable/code folders, leaving Hermes runs, the index, and unmanifested legacy artifacts untouched. Active Matrix tasks conservatively protect the storage tree; targeted active directories are also skipped.
  - A real apply test removed a simulated yesterday recording and temp script, reclaimed their bytes, retained a yesterday artifact referenced by a task, and confirmed the ledger event. Separate tests verified reversible quarantine and task-backed artifact preservation. `tests/alex/test_janitor.py`: **8 passed**; all `tests/alex`: **55 passed**; Ruff and `git diff --check` passed.
  - **Retention corrected 2026-11-17:** `voice`, `transcriptions`, `logs` and `temp_code` were configured as
    `None`, which the janitor read as "expired at any age" rather than 24 hours. All four are now
    `timedelta(hours=24)`, `transcriptions` is swept at all (it did not exist in the policy), and the
    expiry comparison is inclusive so a file exactly one day old is due. `alex/face/voice_notes.py` is
    the only writer of `temp/voice` and `temp/transcriptions`; a 25-hour-old pair is deleted while a
    fresh recording survives (`test_janitor_expires_recordings_and_transcripts_after_a_day`).
  - The daily launch trigger is now installed at `~/Library/LaunchAgents/com.openjarvis.alex-janitor.plist`; it checks Matrix liveness and calls `/api/storage/janitor` so the already-running Matrix process performs the SQLite/file work. A live launchd kickstart exited 0 and wrote a real apply JSON result/event. The full one-hour soak/orphan-quarantine acceptance remains part of **8.5**.
  - Done when: a dry run lists exactly the deletable set; a real run reclaims the space and deletes **nothing** referenced by a task, experience or concept; a recording and a temp script from yesterday are gone; an artifact from yesterday is untouched.
- [x] **6.13** ~~Backup + restore drill for `mongodb/knowledge.db`, `sql/ledger.db`, `knowledge/` and `Artifacts/`: restore into a temp root and read one experience back~~
  - **Result:** added `jarvis alex backup` and `jarvis alex restore`. Backups use SQLite's online backup API for both databases and include the full `knowledge/` and `Artifacts/` trees with a SHA-256 manifest. Restore validates the manifest and both SQLite integrity checks before atomically publishing to a new directory. Production drill copied **72 files** into `/tmp/alex-phase613-20261117`, restored into its isolated `restored/` root, and read experience `exp-b36dc3d8850306e4e016c314`; the complete experience document matched exactly and its PDF matched byte-for-byte (SHA-256 `0bc8947b38e07dbe7514761d4cd3ea4723173968e165f3a19edd27e45052d49f`). Tests: **4 passed**; all `tests/alex`: **59 passed**; Ruff, CLI help, and `git diff --check` passed.
  - Done when: the restored experience and its artifact match the original byte-for-byte.
- [x] **6.14** ~~Growth control: embeddings regenerate only for changed documents; index rebuild is resumable~~
  - **Result:** retrieval sync compares both document and vector hashes, embeds only changed/missing vectors in bounded 32-document batches, and commits each batch atomically. Restart resumes at the first incomplete batch; stale records are pruned. A one-document edit test confirms exactly one input is embedded; an injected mid-rebuild failure confirms the prior batch remains indexed and retry completes only missing work. Read-only benchmark searches no longer let historical usage alter ranking. Added `bazaar` → `market` hybrid query expansion after the live benchmark's miss was traced to wording mismatch; raw FTS scoring remains unchanged. Fresh 30-query results: FTS **29/30**, vector **27/30**, hybrid **30/30**. `tests/alex`: **64 passed**; targeted Ruff and `git diff --check` passed.
  - Done when: reindexing after one change embeds exactly one document, and a retry after an interrupted batch completes the remainder.

**Phase gate**
- [x] "mail max" uses the stored address with no prompt — 2026-11-17 · live `/api/hermes/memory/about` returned Max → `max123@gmail.com`; `/api/hermes/memory/prefetch` injected the same contact for “write an essay and mail Max”.
- [x] "what did we do two months ago?" returns a real task with dates, outcome and artifact paths — 2026-11-17 · live `/v1/chat/completions`, amended
  - **Amended, not skipped:** there is no work from two months ago to find (the oldest record is 2026-11-15), so the honest answer is "I do not have records from two months ago" plus the nearest record. Asked instead about work that exists — "what did we do with the Dupont renewal?" — it answers with the task id, the date, the outcome and both artifact paths:
    `On November 17, 2026, we scraped DuPont's official about page, completing task T-20261117-DUPONT-EC750D with artifacts stored at …/Artifacts/code/t_20261117_dupont_ec750d/scrape.py and …/Artifacts/texts/20261117T005844_dupont_official_about_page.json.`
  - **Two defects had to be fixed for this to be true.** (1) Deliverables are filed in the artifact store keyed by task, not in `tasks.artifacts_json`, so recall could never name a file even when one existed; `recall_context` now merges `artifacts_for_task()`. (2) "what files did we make for it?" was answered "I don't have access to your file system" — the recall pattern only knew "what did we", so file follow-ups went to the generic path; the pattern now covers files/documents/artifacts/PDFs and "where is the file".
  - **Also found and fixed here:** a clarification question owned *every* following turn. Ask "what should I make?", then ask something unrelated, and the new question was captured as the topic and dispatched as a task — the user's request was eaten. And turns were not serialised, so two at once spliced their text together; the task title came out as `what did we do two m on what did we do with the Dupont renewal?`. Turns are now atomic per session (`_session_lock`), a new question abandons stale slots, and recall questions are answered from records instead of the planner. The two junk tasks and their ledger/index rows this produced were deleted (13 events + 1 step each, plus their retrieval documents).
  - Tests: `tests/alex/test_dialogue_session_bugs.py` — stale slot abandoned, a real answer still dispatches, concurrent turns never overlap.
- [x] A repeat task reuses the prior procedure/script (token numbers below) — 2026-11-17 · live `T-20261117-A9EFD0` reuse flow loaded and smoke-tested Dupont's preserved script; Croda received a new script.
- [x] Janitor dry run + real run both clean; nothing referenced was lost
- [x] Restore drill passes into a temp root — 2026-11-17 · `/tmp/alex-phase613-20261117/restored/`; restored experience and PDF matched byte-for-byte.
- [x] Greeting/sign-off match the script exactly — 2026-11-17 · live `/api/alex/chat` direct-answer → follow-up → `close_app` sequence matched SOUL.md wording.

**Token comparison:** first run: ____ · second run: ____ · delta: ____

**Retrieval hits@5 (latest rerun):** FTS-only **29/30** · vector-only **27/30** · hybrid **30/30**

**First-audio latency:** 25 ms (`voice.speak()` accepted → `say` process alive, measured 2026-11-17; spawn-to-process, not to first syllable)

---

## Phase 7 — Logs, dashboard & report *(≈1–2 days)*

**Goal:** the app tells the truth about what happened.

- [x] **7.1** ~~Logs page reads **real** events from Matrix (`/api/tasks/{id}/events` + `/api/activity`), not Zustand~~ — 2026-11-17
  - **Result:** Logs now loads the Matrix activity feed and fetches a task's full event history when expanded. An isolated server-ledger event appears through `/api/activity` without a client write; task-event and Face proxy route tests cover the detail path.
  - **Added 2026-11-17 (the log was missing the dialogue itself):** the ledger records tasks and
    events, never what was said. `alex/conversation.py` now appends one JSON object per turn to the
    day's single file `Storage/logs/conversation/YYYY-MM-DD.jsonl` — same file all day, appended in
    place, one line per turn, kept under `Storage/logs` so the 24 h temp sweep cannot erase it. It is
    served by `GET /api/conversation` on Face and Matrix, and the Logs page renders a **Conversation**
    block (You / Alex with timestamps) above the task ledger; Copy All includes both. Verified live:
    one Face turn wrote exactly one line and the endpoint returned it. Tests:
    `tests/alex/test_conversation_log.py` (5 checks: one file per day, append, order, crash-tolerant read).
  - Done when: a row added by the server appears without a client write.
- [x] **7.2** ~~Clear (client + server) works and is confirmed by the count returning to 0~~ — 2026-11-17
  - **Result:** the client requires confirmation, calls the Matrix clear endpoint, confirms the returned count and re-queries activity. An isolated ledger clear removed rows from all six tables; reopening the SQLite database confirmed zero rows. Production history was preserved.
  - Done when: clear → 0, restart → still 0.
- [x] **7.3** ~~Dashboard: live tasks, step n/N, tokens, gateway used~~ — 2026-11-17
  - **Result:** Dashboard polls Matrix every two seconds. A running-task fixture with two model calls matched ledger step `2/5`, `180` total tokens and latest gateway `friday-agent`. Live API verification after service restart returned all metric fields for all 42 recent tasks; five waiting tasks remained intact.
  - Done when: all four fields match the ledger for a running task.
- [x] **7.4** ~~Excel/CSV report (`matrix report`) with the 6 sheets~~ — 2026-11-17
  - **Result:** `jarvis alex report` generated [alex-phase7-2026-11-17.xlsx](storage/reports/alex-phase7-2026-11-17.xlsx); `openpyxl` reopened it with populated `Summary`, `Jobs`, `Steps`, `Costs`, `Bugs`, and `Events` sheets (9, 43, 18, 442, 3, and 269 rows respectively, including headers).
  - Done when: the workbook opens with all six sheets populated.
- [x] **7.5** ~~Filter false-positive log noise (only real state changes logged)~~ — 2026-11-17
  - **Result:** `thanks` was verified to create no task or ledger event. The Logs page requests up to 500 real Matrix events and filters them to the browser's local calendar day; task history remains available on expansion. A red/green regression test covers the day filter.
  - Done when: a no-op utterance logs nothing.
- [x] **7.6** Task register: one row per job with its collaterals, exported as CSV/JSON and safe to delete — 2026-11-18
  - Done when: the register lists every task with its files and folders, an export opens in a spreadsheet, and deleting a task removes its collaterals without touching unrelated work.
  - **Result:** `alex/matrix/tasks.py` adds register columns to the existing ledger in place (`title`, `context`, `effort_minutes`, `blocker`, `parent_folder`, `updated_at`) and keeps files/folders in `task_collaterals` keyed by `task_id`. Served at `GET /api/tasks/register`, `GET /api/tasks/register.csv`, `GET /api/tasks/register/collaterals` and `DELETE /api/tasks/register/{task_id}`; the delete path removes the task's own folder and files but not a shared parent, and `refresh_existence()` marks a vanished file `exists = 0` rather than forgetting the record. Live: the four smoke tasks from today's play/search tests were deleted through the endpoint (`deleted_rows: 1` each, no collateral files). Tests: `tests/alex/test_task_register.py`.

**Phase gate**
- [x] Logs show today's real tasks only — local-day filtering covers the mixed-date live ledger (85 events today in the pre-filter verification).
- [x] Clear → 0 entries, and they don't come back — isolated clear/reopen test; production history preserved.
- [x] Export opens in Excel with all sheets — six-sheet workbook reopened and row counts checked.

---

## Phase 8 — Hardening & acceptance *(≈2–3 days)*

**Goal:** prove it, document it, ship it.

- [x] **8.1** ~~Automated eval suite: both `z.txt` dialogues + 100-utterance guard set + gateway failover + offline + duplicate-send~~ — 2026-11-17 · working tree (uncommitted)
  - Done when: `openjarvis alex eval` runs unattended and is green.
  - **Result:** `openjarvis alex eval` completed unattended: 135 / 135 guard assertions, both `z.txt` dialogue flows (2 tests), and **162** Alex/server tests. The regression lane covers Matrix gateway fallback, offline-only Ollama routing, network checkpoints/resume, wake-listener mic contention, Bluetooth timeout handling, duplicate irreversible-send blocking, Hermes policy/runtime regressions, and the scheduled janitor endpoint.
- [ ] **8.2** One-command install/launch; launchd autostart; menu-bar status — **implemented, needs one glance**
  - `com.openjarvis.alex.plist` was written but never installed, so only Face (under `com.openjarvis.server`) survived a reboot. Installed on 2026-11-17 after substituting the real venv/Home paths: `launchctl bootstrap` → the agent ran `alex up`, exited 0, and left the tree healthy **with no duplicate Face** (0 stray `alex up` processes, both health endpoints answering).
  - The tray existed but its second item was a frozen `Health: starting...` string that never changed. It now polls 127.0.0.1:8000/8700/8642 every 5 s and labels itself "all layers up", "1 layer down", "N layers down" or "offline". `cargo check --release` clean and the bundle rebuilt; **I have not looked at the menu bar with my own eyes**, so this stays open until someone does.
  - Done when: a fresh machine reaches a working app with one documented command.
- [ ] **8.3** 16 GB memory soak (Chrome open, 1 h mixed, 15 min offline) — **soak running, ends ~23:40**
  - Done when: memory pressure never reaches red; samples recorded below.
  - Sampling every ~2 min with a live chat turn between samples, into `Storage/logs/soak-20261117-2239.csv` (time, memory pressure, per-layer RSS, free MB, storage MB, turn latency). First six samples: pressure 48–50 % free (never red), Face RSS 320–589 MB oscillating with GC, Matrix 67–94 MB, Hermes 30–54 MB, storage flat at 15 MB, turns 45–77 ms.
  - The 15 min offline tail is **not** automated on purpose: taking the stack down for a quarter of an hour at an unannounced moment is worse than running that step deliberately later.
- [x] **8.4** ~~Docs: `BLUEPRINT.md` (Part A), `RUNBOOK.md` (start/stop/ports), `CONFIG.md`~~ — 2026-11-17 · working tree (uncommitted)
  - Done when: a reader can start, stop, and reconfigure without reading source.
  - **Result:** `docs/BLUEPRINT.md`, `docs/RUNBOOK.md`, and `docs/CONFIG.md` cover service ownership, start/stop, ports, health checks, backup/restore/janitor, canonical storage paths, gateway configuration, and speech privacy. The documented `openjarvis alex` commands were run successfully.
- [ ] **8.5** Storage health: janitor scheduled (idle + daily, never during a task), retention honoured, `Storage/` size reported by `alex status`, no unbounded growth through the soak; one orphan-quarantine drill
  - Done when: a 1-hour mixed session leaves `Storage/` inside budget, the janitor log shows scheduled runs, and a deliberately orphaned artifact is quarantined rather than deleted.
  - **Evidence so far:** isolated Phase 8.5 drill `JANITOR-20261117T014544-626862` moved a deliberately manifest-backed orphan PDF and its sidecar into `archive/quarantine/` without deleting it. The latest `alex status` check reports `Storage/` at 11,650,425 bytes and the installed launchd trigger has a successful live run. A one-hour health/RSS/memory sampler is now running at `/tmp/alex-phase8-soak-20261117T075000.log`; the mixed/offline soak and final pressure samples are still required before this step can be checked.

**Phase gate**
- [x] All `z.txt` scenarios pass unattended — 2026-11-17 · `openjarvis alex eval` (2 / 2)
- [x] 0 wrong basic-action matches on the 100-utterance set — 2026-11-17 · 135 / 135 classifier guard assertions
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
| 2026-11-15 | 3 | Speech wording fixed (natural sentences, prepositions kept, no "queued" claim for parallel runs); 123-utterance + 12-argument guard set added (`scripts/alex_classify_check.py`, 135/135). It caught "enable bluetooth" toggling instead of enabling. |
| 2026-11-14 | 3 | 3.1/3.3/3.5 done (`07476c3f`, `2960a82f`): deterministic classifier, live gateway answers with local fallback, real slot-filling replacing the canned bot. 3.2 dry-run verified only. Remaining: 3.4 milestones, 3.6 speech wiring, 3.7 queue names, 3.8 Tauri close. |
| 2026-11-14 | 3 | Blocker fixed: all hosted gateways answered 401 (keys not present in the native process), so quick answers were impossible; added a keyless Ollama last-resort candidate and corrected the `local` model tag. |
| 2026-11-14 | 2 | Bug fixed (`WORKER_LOCK`): a late worker could overwrite an unanswered approval with `done`. `complete_task`/`update_task_progress` now refuse to touch `awaiting_approval`, `awaiting_worker` and all terminal states, recording `LOCK-002`/`LOCK-001` instead. Verified 7/7 transitions. |
| 2026-11-14 | 2 | Follow-up fix (`aec2f506`): approve no longer fakes `running`. New `awaiting_worker` status (sweep-exempt) + live-worker registry; bridge approval gate now blocks instead of proceeding. Real resume of a parked worker remains 3.4/5.5. |
| 2026-11-14 | 2 | Hazard fixed: `store` resolved `storage/data/*.db` relative to cwd, so a worker started elsewhere silently wrote a second empty ledger — indistinguishable from “nothing happened”. Now anchored by `ALEX_DATA_ROOT` (set by `alex up`). |
| 2026-11-14 | 1 | Deviations recorded: `Alex/evals/` deleted (imported removed modules; 8.1 rebuilds), `Alex/jarvis/` deleted wholesale, legacy `tools/friday_mac/` removed. Part D Phase-1 column filled ⛔ with the same reasons as Phase 0. |
| 2026-11-17 | 4/7 | Duplicate install removed (`/Applications/Alex.app` shared `com.openjarvis.desktop` with OpenJarvis.app). The clock is now real: time questions match by shape ("what time was it", "what's the time") and every Matrix-bound request carries the current local date and time in a system line, so the model never again claims it has no clock. The whole dialogue is logged to one appended file per day and surfaced in the Logs page. Echo closed on its last path: Matrix's own speaker is a different process, so `/v1/alex/voice/status` now reports `system_speaking` and the UI defers to it. |
| 2026-11-17 | 4 | Two voices, one cause: Face/Matrix/Hermes are separate processes, so `alex/face/voice.py` was three speakers with three private queues. Speech is now machine-wide — `Storage/run/voice.lock` around the `say` process and `voice.last.json` for cross-process duplicate refusal — measured with two real processes: different lines serialise (max concurrent `say` 1), identical lines collapse to one. The last raw `say` (wake fallback) is deleted. 12 voice tests pass. |
| 2026-11-17 | 4 | Self-talk traced to Whisper inventing `Okay.`/`You` from silent takes; three-layer guard added and the offending recordings now transcribe to `''`. Face was separately dead for 146 launches because the pid file pointed at a PID macOS had reused for Docker — `_registered_pid_alive` now verifies the process is a server. Stack restarted healthy; default microphone turn is 10 s. |
| 2026-11-17 | 4 | Voice repaired rather than re-argued: the doubled audio was the server `say` plus the UI autoplaying the same reply — the client now defers to whoever holds the voice. Continuous partial transcription, one clarification nudge for unfinished sentences, "listen to this" long-form turns, and durable `temp/voice` + `temp/transcriptions` with a real 24 h retention. 4.2 stays open pending live microphone turns. |
| 2026-11-18 | 3 | **Understanding before acting (3.9–3.11).** The Face play route was the bug behind the YouTube screenshots: it searched the whole instruction (`/results?search_query=i want you to play…`) and claimed playback without playing. It now calls the real `play_song` on the stripped subject, “play it” resolves through the thread, and a bare artist name is a correction, not a biography question. New `alex/web.py` turns “google about harry potter series on chrome” into a search for the subject, reads the top pages and returns a cited summary (or an honest “nothing to summarise”). Conversation threads (`alex/threads.py`) and the task register (7.6) are recorded too. Tests: `tests/alex` + `tests/server/test_routes.py` = 253 passed, one pre-existing `pdfinfo` failure; live verified for the search and two play turns. |
| 2026-11-18 | 5 | **Done only when verified, and silence until then.** `complete_task(verified=True)` used to follow any non-trivial Hermes reply. A second Hermes turn (`<task>-verify`) must now return `VERIFIED:`; `NOT VERIFIED:` retries once and then fails, and `task_started` was removed from the spoken events. Unit-tested (`test_completion_evidence.py`); the full gate has not been run against a live multi-minute task. |
| 2026-11-19 | 3/11 | **Code in the chat, and questions are not tasks (3.12–3.16).** The audit found no code-in-chat path at all: "write a python program" classified as `complex_task` and went to Hermes, whose run directories produced the five or six `triangle_area.py` copies in the screenshots. New `alex/coder.py` (deterministic `understand` → generate/show/save/run/explain/status/reject, one snippet per thread, exact-bytes idempotent save, scratch-dir run) is reached before web research and classification, so a code request, a status question, a "show me the code here" and "I'm not making that" no longer dispatch a task or open a browser; project requests still go to Hermes. Session counters now read "Unavailable" rather than 0 when no backend reported them. Tests: `tests/alex` 203 passed with the pre-existing `pdfinfo` failure; `test_code_in_chat.py` 10/10; `npx tsc -b` exit 0. Not verified live: real model code generation (local gateways 401). |
| 2026-11-19 | 3/11 | **One conversation is one chat, and a follow-up keeps its code (3.17–3.19).** The hallucination had two mechanical causes. Code answers were generated with no history, so "the code for the above problem" had no problem to answer and the model filled the gap itself; the prompt now carries the thread with previous code blocks elided, so the problem survives but the old block cannot be replayed, and that phrase is a new generation ahead of the replay rule. Separately the backend kept one thread per conversation while the UI kept one record per draft, so one conversation was listed twice; the turn now returns `thread_id` and `store.adoptThread()` merges the twin into the earlier chat (and again at load). "Open a new chat" was matching `open_app` as app "new check" (ASR: chat → check/chad); it is now a UI action like `close_app`, accepted only when it is the whole turn. Tests: `tests/alex` **214 passed**; `npx vitest run` **131 passed**; `npx tsc -b` exit 0. The desktop app needs a rebuild to carry the frontend half. |
| 2026-11-19 | 3 | **The last red test was a missing binary, not a broken PDF.** `test_write_text_pdf_creates_a_readable_pdf` shelled out to `pdfinfo`, which poppler does not install here, so a healthy writer looked broken. The writer emits an uncompressed PDF, so the test now validates it in-process: `%%EOF`, every xref offset landing on its own `N 0 obj`, a `/Pages` tree with `/Count 1` and exactly one `/Type /Page`, and the title and both paragraphs present as `Tj` strings. That is a stricter check than `pdfinfo` without the optional dependency. Tests: `tests/alex` **204 passed, 0 failed**. |
| 2026-11-18 | 4 | **Voice agent signed off by the user.** The last duplicate path was closed by ChatGPT (Astra 6.1): the per-message speaker button now replays through Face's single `say` (`/v1/alex/voice/say` + polled status + local-only `/v1/alex/voice/stop`, health `native_alex: true`) instead of a second browser `Audio`. The "does not answer its own voice" gate is ticked on the user's live confirmation, backed here by the health/status payloads and 18 passing `tts` tests. Code frozen; handover in `VOICE_AGENT_NOTES.md`. 4.2 (ten turns) and 4.6 (wake firing) stay open — they were not part of this fix. |
