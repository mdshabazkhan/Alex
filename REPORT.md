# Alex merge — progress report

## Voice overlap repair — 2026-11-18

- Alex now has one native speech path, using **Samantha**. The browser audio fallback cannot start while Alex voice detection is pending or unavailable, so it cannot overlap native speech.
- Repeated speaker presses for the same message are ignored. Stop waits for any in-flight native stop before another message starts, and a queued line is cancelled even if it is waiting for the shared system voice lock.
- Verification: frontend voice suite **18 / 18**, full frontend suite **128 / 128**, and Alex/server suite **250 / 250** passed. A live concurrent playback probe accepted one of two simultaneous requests, observed one `say` process using Samantha, and left no active or queued speech after Stop. Physical-speaker listening was confirmed by the user afterward.

_Last updated: 2026-11-17. Read this top box first._

**Resume:** [jump to Resume](#resume-here). Phase 7 implementation and its three phase gates now pass. Phase 8 evaluation and operating documentation now pass; continue with the remaining Phase 3–6 acceptance items, live Hermes evidence, and the remaining Phase 8 install/soak/storage checks. Source and document changes remain in the shared, uncommitted worktrees.

---

## Status at a glance

| Phase | Progress | State | Last commit |
|---|---|---|---|
| 0 Freeze & baseline | 4 / 4 | **Done** | `084274eb` |
| 1 One repo, one app | 8 / 8 | **Done** | `05b06464` |
| 2 Ledger truth | 7 / 7 | **Done** (+3 bug fixes) | `1406106a`, `aec2f506`, `d9e5e9b9` |
| 3 Face ↔ Trinity wiring | 7 / 8 | **In progress** | `6e7f3a56` |
| 4 Voice + human delivery | 5 / 10 | **In progress** (4.2/4.6 built, not yet observed live) | `40b96cf5` |
| 5 Hermes becomes real | 7 / 8 | **In progress** | 2026-11-17 |
| 6 Memory: short-term ⇄ long-term | 14 / 14 | **In progress** (phase gate pending) | working tree (uncommitted) |
| 7 Logs, dashboard & report | 5 / 5 | **In progress** (Part D acceptance pending) | working tree (uncommitted) |
| 8 Hardening & acceptance | 2 / 5 | **In progress** | working tree (uncommitted) |

Work tree: shared in-progress changes are uncommitted; existing user changes are preserved.
Services: Face `:8000`, Matrix `:8700`, Hermes `:8642` — all `/health` green.

### Current verification addendum — 2026-11-17 (resume)

- While checking the remaining Bluetooth acceptance, the live `/opt/homebrew/bin/blueutil` command hung even though `system_profiler SPBluetoothDataType` could see the BCM_4387 controller (State: Off). The Face actuator now bounds every blueutil call to eight seconds and returns an explicit unverified timeout instead of blocking the request; the new regression test passes. This is a safety fix, not acceptance evidence: 3.2 still needs a successful real toggle, recorded Face task, and spoken confirmation.
- Network checkpoint recovery now has a real API path: `POST /api/tasks/{task_id}/resume` checks connectivity, leaves paused tasks untouched while offline, records `NETWORK-RESUME-001`, and requeues the original request when online. The live Wi-Fi-off/pause/on/resume sequence is recorded below; 5.7 is now checked.
- The live network/offline acceptance is now observed: `T-20261117-C8B794` paused at step 1 while Wi-Fi was off, resumed after Wi-Fi restoration through `NETWORK-RESUME-001`, and advanced to step 2 with one intake and no repeated external effect. `T-20261117-1988C1` ran with Wi-Fi off through the Ollama-only `profile=offline` route using installed `qwen3:4b-16k` and completed with evidence `7`; the hosted 429 path was not touched. Step 5.7 and the Phase 5 Wi-Fi gate are checked. The resumed web task was deliberately stopped before a long provider run, so this is checkpoint/resume evidence, not proof of a successful external research/mail provider.

- The active verification paths are the checklist/report in `/Users/mdshabazkhan/Documents/dependencies/Alex`, the merged implementation in `~/.openjarvis/src`, and the live Face/Matrix/Hermes services plus canonical `Storage/` root. This is the source of truth for the remaining work; legacy files under the original Alex tree are not used by the running app.
- Phase 6 gate evidence was refreshed: the live memory-about/prefetch endpoints resolved “mail Max” to the stored `max123@gmail.com` address without a prompt; the Dupont/Croda run reused Dupont's preserved procedure; the Phase 6.13 restore matched both an experience and its PDF byte-for-byte; and the live persona sequence matched the exact greeting/sign-off script. Those four gate boxes are now checked in `CHECKLIST.md`. The historical-date query remains open because no real two-month-old task/artifact evidence has been fabricated.
- Offline execution was hardened: the worker now uses the installed Ollama tag `qwen3:4b-16k`, and the Ollama gateway sends `think: false` for Qwen3. The regression tests cover both the tag and payload. Live Qwen3 probing still occasionally stalls in the local runner, so this is verified as a safe fallback/configuration fix, not counted as Hermes' three-tool completion proof.
- Hermes' plugin workspace bridge now uses Hermes' session-scoped cwd (`session_cwd`) and falls back to `ALEX_RUN_WORKSPACE` only for direct child execution. The Matrix pre-tool endpoint merges that workspace into policy evaluation, so relative file operations are evaluated inside the task workspace while absolute outside paths still require approval.
- The real file/search Hermes run `run_2dba8692` remains valid (write/read artifact, tool steps, SHA-256). The newer live three-tool proofs close 5.1 and 5.4: `run_b4126aa5` independently executed terminal, file, and search in an isolated workspace, and normal Matrix task `T-20261117-AE2B0E` repeated the proof with artifact `/Users/mdshabazkhan/Documents/dependencies/Storage/Artifacts/hermes/runs/run_d6634396/matrix_step_proof.txt`, exact content `MATRIX_LIVE_STEP_PROOF`, and real `STEP 1/3`–`STEP 3/3` progress events. Steps 5.3, 5.6 and 5.7 are now closed by the policy/prefetch, idempotency, and live network/offline drills below; 5.8 remains open for mail/Sent-folder acceptance; 5.5 is closed by the live steering task below.
- Phase 8.5 scheduling is installed at `~/Library/LaunchAgents/com.openjarvis.alex-janitor.plist` for daily idle-only execution. A launchd contention reproduced a SQLite open stall; the trigger now calls `/api/storage/janitor` inside the Matrix process, avoiding the background agent's direct Documents-backed SQLite access. A live launchd kickstart exited 0 and wrote a real apply JSON result plus janitor ledger event. The one-hour memory/storage soak remains open; the isolated orphan-quarantine drill is recorded below.
- Latest live check after the restart: Face, Matrix, and Hermes all returned healthy; `alex status` reported `Storage/` at **11,650,425 bytes**; the latest durable janitor event remains `JANITOR-20261117T014716-a1a44e` with zero deletions/quarantines and both SQLite stores vacuumed.
- During the Phase 5.3/5.6 continuation, macOS began blocking directory-open calls under `Documents/` (plain `ls` and SQLite WAL commits hung while `stat`/known-file reads still worked). Matrix was stopped before data loss; the current `ledger.db` and `knowledge.db` were copied, WAL-checkpointed in a temporary recovery directory, and the original ledger was replaced only with the consolidated copy (original files retained under `/tmp/alex-ledger-original-backup.xKwbI6`). Face, Matrix, and Hermes health are green again: Matrix reads the recovered canonical ledger and temporarily uses the exact current document-store snapshot at `/tmp/alex-live-clone.tK1O8b/mongodb/knowledge.db` so the blocked Documents directory cannot deadlock startup. No checklist evidence is being claimed from a fabricated external action.
- A desktop audio shutdown probe also caught Face blocked in CoreAudio's `AudioOutputUnitStop`; the process was terminated through its launch agent and relaunched successfully. All three health endpoints are green again (Face PID `1832`, Matrix `:8700`, Hermes `:8642`); the live 10-turn mic/wake gates remain open rather than being inferred from this recovery.
- Follow-up sampling traced the recurring CoreAudio wedge to the wake listener opening/closing PortAudio while the Tauri desktop was already active. The listener now checks desktop ownership before opening a stream and keeps an existing stream stable while the app is active; `tests/alex/test_wake_listener.py` covers the no-open contention case. After a fresh Face restart, a live offline Ollama task completed and all three health endpoints remained responsive.
- The gold-rate acceptance is now live rather than model-generated: after the Matrix restart, `POST /api/alex/chat` for “What is the gold rate today?” returned `$3,868.97` per troy ounce, “updated a few seconds ago,” with `Source: gold-api.com.` The dialogue path uses a bounded public live-price request and a second source fallback; no fixed price remains.
- The Bluetooth acceptance is now live: `turn off bluetooth` produced task `T-20261117-6C9A16`, returned `Bluetooth: Bluetooth disabled (verified)`, and recorded the same evidence on the Face `done` event. `system_profiler` observed State Off; Bluetooth was restored to On after the drill. The earlier blueutil hang remains covered by the timeout regression, but it did not recur during this verified run.
- Storage safety drill: isolated run `JANITOR-20261117T014544-626862` moved a manifest-backed orphan PDF plus sidecar into the timestamped `archive/quarantine/` tree and preserved both bytes. This closes the orphan-drill portion of 8.5; the one-hour mixed/offline soak and pressure samples remain open.
- Phase 4.7 is now verified in the frontend: `MicButton` renders server-backed Listening/Thinking/Speaking states, pulse/spinner feedback, and the silence countdown ring. Three render regressions pass and `npm run build` completes; live microphone/wake observations for 4.2 and 4.6 remain separate open gates.
- Voice delivery implementation coverage was strengthened without overstating live acceptance: sanitization/rate tests verify natural punctuation pauses, no spoken “comma”/URLs, intent-specific rates, and five non-identical human repair phrasings (**17 focused tests passed**). 4.8–4.10 remain open until the checklist's audible latency and microphone observations are measured.
- Conversational timing coverage now has a concrete ordering guard: the Matrix worker emits exactly one `task_started` acknowledgement before the connectivity/network probe, and the focused regression test verifies that ordering. The focused completion/handoff/voice suite passed (**8 tests**); this is implementation evidence only, so 4.9 remains open until live first-audio latency is measured below 300 ms.
- Hermes policy handling was tightened after a live probe showed a `DENY-003` response could be reported as a successful run. Safety-policy-blocked or unusable output is now classified as failed; the post-fix rerun `run_7a34f574` ended with `status=failed`, `Hermes returned a blocked or unusable result`, and no artifact. The new regression coverage passed in the focused Hermes suite.
- Phase 5.3 now has both acceptance halves: the canonical live three-tool proof recorded `pre_tool_call`/`post_tool_call` activity and ledger `PRE-ALLOW` steps, while the live `matrix-bridge` pre-LLM hook against a fresh clone of the current Matrix stores returned a provenance-bearing **241-token** brief (262 tokens including the instruction wrapper) instead of the **15,453-token** unfiltered 482-document retrieval index (**98.4% reduction**). The Max contact was supplied from memory without an invented value.
- Phase 5.6 is closed by a live side-effect-free idempotency drill on Matrix clone task `T-PHASE5-IDEMP-CLONE-20261117`: `email.send`, `file.move`, and `calendar.book` each returned `allow` once, `DUPLICATE-001` on the retry, and executed exactly once. The real mail/Sent-folder provider check remains a separate open 5.8/gate item.
- Live evidence steering now passes its acceptance branch: task `T-20261117-FFD526` had a first Hermes result of exactly `done` with no artifact, Matrix recorded `EVIDENCE-001` and exactly one `steer` event, then retried. The second attempt failed safely as unusable instead of being falsely completed; events `389`–`395` preserve the sequence. Step 5.5 is checked; the remaining Phase 5 boxes still need their distinct criteria.

### Phase 8 — evaluation and documentation (2026-11-17)

- `openjarvis alex eval` now runs the 135-case classifier guard set, both executable `z.txt` dialogue flows, then the complete Alex/server regression suite. The latest completed run reported **135 / 135**, **2 / 2**, and **162 passed** respectively. The suite includes gateway fallback, offline-only Ollama routing, checkpoint/resume, wake-listener mic contention, Bluetooth timeout handling, duplicate-send checks, Hermes policy/runtime regressions, and the Matrix janitor trigger route.
- The dialogue scenario found and corrected two input-handling bugs: a combined reply such as “100 words topic Diwali” now fills both slots, and “I need you to write … and send to Max” resolves Max rather than treating “write” as a recipient. Complex requests now hand off to Hermes through its `/v1/runs` API; Matrix polls the run, records its run ID/artifacts/token count, and only completes after evidence is returned.
- Added `docs/RUNBOOK.md` and `docs/CONFIG.md`, aligned with the existing blueprint. They document service ownership, start/stop/status, ports, health endpoints, backup/restore/janitor, canonical storage, provider environment configuration, and speech privacy. The running services were restarted after this change: Face, Matrix, and Hermes each answered `/health` successfully.
- Desktop packaging verification: `npm run tauri build` completed the TypeScript/Vite build, Rust release build, `OpenJarvis.app` bundle, and codesign verification (`valid on disk`, arm64 executable). The final DMG Finder/AppleScript layout helper hung in `bundle_dmg.sh` and was stopped after the signed `.app` was produced; 8.2 remains open for fresh-machine install/menu-bar observation.
- A non-destructive Phase 8 soak sampler is running at `/tmp/alex-phase8-soak-20261117T075000.log` for one hour. It records Face/Matrix/Hermes health, OpenJarvis/Chrome RSS, swap/compressor counters, and system free-memory percentage every minute; the first sample was healthy with **74% free memory**. This is in progress and is not yet counted as the 8.3/8.5 acceptance result.
- Phase 8 steps **8.1** and **8.4**, and its `z.txt`/classifier gate checks, are checked in `CHECKLIST.md`. Fresh-machine install, one-hour memory soak, and scheduled storage health remain open.

### Hermes execution audit — 2026-11-17

- Matrix now hands complex work to Hermes through `/v1/runs`, polls the run, records its run ID/artifacts/token count, and only accepts evidence-backed completion. The runtime itself runs in an isolated workspace and marks Hermes’ own “No reply” sentinel as **failed**, rather than reporting a false success.
- Live probes exposed and fixed two protocol defects: Matrix decoded upstream streams as JSON, and it returned JSON to Hermes even when Hermes requested OpenAI SSE. Matrix now requests complete JSON from providers, removes its internal `profile` routing field, then adapts the result to valid SSE with terminal `[DONE]` for Hermes. Direct live probing verified the SSE shape and indexed tool-call chunk.
- A real file/search Hermes run now succeeds: `run_2dba8692` created and reread `smoke_proof.txt`, with three tool calls recorded in `steps` and a verified SHA-256. The former 5.1 gap is closed by the newer three-tool proofs; `run_b799bb88` remains historical evidence of a no-reply attempt, not a current blocker.
- Regenerated the six-sheet report at [alex-report-2026-11-17.xlsx](storage/reports/alex-report-2026-11-17.xlsx): Summary 9 rows, Jobs 43, Steps 25, Costs 499, Bugs 3, Events 276; it reopened successfully.

### Phase 7 — Logs, dashboard & report (2026-11-17)

- Logs reads Matrix activity through Face and fetches the expanded task's full event history. UI verification at `:8000/logs` showed exactly 85 events dated today; expanding a row loaded its seven ledger events from the task-events endpoint. An event inserted directly into an isolated server ledger appeared through `/api/activity`; no browser write was involved. The live ledger had 85 events dated today, 164 from Nov 15 and 2 from Nov 16 before filtering.
- Clear confirms before deleting, checks Matrix's deleted/remaining counts, then re-queries. Isolated integration verification cleared tasks, events, steps, model calls, checkpoints and traces; reopening the database confirmed zero rows. Live production history was intentionally preserved. Service restart retained all 42 tasks, including five waiting on approval/worker handoff.
- Dashboard polls every two seconds and shows active task, step `n/N`, token total and latest/pinned gateway. A running fixture matched the ledger values `2/5`, `180`, and `friday-agent`. After reloading the services, the live recent-task API included both metric fields on all 42 returned tasks.
- `jarvis alex report` generated [alex-phase7-2026-11-17.xlsx](storage/reports/alex-phase7-2026-11-17.xlsx), which reopened successfully with six populated sheets: Summary (9 rows), Jobs (43), Steps (18), Costs (442), Bugs (3), Events (269). The CLI writes to the configured data root's reports folder.
- No-op verification: `Thanks` created no task or event. The local-day filter has a regression test that was observed failing before implementation and passing afterward.
- Verification: all `tests/alex` plus `tests/server/test_routes.py`: **162 passed** (473 existing pytest/FastAPI lifecycle deprecation warnings); full frontend suite: **124 passed** across 26 files; frontend TypeScript/Vite build passed; targeted Ruff and `git diff --check` passed. Existing frontend warnings remain: npm's unknown `strict-allow-scripts` setting and Vite's large bundle/ineffective analytics dynamic import.
- Face, Matrix and Hermes were restarted to load the new APIs and are healthy. The five approval/worker-waiting tasks persisted. Phase 7 steps and its three gates are checked in the checklist; the overall phase remains In progress until Part D acceptance is run.

---

## What actually works now

- **One app, one tree.** `openjarvis alex up|down|status` drives Face (through the
  `com.openjarvis.server` launch agent), Matrix and Hermes. `down` bootouts the agent, so
  "stopped" means nothing is listening.
- **The ledger is truthful.** Every state change writes an `events` row; steps are
  sequential from the ledger; `clear` returns counts and empties the tables; a heartbeat
  sweep fails dead runs instead of leaving them `running`.
- **Approval is honest, closed and owned by you.** Approve resumes an attached worker or
  parks the task as `awaiting_worker`; the sweep never fails parked tasks; the Hermes
  bridge *blocks* approve-required tools rather than running them; a late worker can no
  longer overwrite your decision (`LOCK-001`/`LOCK-002`).
- **Real conversation.** `classify.py` routes every turn deterministically (31/31 labelled
  utterances, including the false-positive traps). `dialogue.py` runs verified reflex
  actions, answers through the gateway, and slot-fills complex requests. The hardcoded
  essay, the "₹7,850" gold rate and "Understood, Master Khan" are gone.
- **Answers survive broken gateways.** Hosted gateways return 401 (no keys in the native
  process); the gateway falls back to local Ollama, so Alex still answers.
- **Alex talks only when it should.** `speech_policy.emit()` is the single writer: the five
  allowed moments, an unverified `task_done` suppressed, everything else silent. Every line is
  recorded as a `speech` event, so what Alex said is auditable, and served to the shell at
  `/api/speech/pending`.
- **Alex actually says the line, and knows it said it.** `emit()` speaks through the one voice path and
  tells the mic session what was said, so a transcript of Alex's own voice is dropped as an echo while a
  real interruption survives.
- **Gemini's server rewrite was mostly destructive.** `routes.py` lost 214 lines of the live chat
  handler into unreachable code inside `toggle_mic_recording`, killing the shutdown/time reflexes,
  memory injection and agent dispatch; it also re-implemented stopwords and echo matching inside
  `/v1/speech/mic/stop`. Restored the handler, forwarded `alex` metadata, and deleted the duplicate
  logic — see 4.4. The new `macos_say` backend is kept but is a fallback, not the default.
- **Frontend drives the mic; wake word lives in the server.** `useSpeech`/`MicButton` call
  `/v1/alex/listening/*` on the Face, and `alex/face/wake.py` is started and stopped with the server;
  the standalone wake daemon is deleted. Both paths verified over HTTP — the live 10-turn mic test and a
  real wake-phrase trigger still need the app and a microphone.
- **One speaker.** `alex/face/voice.py` is the only thing that plays audio: a single queue, one
  line at a time, and a barge-in that terminates the current line and drops what was waiting. The
  four previous `say` call sites delegate to it, so two replies can no longer talk over each other.
- **One microphone state machine.** `alex/face/listening.py` owns the cycle — 5 s silence, "alex
  reply" to submit, "listen" to barge in, echo suppression at 0.45 similarity — and exposes it at
  `/v1/alex/listening/*`, so the browser can no longer disagree with the server. Tested with an
  injected clock: 27/27, and verified live over HTTP.
- **Two tasks at once, and you can tell them apart.** Every update names its task in a sentence
  someone would actually say ("On it — short note about solar power.", "Done — PDF of my resume."),
  long runs emit discrete milestones without speaking them, and a second concurrent request is
  reported as running alongside the first rather than falsely as "queued".

## Bugs found and fixed so far

| # | Bug | Impact if left |
|---|---|---|
| 1 | `store` resolved DB paths from the process cwd | a worker launched elsewhere silently wrote an empty second ledger |
| 2 | Indented `from matrix.…` imports survived the rewrite | bridge fails closed → **every** Hermes tool call silently blocked |
| 3 | `hermes/__init__.py` exported the `bridge` instance, shadowing the subpackage | `import …bridge.matrix_bridge` broke |
| 4 | Approve-required tools ran without approval | an email could send before you answered |
| 5 | Approve wrote `running` with no worker attached | approved tasks later "failed" for being idle |
| 6 | **A late worker could overwrite an unanswered approval with `done`** | work completed behind your back; your decision ignored |
| 7 | All hosted gateways 401, no local fallback | Alex could not answer anything |
| 8 | `local` profile named `qwen3-4b-64k` (not a real Ollama tag) | offline answers always failed |
| 9 | `dialogue.py` duplicated the deliverable list, missing "note" | asked for a deliverable the user had already named |

---

## New: the memory architecture (plan extension, 2026-11-15)

Your two-layer model is designed in `docs/BLUEPRINT.md` **§A7** and tracked as **Phase 6 (14 steps)**.
The implementation status below is current as of 2026-11-17.

**The split**

| Layer | Store | Answers | Budget |
|---|---|---|---|
| Short-term | `Storage/mongodb/knowledge.db` — mongo-style document store | who/what/where, preferences, "have we done this", where the code lives | < 20 ms, no model call |
| Long-term | `Storage/sql/ledger.db` + `Storage/Artifacts/` | what happened, when, in what order, with evidence and code | 50–200 ms |
| Curated | `Storage/knowledge/` — OKF markdown bundle | stable facts written once, read directly | a file read |

**Retrieval** is a hybrid, because your data is deliberately scattered: rule router → BM25 (FTS5) +
local embeddings (`nomic-embed-text`) + one-hop graph over real links → RRF fusion → recency/importance
rerank → ≤1,200-token brief with provenance on every claim.

**The Dupont/Croda loop** is written out step by step in §A7; the rule that makes it real is that a task
is not "done" until its experience is written and linked to its ledger task and artifacts.

**Storage root** `/Users/mdshabazkhan/Documents/dependencies/Storage` exists and is organised so you can open
it by hand:

```
Artifacts/{images,videos,texts,word_files,ppts,pdfs,code}   durable — kept until you delete it
temp/{temp_code,voice,logs,cache,scratch}                   disposable — swept daily
sql/ledger.db    long-term truth      mongodb/knowledge.db   short-term recall
knowledge/       OKF bundle           backups/  archive/    safety and cold storage
```

The one rule that places every file: **the answer** goes to `Artifacts/<type>/`; **a step towards the
answer** goes to `temp/`; **a fact** goes to `knowledge/` or `mongodb/`; **the record of what happened**
goes to `sql/`. "Make a PDF on X" therefore runs `temp/temp_code/<ts>_create_pdf.py` and files
`Artifacts/pdfs/<ts>_x.pdf` — the script is throwaway, the PDF is not.

Each top folder has its own `index.md`, and the root `index.md` states the layout, the naming convention
(`<timestamp>_<what>.<ext>`) and the daily sweep policy.

**Decisions you should know about**

- **`mongodb/` holds an embedded document store, not a `mongod` daemon.** `knowledge.db` is one SQLite file
  exposing a mongo-style API (`find`, dotted paths, indexes). Phase 1 removed every container; a fourth
  daemon would add a port, ~200 MB of RSS (against a 16 GB soak target) and a backup surface for no benefit
  at this data size. Swapping in real MongoDB later touches one class — say the word and I'll do it.
- **`sql/` is SQLite, not Postgres.** Same reasoning; `pgvector` is the documented swap if the corpus ever
  reaches millions of rows.
- **No vector database.** Thousands of rows, not millions: SQLite + numpy cosine is faster than a service.
- **`memory.db` retires** — its contacts/knowledge/pitfalls migrate into `knowledge.db` in 6.1.
- **The janitor is conservative by default:** `--dry-run` first, never deletes anything referenced by a
  task/experience/concept, and every run is logged.

---

## Known gaps (deliberate, tracked in CHECKLIST)

| Gap | Why | Where |
|---|---|---|
| 3.2 real hardware action not executed | toggling Bluetooth/Wi-Fi while you sleep changes your machine | you: ask "turn off bluetooth" |
| Approve does not wake a parked worker | no worker waits at the gate yet | 3.4 / 5.5 |
| 3.8 window did not actually close | built and compiled, but needs the desktop app running | you: say goodbye in the app |
| "Gold rate today" is model knowledge, not a live rate | `quick_answer` has no browsing | Phase 5 (Hermes/browser) |
| Approval-required tools are blocked, not paused | fail-closed until parking exists | 5.5 |
| UI does not render `evidence` or call real clear | Logs page rewrite | 7.1 / 7.2 |
| Mic not yet wired into the UI | 4.1 proved the rules and the API, not a live microphone | 4.2 |
| Browser speech fallback not wired | 4.3 removed the duplicates; the fallback is 4.2's job | 4.2 |
| Memory system designed, not built | Phase 6, after the voice pipeline | Phase 6 |

---

## Verification performed (commands actually run)

- Phase 0 — one `:8000` owner; 10/10 DB backups `integrity_check = ok`; port map; blueprint commit.
- Phase 1 — import from `/tmp`; 24 routes; 10 registry tools + MCP server returns the same 10;
  `alex down` → no listeners; `up` → 3/3 healthy; wheel contains 22 `alex/` entries; grep clean.
- Phase 2 — clear `21 tasks / 61 model_calls` → 0 rows; 7 event types; steps 1..5; approve/reject/
  stop/steer with rule IDs; Doctor row `rate_limit` ×2; `TIMEOUT-001` sweep.
- Approval fixes — no worker → `awaiting_worker` survives `sweep(0)`; worker → `running`;
  `mail.send` → blocked + `awaiting_approval`; finished task → 409; 7/7 lock assertions.
- Phase 3 — 31/31 utterances; spy fallback proves no model call on rule hits; live `/api/alex/chat`
  answers via Ollama (`tokens_in=51, tokens_out=128`); slot question → task `T-20261115-29EC00`.
- Phase 3 (speech) — two concurrent tasks: speech moments exactly `{task_started, task_done}`,
  3 milestones each, every line task-named and distinct; `/api/speech/pending` returned 3 with
  `next_after_id=97`; live concurrency check `parallel=false` then `parallel=true`
  ("Starting that alongside the other one"); SSE for "goodbye alex" carried
  `alex.action=close_app`; `cargo check` and `tsc` both exit 0.
- Classifier guard set — `scripts/alex_classify_check.py`: **135/135** (123 utterances: 39 reflex,
  44 quick, 40 complex; plus 12 argument checks), exit 0.
- Mic state machine — `scripts/alex_listening_check.py`: **27/27**, exit 0, including "silence alone
  never submits", "each voice frame restarts the countdown", "alex reply submits and is stripped",
  "listen is a barge-in not an echo", and "an old spoken line stops suppressing after 20 s".
- Voice path — `scripts/alex_voice_check.py`: **11/11**, exit 0 (queue never overlaps, barge-in
  silences and drops the queue, exactly one `say` call site); live `/v1/alex/voice/say` and
  `/api/alex/stop_speaking` both behave.
- Storage tree — created and listed (11 directories, 2 OKF indexes, 239 GiB free).

## Not verified (be sceptical here)

- **No real macOS action executed** (dry-run only) — Bluetooth/Wi-Fi/volume paths are unproven on hardware.
- **No microphone, speaker or Tauri window touched** — Phase 4 is entirely unstarted.
- **No real Hermes run** — the worker is still Matrix's built-in path, not `hermes-agent`.
- **No frontend change** — the Logs page still reads client state only; `evidence` is API-only.
- **No memory code exists yet** — Phase 6 is a design, not a working store.

---

## Resume here

1. `openjarvis alex status` → expect three healthy lines. If not: `openjarvis alex up`.
2. `cd ~/.openjarvis/src && git log --oneline -5` → confirm the blueprint commit with §A7.
3. Close **3.8** by saying goodbye in the running desktop app (the command and the stream metadata
   are in place and compiled), and **3.2** by asking "turn off bluetooth" once. Then take the Phase 3
   gate audit at the end of Phase 3 in `CHECKLIST.md`: four items are blocked on Phase 5 (real Hermes,
   live web answers) and on the ≥100-utterance guard set, not on wiring.
4. Ask **"turn off bluetooth"** to close 3.2 on real hardware.
5. **Phase 4 status:** 4.1, 4.3 and 4.5 are done. Next is **4.2** — the frontend must drive
   `/v1/alex/listening/*` and keep the mic live for 10 consecutive turns. That needs the desktop app
   running with a microphone, so it cannot be verified headlessly; do it at the machine, then tick it.
   After that: 4.4 (stopwords in the UI), 4.6 (wake word into the server), 4.7 (visual state), 4.8–4.10
   (human delivery). Then **Phase 6** (memory) — 6.1→6.14 in order.
6. Tick `CHECKLIST.md` only when each "Done when" holds; append date + commit. Update this report at
   every phase boundary.

---

# Phase 5 — Hermes becomes real (route re-done 2026-11-16)

## Where the checklist actually stands
`CHECKLIST.md` leaves 5.1 open because its completion criterion requires one run using at least three
distinct toolsets and returning artifacts. The real runtime and file/search hooks are proven, but the
three-toolset run `run_b799bb88` failed with Hermes' no-reply sentinel before producing an artifact.
The Phase 5 gate now records the independently verified file artifact and tool-step ledger.

## What was wrong (verified by inspection and by live probes)
1. **The daemon was a stub.** `~/.openjarvis/src/src/openjarvis/alex/hermes/runtime.py` fabricated
   a run: it called `bridge.pre_tool_call("web.search", …)` against a fake query and returned
   `"Hermes completed execution for: <prompt>"` without any model call. `:8642/health` said
   "operational" the whole time. Replaced with a runtime that drives the installed
   `hermes chat`/`hermes -z` CLI out of process, one workspace per run under
   `Storage/Artifacts/hermes/runs/<run_id>/`, and records `api_calls`, `total_tokens`,
   `output`, `stderr` and the artifact list. New `GET /v1/runs/{id}` for polling.
2. **In-process import is impossible.** Importing `run_agent.AIAgent` into the Alex venv triggers
   Hermes' bootstrap, which re-execs the process with `sys.path` pointing at `~/.hermes/hermes-agent`
   and kills the server (`ModuleNotFoundError: openjarvis`). Hence the out-of-process CLI.
3. **Alex's dialogue layer was eating Hermes' traffic.** `alex/matrix/api.py` computed
   `is_internal` with `all(not (system mentions "hermes"))`, i.e. exactly backwards: requests whose
   system prompt names Hermes got routed into `handle_utterance`, which answered with the canned
   clarify strings in `alex/dialogue.py:60,63` ("What should it be about?",
   "What email address should I use for {recipient}?"). Every "Hermes" answer to date was one of
   those two strings. Now: a request is internal when it carries `tools` (an agent loop) or a
   Hermes-identity system prompt; only Alex's own voice/desktop turns reach the dialogue layer.
   After this fix `hermes -z "What is 2+2?…"` answers `4` from a real model.
4. **The gateway could not carry a local model.** Two defects in `alex/matrix/gateway.py`:
   a 45 s httpx timeout against a model that needs minutes (now 600 s for `ollama`, 45 s for cloud),
   and no completion budget floor, so `qwen3:4b` spent the whole `max_tokens` on its reasoning block
   and returned empty `content` (now floors `max_tokens` at 1024 for `ollama`). Ollama's default
   4096-token context also truncated the agent prompt, so `qwen3:4b-16k` was created from the same
   weights with `PARAMETER num_ctx 16384` and is the `ollama` route in `config/profiles.yaml`.

## Evidence collected
- `GET :8642/health` → `{"agent":"hermes-agent","runtime":"/Users/mdshabazkhan/.local/bin/hermes",
  "toolsets":["terminal","file","search","web"]}`.
- `hermes -z "What is 2+2?…"` → `4`; `--usage-file` reports `api_calls: 1`,
  `model: friday-agent`, `provider: custom`, `completed: true`.
- `POST :8700/v1/chat/completions` with a `write_file` tool schema → a real
  `tool_calls` entry (`write_file {"path":"hello.txt","content":"hi"}`) in ~8 s.
- No completed run yet: the three dispatched runs either hit the 1020 s subprocess cap or were
  killed by a service restart. `Storage/Artifacts/hermes/runs/run_c6e60a25/` holds no `plan.md`.

## Blocker to close 5.1
There is **no cloud model credential on this machine** — `~/.openjarvis/src/.env` defines no
`*_API_KEY`, and the gateway chain `freellmapi → groq → openrouter` therefore always falls through
to local `qwen3:4b-16k`. That 4B model needs several minutes per agent turn through Hermes' system
prompt, so a three-toolset task does not finish inside the run budget. Two ways forward:
add one provider key (Groq's free tier carries `llama-3.3-70b-versatile`, already first in the
`agent` chain at `config/profiles.yaml`), or raise `ALEX_HERMES_RUN_BUDGET` and accept a ~20 min
local run. Until one of those exists, 5.1 stays unticked and 5.2–5.8 stay untouched.

## Changes are in this working tree, not committed
`~/.openjarvis/src`: `src/openjarvis/alex/hermes/runtime.py` (rewritten),
`src/openjarvis/alex/matrix/api.py` (`is_internal`), `src/openjarvis/alex/matrix/gateway.py`
(timeout, token floor, local model from config), `config/profiles.yaml` (`ollama.model`).
Local model store gained `qwen3:4b-16k` (`ollama rm qwen3:4b-16k` reverts it).

### Addendum (same session): a fifth defect, found after the runs kept "running" forever
`subprocess.run(..., capture_output=True)` waits for the pipe to reach EOF. Hermes leaves child
processes that inherit stdout and outlive the agent, so `communicate()` never returned: the child
was already gone (`ps` showed no `hermes -z`), the run still reported `running`, and on the 1020 s
cap the partial output was thrown away — which is why every dispatched run looked like a silent
timeout. The runtime now redirects the child to `<workspace>/run.log` (a file always closes) and
keeps the last 8 KB as `output`, so a timed-out run is diagnosable. Runs dispatched before this fix:
`run_19c1de9f`, `run_c1245c7f`, `run_c6e60a25` (all `failed`/`running`, no artifacts);
`run_294c1689` after it, still inconclusive at the time of writing.

## Runs that hung at `running` with an empty `run.log` — fixed (2026-11-16)

The suspected cause (post_tool_call blocking on the SQLite ledger) was **not** it. Four real
defects, each verified after the fix:

1. **The ledger path followed the process working directory.**
   `matrix/store.py` had `_DATA_ROOT = os.environ.get("ALEX_DATA_ROOT") or os.getcwd()`, directly
   under a comment claiming the opposite. The Hermes daemon runs with the user's project as its
   cwd (`/Users/mdshabazkhan/Documents/dependencies/Alex`), so it wrote steps and model calls to
   `Alex/storage/data/ledger.db` while Matrix wrote `~/.openjarvis/src/storage/data/ledger.db` —
   two ledgers, one of them invisible. The root now comes from the package location
   (`parents[4]` when it holds `config/`, else `~/.openjarvis/src`); verified identical from both
   working directories.
2. **Agent children outlived the daemon and shared its process group.** `os.getpgid(child)` returned
   the *daemon's* group, so one orphan sat for 52 minutes holding the only local model and the next
   run queued behind it. Children now start with `start_new_session=True`, `/stop` and the 1200 s
   budget kill the whole group (`SIGTERM`, then `SIGKILL`), the `lifespan` shutdown kills every
   in-flight group, and startup reaps orphans matched by `Storage/Artifacts/hermes/runs` + the
   hermes binary. Verified: child pgid == its own pid, `/stop` → child exit `-15`, run `stopped`
   with `finished_at`, no orphan, `active: 0`.
3. **Candidate failures were invisible.** `api.py` returned `HTTPException(500, detail=str(e))` and
   `str(httpx.ReadTimeout())` is empty, so every gateway failure reached Hermes as a bodyless 500.
   The detail now names the type, and the gateway prints one line per failed candidate. That is how
   the real blocker became visible: `groq 401`, `openrouter 401`, `freellmapi 401` on every call.
4. **No progress visibility while a run was in flight.** Output went to a pipe; `-z` is quiet. Each
   run now writes `<workspace>/run.log` and `GET /v1/runs/{id}` returns a `log_tail`.

## Why 5.1 still cannot be ticked

- `groq`, `openrouter` and `freellmapi` all answer **401 Unauthorized**: no provider key exists on
  this machine, so the `agent` chain always ends at `ollama:qwen3:4b-16k`.
- Local measurements: `hermes -z "What is 2+2?…" -t file` answers in under a minute, but
  `hermes -z "Create hello.txt containing the word hi." -t file` did **not** finish in 280 s
  (no `hello.txt`, no `usage.json`), and a Hermes-sized payload (26.6 KB, 24 tools) at 16k context
  returns HTTP 200 with `content: ""` — qwen3 spends its whole completion budget reasoning.
- A three-toolset task therefore cannot complete on this machine today. Closing 5.1 needs one
  provider key (Groq's free `llama-3.3-70b-versatile` is already first in the `agent` chain) — after
  that, the same POST to `/v1/runs` is the whole proof.

## Runtime review and the ledger cleanup (2026-11-16)

`~/.openjarvis/src` @ `0e805f91`.

- **Runtime simplified** (`hermes/runtime.py`): one `runs` dict instead of `runs` + `run_procs` (each
  entry carries its `pid`), one `TOOLSET_FOR_TOOL` table instead of the hand-rolled config walk, the
  150-line static dashboard replaced by a compact page listing live runs, and a failed ledger write
  now prints instead of being swallowed. Behaviour re-verified: `POST /v1/runs` → `running` with a
  pid; `/stop` → `stopped`, `hermes exited with code -15`, `finished_at` set; `/` renders 200.
- **One data root.** `paths.data_root()` is now the only rule: `$ALEX_DATA_ROOT`, then
  `config.toml [alex].data_root`, then `~/.openjarvis`. `store.py`, `dialogue.py` and `reports.py`
  used to carry their own `env or os.getcwd()` copies (and `reports` was a bare relative path), so
  the launchd-started Face process and any ad-hoc script could write a different ledger than Matrix.
  Verified from `/tmp` with the env unset: ledger, memory, reports and workspace all resolve into
  `Alex/storage/`.
- **Which ledger was stray — not the one it looked like.** `Alex/storage/data/ledger.db` holds the
  real history (28 tasks, 167 events, 184 model calls) and stays. The accidental copy was
  `~/.openjarvis/src/storage/` (96 KB, one `model_calls` row from a 03:09 inline probe, no tasks);
  with no open handles and every path now resolving to Alex, it was removed and did not reappear
  after a full `jarvis alex down/up`.
- **Guards:** classify 135/135, human-delivery 38/38, voice 11/11 (the first voice run gave 8/11
  under load and the rerun 11/11 — it asserts speech-queue timings, so treat a lone miss as a flake).
- Phase 5 status unchanged: **5.1 still unticked**, same blocker (no provider key; local 4B model
  cannot finish a tool-using run).

## Verification refresh — 2026-11-16

- Corrected the Phase 4 progress row in `CHECKLIST.md`: 4.1, 4.3, 4.4, and 4.5 are checked, so it is
  **4 / 10**, not 3 / 10. The remaining 4.2 and 4.6 acceptance criteria require a live microphone;
  4.7 requires a live desktop observation; 4.8–4.10 require audible confirmation despite their
  automated checks.
- Re-ran the focused checks: listening **32 / 32**, voice **11 / 11**, human delivery **38 / 38**,
  and classifier guard set **135 / 135**.
- Repaired the frontend model-selection fallback: an embed-only model list no longer leaves the UI
  selecting nonexistent `friday-agent`. Updated three credential-client assertions to the documented
  centralized local API base. Fresh verification: frontend **117 / 117** tests pass and
  `npm run build` succeeds.
- Phase 5 remains blocked by absent credentials for the configured hosted model providers; the local
  4B model has not completed the required tool-using Hermes run. No 5.x box was ticked.

## Phase 5 provider integration refresh — 2026-11-16

- The native Alex launcher now loads the project `.env` for Matrix and Hermes child processes. A
  post-restart Matrix request through the configured Groq route returned `ready`; credentials are
  not recorded here.
- Updated the stale Groq route from unavailable `llama-3.3-70b-versatile` to the account-visible
  `openai/gpt-oss-120b`. Matrix tool-call compatibility was verified with a real `write_file`
  function call.
- A real Hermes run completed a file-and-terminal task: `run_378248f6` made
  `Storage/Artifacts/hermes/runs/run_378248f6/verification.txt`, recorded 3 API calls and 14,094
  tokens, and returned its artifact path.
- Full terminal/file/search/web runs remain blocked by the Groq account's hard 8k TPM limit: Hermes'
  initial agent context is 30,064 tokens and Groq returns HTTP 413 before a tool call. Hermes tool
  discovery was configured for deferred schema loading, but the base runtime context remains above
  the account limit. Phase 5.1 is therefore still unticked; completing it requires a higher-TPM
  provider tier or a credential for another compatible hosted provider.

## Phase 5 routing recheck — 2026-11-16

- Restarted the native Face, Matrix, and Hermes stack after changing the fast, agent, and coding
  Groq fallback to `qwen/qwen3.8-27b`; all three health checks passed.
- The first probe used API labels rather than Hermes toolset names and failed fast with
  `invalid_params`; it made no provider request. The corrected run used `terminal,file,search,web`.
- The corrected multi-tool run reached Matrix, but Groq rejected the first Qwen request with HTTP
  413: **41,772 input tokens requested** against the account's **7,000 ITPM** limit. Matrix's other
  fallbacks also failed: FreeLLM returned invalid JSON, the configured free OpenRouter model is no
  longer available, and the local Ollama endpoint returned invalid JSON. The run was stopped; it
  created no artifact and did not execute a tool.
- This reconfirms that **5.1 remains unticked**. The checklist has not been advanced on the strength
  of routing, health checks, or an unsuccessful run.

## Matrix local-fallback repair — 2026-11-16

- Fixed two defects that had made the healthy local Ollama server appear unavailable. Matrix now
  forces `stream: false` only for its Ollama upstream because Matrix consumes one JSON response,
  while Ollama's streamed response is NDJSON. The profile parser now splits only the first colon,
  so `ollama:qwen3:4b-16k` no longer becomes the nonexistent model `qwen3`.
- Added `tests/alex/test_matrix_gateway.py`; it verifies the full model ID and non-streaming
  Ollama payload. Fresh focused test: **1 passed**. A live Matrix request using the `local` profile
  returned the streaming envelope with exact content `local-ready` after the upstream local route
  completed successfully.
- Retried Hermes through the repaired fallback with the file-only `run_29a2653c`. It reached the
  local model but produced no output, tool call, usage record, or artifact in three minutes, so the
  bounded probe was stopped cleanly (`hermes exited with code -15`). This was not evidence for 5.1
  or 5.7 at the time; the current 5.1 and 5.7 evidence is recorded in the 2026-11-17 addendum.

## Matrix-only Hermes route proof — 2026-11-16

- Verified the Matrix process identity, stopped only that native process, and confirmed that
  `127.0.0.1:8700/health` refused connections. During the outage, a new Hermes run
  (`run_b6d7f46d`) made no response, usage record, or artifact and did not receive a response from
  any direct provider. It was stopped safely.
- Restored only the missing layer with `alex up`; Face, Matrix, and Hermes all passed their health
  checks. This proves the configured `custom` Hermes provider is constrained to Matrix, so **5.2 is
  now checked**. It does not establish the separate per-tool bridge integration in 5.3.

## Hermes per-tool bridge wiring — 2026-11-16

- Added and enabled the local `~/.hermes/plugins/matrix-bridge` Hermes plugin. It registers real
  `pre_tool_call` and `post_tool_call` hooks, calls Matrix's local policy/ledger endpoints, fails
  closed when Matrix cannot be reached before a tool call, and carries `ALEX_TASK_ID` from the
  native runtime child environment.
- Added Matrix endpoints for the hooks: `/api/hermes/tool/pre` evaluates the existing policy and
  records approval gates; `/api/hermes/tool/post` writes sequential step evidence through the
  existing bridge. Hermes plugin validation passed (including isolated `register()`), and
  `hermes plugins list` reports `matrix-bridge` as **enabled**.
- After a full restart, a live pre-hook request for `terminal` with `rm -rf /` returned a Matrix
  block under **DENY-003**. 5.3 stays unticked: its required proof also needs an agent-originated
  tool call and measured memory-prefetch reduction.

## Matrix memory-prefetch implementation — 2026-11-16

- Added a bounded, local-only Matrix memory retrieval endpoint at
  `/api/hermes/memory/prefetch`. It ranks exact query-token matches from the `knowledge` table,
  returns at most three records and caps output at 1,200 characters; it never mutates or exposes a
  raw database table.
- The enabled `matrix-bridge` plugin now registers `pre_llm_call` and injects only that compact
  context. Tests cover relevance, output capping, empty memory, and the endpoint cap; **4 focused
  tests passed**. Hermes plugin validation also passed after the new hook was registered.
- After a full service restart, the live endpoint and installed hook both retrieved the existing
  `user_name` profile record. **5.3 remains unticked**: the acceptance criterion still requires a
  real agent-originated policy-blocked tool call and a measured first-agent-turn prompt result.

## Hermes structured-progress implementation — 2026-11-16

- The Hermes runtime now parses valid `STEP n/N: description` output while its child agent is still
  running and writes the resulting step number, total, label, and running status through Matrix's
  task-progress ledger. It also exposes the current milestone in the live run record.
- A subprocess-level test emitted `STEP 1/2` and `STEP 2/2`; it verified both live run state and
  the two Matrix ledger writes. The focused Phase 5 tests passed (**7 passed**) and the complete
  Face/Matrix/Hermes stack was restarted successfully.
- **5.4 remains unticked** until a non-test Hermes agent run produces milestones and the Matrix
  dashboard visibly reports those real `n/N` values.

## Evidence-verified completion implementation — 2026-11-16

- Matrix now refuses status-only completion claims such as `done`, `task completed`, and `all
  finished successfully`. For a complex task it records **EVIDENCE-001**, updates the task as
  still running, and steers exactly once for a concrete artifact, verified observation, or tool
  result; a second evidence-free claim fails instead of being marked complete.
- The targeted execution test supplied `done` followed by an artifact-verification response. It
  proved two gateway calls, exactly one `steer` event, and completion only after evidence. Focused
  Phase 5 tests now pass **9 / 9** and the native stack passed post-restart health checks.
- **5.5 remains unticked** pending a live provider-run demonstration; the test proves the safety
  branch but is not being treated as production acceptance evidence.

## Irreversible-action idempotency implementation — 2026-11-16

- Matrix now derives a stable SHA-256 idempotency key from the task, tool, and canonical arguments
  for `send`, `mail`, `move`, and `book` actions. It atomically reserves the first action in the
  ledger and blocks repeats with **DUPLICATE-001** before the tool can execute.
- Tests prove the same `mail.send` claim is accepted once and rejected on retry. After a stack
  restart, a live `booking.create` policy-hook probe returned `allow` once and then
  `DUPLICATE-001`; the probe did not create a real booking or send mail. Focused Phase 5 tests:
  **11 passed**.
- **5.6 remains unticked** pending an agent-originated, approved send/move/booking retry through
  the real Hermes hook chain.

## Local offline-route correction — 2026-11-16

- Corrected the stale `local` profile and offline worker payload to use the installed,
  Matrix-verified `ollama:qwen3:4b-16k` rather than the stock 4k-context alias. A live streamed
  Matrix `local` request returned `local-16k-ready`; focused Phase 5 tests remained **11 passed**
  and all services restarted healthy.
- The machine does not have the checklist's originally requested `qwen3-4b-64k` model: installed
  local tags are `qwen3:4b-16k`, `qwen3:4b`, `qwen3-vl:4b`, and `qwen2.5:0.5b`. This historical
  snapshot predates the checkpoint/resume endpoint; the current installed tag and live resume
  evidence are recorded at the top, and **5.7 is now checked**.

## Local document-to-PDF deliverable — 2026-11-16

- Added a dependency-free PDF writer for locally generated documents. It uses a built-in PDF font,
  supports paginated text, and writes a portable PDF without needing an external renderer.
- Focused test created a PDF and validated it with `pdfinfo`; a real artifact now opens at
  `Storage/Artifacts/phase5/pdf-verification.pdf` (one letter-size page, PDF 1.4). Focused Phase 5
  tests: **12 passed**.
- **5.8 remains unticked**: the repository still lacks an approved-mail sending adapter and a
  configured account/Sent-folder proof. The PDF half is real; the external-mail half is not claimed.

## Network-loss checkpoint persistence — 2026-11-16

- Matrix now writes a durable checkpoint before pausing a network-dependent task. Each record
  stores the reason, next step, prior artifacts, idempotency keys, token count, and optional Hermes
  identifiers, so resume logic has state to work from instead of a bare `paused` label.
- Tests verify checkpoint sequencing and round-trip retrieval. The focused Phase 5 suite is now
  **13 passed**, and Face, Matrix, and Hermes passed a clean restart and health check.
- **Historical note:** this 2026-11-16 entry predates the live resume endpoint and is superseded by
  the 2026-11-17 evidence at the top of this report; 5.7 is now checked using `qwen3:4b-16k`.

## Phase 6.1 document-store implementation — updated 2026-11-17

- Added a Matrix-owned embedded document store at `Storage/mongodb/knowledge.db`, with collections
  `people`, `preferences`, `skills`, `experiences`, `artifacts`, and `episodes`; Mongo-style
  `find`, `insert`, `update`, `upsert`, dotted-path matching, and indexed dotted-path lookup.
- Matrix startup now idempotently migrates legacy `contacts`, `knowledge`, and `pitfalls` rows
  without changing the source database. Live migration verification compared every legacy row:
  contacts **2/2 exact**, knowledge **1/1 exact**, pitfalls **0/0 exact**. The new database passes
  SQLite `integrity_check`.
- Added a verified web-scraping skill only after real DuPont and Croda tasks completed. The named
  indexed lookup returns one record in **13.592 ms from a cold process including store
  initialization**. Live migration still matches every legacy row exactly (contacts **2/2**,
  knowledge **1/1**, pitfalls **0/0**); the old database was read-only.
- `PRAGMA integrity_check` returns `ok`. A review found that `sqlite3.Connection` context managers
  commit but do not close; the document store now explicitly closes every connection. A regression
  test checks connection lifetime, and `lsof` showed no process holding the database after Matrix
  requests. Focused document-store and reuse tests pass. **6.1 is checked** in `CHECKLIST.md`.

## Phase 6.2 ledger↔memory links — 2026-11-16

- Added the `memory_ref` column to existing and new ledger task rows, a `link_memory_ref()` writer,
  and a two-way audit exposed at `GET /api/memory/links/audit`. It reports tasks pointing to
  missing experience IDs and experiences whose task IDs are absent or do not point back.
- Focused store tests pass. The live ledger contains verified scrape experiences whose `task_ids`
  resolve through each task's `memory_ref` to real events. The current Matrix audit reports **0
  task orphans and 0 experience orphans**. **6.2 is checked** in `CHECKLIST.md`.

## Phase 6.3 OKF concept bundle — updated 2026-11-17

- Added person concepts for the two legacy contacts, then updated DuPont and Croda company concepts
  from verified Matrix tasks. Both company pages link to the web-scraping skill and cite their task,
  experience, source, script, and artifact. The skill page links back to both companies.
- Updated company, skill, and root indexes. The original eight-file link audit passed; the expanded
  bundle is being re-audited with Phase 6.7. Step **6.3 remains checked** in `CHECKLIST.md`.

## Phase 6.4 artifact routing — 2026-11-16

- Added a typed artifact router for images, videos, text, Word files, presentations, and PDFs;
  reusable code is stored under `Artifacts/code/<task-id>/` with `manifest.json`. Artifact
  manifests include task ID, path, kind, size, timestamp, and SHA-256; each artifact is also
  indexed in the document store for lookup by task ID.
- PDF generation now writes a timestamped script and payload under `Storage/temp/temp_code/`,
  executes it there, routes the PDF to `Artifacts/pdfs/`, and removes all temporary files.
- A real task `T-PHASE64-PDF` produced a one-page PDF 1.4. Its manifest hash matches the disk file,
  and task lookup returns its path. The temp-code directory was empty afterward. Focused tests:
  **2 passed**. Step **6.4 is checked** in `CHECKLIST.md`.

## Phase 6.5 task-close experience writer — 2026-11-16

- Verified successful task closure now upserts a deterministic experience document containing the
  inferred skill, named subjects, outcome, evidence, artifact paths/checksums, and a ledger events
  reference. The stable experience ID is written to `tasks.memory_ref`; retries refresh the same
  document instead of adding duplicates.
- A real verified close for `T-PHASE64-PDF` created one `document_creation` experience linked to its
  PDF manifest and event 179. A repeated close retained one experience and refreshed its event IDs.
  The live task→experience→events path resolved, and the two-way audit reported **0 orphans across
  29 tasks and 1 experience**. Focused tests: **5 passed**.
- Steps **6.2** and **6.5** are now checked in `CHECKLIST.md`. A test exposed that array membership
  in the `task_ids` index was mishandled; the document store now indexes array elements, and the
  live lookup by `task_ids` returns the experience.

## Phase 6.6 hybrid retrieval — 2026-11-17

- Added Matrix's `/api/memory/search` endpoint and a persistent retrieval index beside the document
  store. It indexes Matrix documents, ledger tasks, and events in SQLite FTS5; local
  `nomic-embed-text` embeddings are cached by document content hash. Retrieval applies a rule-based
  lexical/semantic weighting, one-hop task-link expansion, RRF, then recency, importance, and
  access-count reranking. The endpoint was exercised against the live Matrix service and returned
  the PDF task, linked experience, and ledger events; the memory-link audit stayed at **0 orphans**.
- Added a 30-query labeled benchmark and repeatable runner at
  `tests/alex/fixtures/retrieval_benchmark.json` and `scripts/alex/benchmark_hybrid_retrieval.py`.
  Fresh hits@5: FTS-only **29/30**, vector-only **28/30**, hybrid **30/30**. Labels treat a task and
  its own event/experience records as relevant. This measures the current small local corpus and
  is not a claim of general retrieval quality beyond it.
- Verification: `uv run pytest tests/alex -q` → **28 passed**; targeted Ruff checks for the new
  retrieval, benchmark, and test files passed; `git diff --check` passed. The API emits the existing
  FastAPI startup deprecation warning and OpenAPI reports a pre-existing duplicate CSV operation ID.
- Step **6.6** is checked in `CHECKLIST.md`. Changes remain uncommitted because the shared worktree
  contains other in-progress files; no unrelated changes were included in a commit.

## Phase 6.7 verified procedure reuse — 2026-11-17

- Added a Matrix worker path for supported public company about-page requests. It looks up the
  `webscraping` skill and matching subject experiences, loads and smoke-runs a preserved script,
  or creates a new subject script when there is no verified procedure. It stores scripts and JSON
  page captures under `Artifacts/`, and records per-subject ledger tasks, evidence, events, and
  reciprocal experiences. Matrix updates the company and skill OKF concepts only after success.
- Live acceptance: seed task `T-20261117-24E859` learned the first DuPont script. Composite task
  `T-20261117-A9EFD0` reused it for child task `T-20261117-DUPONT-9D5DFA` and built Croda's script
  from scratch for `T-20261117-CRODA-4B23D2`. Both official about pages returned HTTP 200; captures
  contain **3,027** and **3,520** readable characters. Each child task is verified and linked to
  its own experience, code artifact, output artifact, and ledger events. The link audit returned
  **0 orphans**. Later live retries confirmed both scripts are reusable.
- Safety and repeatability checks: page targets are fixed to the official company URLs; script
  fetches verify TLS, enforce an expected host across redirects, cap response size, check
  `robots.txt`, and fetch one page only. Focused reuse/store tests pass; `uv run pytest tests/alex -q`
  → **28 passed**. Step **6.7 is checked** in `CHECKLIST.md`.

## Phase 6.8 RAG brief into Hermes — 2026-11-17

- Added a token-bounded Matrix memory brief for Hermes' first model call. Each claim carries
  `{source, id, age}` provenance. Matrix retrieval now returns record timestamps, and OKF concept
  files without an authored `updated_at` use their filesystem modification time for age.
- Updated the installed Hermes Matrix bridge hook to request the 1,200-token brief. Live endpoint
  verification returned **5 claims / 245 whitespace-delimited tokens**; every claim included all
  provenance fields and resolved to a real OKF file or ledger row. Calling the real
  `pre_llm_call` hook returned the brief with provenance (**249 words including the heading**).
- Verification: focused memory/retrieval tests → **11 passed**; Ruff → passed. The documented
  non-live/non-cloud/non-hub test lane completed: **9,437 passed, 98 skipped, 33 deselected,
  0 failed**. Existing deprecation warnings and an optional wake-listener thread warning about
  missing `sounddevice` were reported; they did not fail tests. Step **6.8 is checked** in
  `CHECKLIST.md`.

## Phase 6.9 contact book and standing preferences — 2026-11-17

- Added explicit statement capture to Matrix's document store for contact email addresses and the
  user's favorite/favourite place. The Hermes pre-LLM hook submits each message to the capture
  endpoint; only matching save/remember/store statements write data, and matching contacts or
  preferences are updated in place.
- Live bridge verification used a synthetic QA contact. The save statement reached the contact
  store; a follow-up request to draft an email for that name received the saved address plus the
  instruction to use saved recipients without asking again. A separate favorite-place statement
  was recalled verbatim by a subsequent question. Temporary synthetic contact/preference rows were
  removed after verification.
- Verification: contact, preference, and endpoint tests → **7 passed**; all Phase 6 tests via
  `uv run pytest tests/alex -q` → **33 passed**; Ruff and `git diff --check` passed. **6.9 is checked**
  in `CHECKLIST.md`.

## Phase 6.10 transparency and durable forgetting — 2026-11-17

- Added a “what do you know about me?” path that lists only current contacts and preferences,
  with provenance and age, and records which entries that Hermes session saw. “Forget that”
  tombstones those entries rather than deleting their evidence; hybrid retrieval removes
  tombstoned documents from its live index. Tombstones are durable in the document store.
- The first live isolated run exposed a 500 from a keyword-only helper called positionally.
  Corrected the API call and strengthened its route test. The isolated end-to-end flow then
  captured and listed a synthetic contact, tombstoned it, returned zero retrieval hits, restarted
  Matrix, and again returned zero about-list entries and zero search hits. The production bridge
  about command also returned successfully; no real user records were forgotten.
- Verification: complete `tests/alex` suite → **37 passed**; Ruff and `git diff --check` passed.
  **6.10 is checked** in `CHECKLIST.md`.

## Phase 6.11 persona and stage directions — 2026-11-17

- Replaced the malformed packaged SOUL text and merged the persona with Alex's stage directions.
  The active `/Users/mdshabazkhan/.hermes/SOUL.md` and packaged `SOUL.md` now match. Wake and
  dialogue share the exact scripted greeting; direct answers and task completion use
  “Anything else, master?”; “No” returns the scripted sign-off and `close_app` action.
- Made dialogue/API and failed-reflex error replies outcome-first and concise, without exposing
  exception classes or raw provider details. Verified task-completion speech arms the same
  yes/no follow-up state as a direct answer.
- Verification: persona/error tests → **10 passed**; `uv run pytest tests/alex -q` → **47 passed**;
  server routes + integration → **79 passed**; Ruff and `git diff --check` passed. Live
  `/api/alex/chat` returned the scripted follow-up then the close action after “No.” The action
  path is confirmed; the actual desktop window-close check remains the GUI-only limitation already
  recorded under Phase 3.8. **6.11 is checked** in `CHECKLIST.md`.

## Phase 6.12 storage janitor — 2026-11-17

- Added `jarvis alex janitor` with dry-run as the default. It cleans only the five approved
  `Storage/temp/` subdirectories under their retention rules, skips files referenced by the task,
  experience, or concept stores, skips active writers, and vacuums the SQLite stores on apply.
  Orphan quarantine is reversible and limited to manifest-backed items in routed artifact/code
  directories; it leaves Hermes run workspaces, the Artifacts index, and unmanifested legacy files
  alone. The one-hour/daily scheduler remains step 8.5.
- The first production dry run exposed an overbroad orphan scan that proposed Hermes run logs and
  `Artifacts/index.md`. Narrowed the scan and added regression coverage before applying anything.
  The corrected production dry run proposed **0 temp deletions and 0 quarantines**; `Storage/temp`
  measured **8,884 bytes** against the **1 GiB** budget. Its JSON log entry and durable ledger event
  both record the empty plan.
- A fixture-backed apply run removed a simulated yesterday recording and script and reclaimed their
  bytes, while preserving a task-referenced artifact from yesterday. Tests also cover retention
  boundaries, reference protection, active writers, manifest-backed quarantine, and the CLI default.
  `tests/alex/test_janitor.py` → **8 passed**; all `tests/alex` → **55 passed**; targeted Ruff and
  `git diff --check` passed. **6.12 is checked** in `CHECKLIST.md`.

## Phase 6.13 backup and restore drill — 2026-11-17

- Added `jarvis alex backup` and `jarvis alex restore`. Backups use SQLite's online backup API
  for the document store and task ledger, copy the OKF `knowledge/` bundle and durable `Artifacts/`,
  and write a SHA-256 file manifest. Restore validates every file and both SQLite integrity checks,
  stages the result, and only publishes into a new destination after validation passes.
- Production drill backed up **72 files** and restored them under
  `/tmp/alex-phase613-20261117/restored`. Experience `exp-b36dc3d8850306e4e016c314` was read from
  the restored database and matched the original document exactly. Its PDF artifact matched the
  original bytes and SHA-256 (`0bc8947b38e07dbe7514761d4cd3ea4723173968e165f3a19edd27e45052d49f`).
  The source databases and files were not changed by the drill.
- Tests cover exact restore, rejection of a checksum-corrupted backup without partial output,
  refusal to overwrite an existing backup, and the CLI entry points. Backup tests → **4 passed**;
  all `tests/alex` → **59 passed**; Ruff, CLI help, and `git diff --check` passed. **6.13 is checked**
  in `CHECKLIST.md`.

## Phase 6.14 retrieval growth control — 2026-11-17

- Retrieval synchronization now checks each document against both its indexed content hash and
  vector hash. It embeds only changed or missing vectors, in batches of 32, committing every batch
  atomically. If an embed call fails partway through a rebuild, committed batches remain valid and
  the next sync resumes at the first missing/stale batch. A missing-vector repair test also covers
  recovery from rows left by the earlier non-resumable implementation.
- The one-document edit test confirms the embedder receives exactly that one changed record. A
  simulated interruption after one batch then a retry proves that the first batch is retained and
  only incomplete work is repeated. Read-only benchmark runs exclude access-history reranking so
  results are repeatable. The live benchmark exposed one wording mismatch (“bazaar” versus
  “market”); added hybrid-only synonym expansion while keeping the FTS baseline untouched.
- Latest labeled 30-query run: FTS **29/30**, vector **27/30**, hybrid **30/30**. Focused retrieval
  tests → **13 passed**; all `tests/alex` → **64 passed**; targeted Ruff and `git diff --check`
  passed. **6.14 is checked** in `CHECKLIST.md`.

## Server chat routing repair — 2026-11-17

- A documented-lane suite run had exposed many chat route failures. The server's chat handler
  unconditionally posted to `127.0.0.1:8700`, then returned `None` when Matrix routing was disabled;
  its Matrix success path also referenced undefined `alex_res`. The standard engine/agent/stream
  fallback and trusted memory-context injection had been lost. Matrix routing is now explicit via
  the `matrix_url` supplied by the Alex CLI, while generic server instances use their injected
  engine. Focused tests cover both routing modes.
- Verification: **102 passed** across server routes, model management, integration, and
  SkillOrchestra security tests. Existing FastAPI lifecycle deprecation warnings remain.

## Phase 4 live voice-loop repair — 2026-11-17

**2026-11-18 follow-up.** Manual replay now uses the same Samantha speaker as Alex's automatic replies. The desktop player previously bypassed the microphone's playback guard. Native capture now stops accumulating audio when a turn expires, uses speech detection for partial and final transcription, and requires a fresh final transcript before submission. Regressions reproduced duplicate playback routing and stale partial submission before the fix. The frontend suite passed 122 tests and the Alex/server suite passed 248. The live service reports Samantha as the native speaker and serves the rebuilt frontend. Live microphone and speaker acceptance remains open.

- Restored Matrix on port 8700 after it had stopped; Face, Matrix, and Hermes are healthy again.
  This was the immediate reason a live microphone turn could be captured without receiving a
  response.
- Fixed `useSpeech` so a native microphone response is accepted only when it explicitly says
  `status:"recording"`. Previously, a server-side CoreAudio failure still returned HTTP 200, which
  the UI displayed as Listening and prevented browser microphone fallback. The hook now exposes
  the error, falls back correctly, and refuses to reopen an already-active capture stream after a
  React render. This removes a repeated-mic-open race in continuous conversation.
- Added macOS `NSMicrophoneUsageDescription` to the Tauri bundle, then rebuilt and launched the
  desktop app. The live UI auto-started in **Listening** state. A visible live turn (`Hello Alex`)
  completed through the Matrix response path and returned to Listening. The speech synthesis route
  produced a valid 24 kHz PCM WAV response (88,448 bytes, Samantha voice).
- Fixed automatic spoken-reply preferences: they are now enabled by default and persist after a
  reload rather than being forcibly reset off. Focused hook/settings/TTS regressions: **23 passed**;
  frontend build and signed Tauri app build passed. The ten real spoken-turn acceptance gate is
  deliberately still open in the checklist until human-audible verification is recorded.
- A clean restart of the rebuilt bundle then auto-opened a native microphone stream with no click:
  `/v1/speech/mic/status` reported `recording:true` and `state:"listening"` across repeated samples.
  The corresponding Phase 4 launch/microphone gate is now checked; the spoken-turn gates remain open.

## Voice: the echo, continuous transcription, and human turn-taking — 2026-11-17

**The echo was not acoustic — the app said every reply twice.** The Face speaks each Alex reply
through `say` (`/v1/chat/completions` → `_alex_speak(reply)`), and the desktop UI separately
autoplayed the same finished message by synthesising it again (`ChatArea` → `tts.speak` →
`<audio>`). Two voices, one a beat behind the other: that is the doubling heard on every answer.

**Fix — one voice, decided by whoever holds it.** `Speaker.status()` now reports `last` and
`last_finished_at` alongside `speaking`, and the UI asks before it plays
(`serverHoldsTheVoice(status, reply)`): if the server is speaking, or has just finished saying that
same line, autoplay stands down. It still autoplays when the server stayed silent (plain model
answers). Measured live: one `say` process for `Hello. How can I help you today? Anything else,
master?`, `speaking: true` while it runs, then `last` = that exact sentence after it ends — so a long
stream that outlives the speech is still recognised.

**Mic echo, second layer.** The native capture callback now gates on the speaker itself
(`voice.status()["speaking"]`, not just a `pgrep say` guess) plus a 1.2 s tail, clears its buffer
while Alex talks, and the browser fallback requests `echoCancellation`/`noiseSuppression`/
`autoGainControl`. A latent bug made this worse: nothing called `note_speaking_done()`, so the
listening session stayed in `SPEAKING` for the rest of the process life — after the first reply it
could never submit again. The speech monitor now hands the turn back when `say` exits; verified live
(`state: speaking` → `listening`).

**Continuous transcription.** The microphone no longer waits for the end of a recording to understand
it: every 2 s the buffered audio is transcribed on a worker thread, fed into the listening session and
exposed as `partial` from `/v1/speech/mic/status`, so the UI can show the sentence as it forms.

**Human turn-taking (`alex/face/listening.py`).**
- `utterance_complete()` decides whether a thought finished: terminal punctuation finishes, a trailing
  comma or dangling function word ("about", "the", "to") does not, one bare word is too little.
- An unfinished sentence that has been quiet for 6 s gets **one** nudge, spoken: "Can you specify
  further?" — the session marks that it asked, so status polling cannot nag or loop.
- Saying "listen to this" at the start marks the turn long-form: the cue is stripped from the
  transcript, the silence budget grows from 5 s to 15 s, and the user is never nudged mid-dictation.

**Every turn is kept.** `alex/face/voice_notes.py` writes the recording to
`Storage/temp/voice/<utc>.wav` and its transcript to `Storage/temp/transcriptions/<utc>.json` (+ `.txt`),
sharing one timestamp stem and cross-referencing each other. `janitor.TEMP_RETENTION` now expires
`voice`, `transcriptions`, `logs` and `temp_code` at 24 h (they were `None`, i.e. swept regardless of
age) with `scratch` at 24 h and `cache` at 7 d, and the boundary is inclusive so a day-old file is due.

**Verified.** `tests/alex/test_listening_voice_flow.py` (24 checks: completeness, one nudge only,
long-form budget, sidecar pairing, 24 h retention) + janitor suite → **28 passed**; `tests/alex` →
**122 passed, 2 environment failures** (`pdfinfo` from poppler is not installed; the gold-rate test
hit the live network and got a real answer instead of the mocked failure). Frontend: **131 tests**,
`tsc --noEmit` clean. Live over HTTP: `long_form` action with a 15 s budget and the cue stripped;
`clarify: true` with `clarification: "Can you specify further?"` after 7 s of quiet; `speaking`
returning to `false`/`listening` when the voice finishes; a real reply spoken exactly once.

**Not verified.** Ten spoken turns with a human listening, first-audio latency under 300 ms, and the
wake phrase firing — all still need the microphone. The rebuilt app carries the fix, but nothing here
watched the window itself.

## Duplicate app, the clock, the conversation log — and the rest of the echo — 2026-11-17

**Two applications, one bundle id.** `/Applications/Alex.app` (2026-11-14) and
`/Applications/OpenJarvis.app` (rebuilt) both declared `com.openjarvis.desktop`, so Launchpad showed
two "apps" and it was impossible to tell which one carried the fixes. `Alex.app` was moved to
`~/.Trash/Alex.app-duplicate-20261117`; OpenJarvis.app is the only one left.

**The agent could not tell the time — because nothing told it.** Two separate causes:
1. The time fast-path matched a fixed phrase list, so "What time was it?" and "do you have the time?"
   fell through to the model.
2. The model was never given the clock, so it correctly answered that it had no access to one.

Now `dialogue._TIME_QUESTION` / `_DATE_QUESTION` match the *shape* of the request (contractions
included: "what's the time"), the Face uses the same shape matching, and every Matrix-bound request
carries a leading system line — `Current local date and time: Tuesday, 17 November 2026, 10:14 PM IST.
You have a clock; answer time and date questions from it.` Direct check: "What time was it? What time
was it?" → "It's 10:13 PM now, sir."; "what's the date" → "Today is Tuesday, 17 November 2026."

**The whole conversation, one file per day.** The ledger records tasks and events, never sentences, so
there was nothing to read afterwards. `alex/conversation.py` appends one JSON object per turn to
`Storage/logs/conversation/YYYY-MM-DD.jsonl` — the *same* file for the day, appended in place, so a
day's dialogue is one file to open and costs one line per turn. It lives under `Storage/logs`, not
`Storage/temp`, precisely so the janitor's 24-hour sweep cannot erase it. Served by
`GET /api/conversation` on Face and Matrix, and the Logs page now renders a **Conversation** section
(You / Alex, with timestamps) above the task ledger, with both included in Copy All. Verified live:
one Face turn produced exactly one line, and `/api/conversation` returned it.

**Echo, the remaining path.** Matrix owns its own speaker process, so a reply voiced by Matrix was
invisible to the Face's speaker status and the UI would autoplay it again. `/v1/alex/voice/status` now
also reports `system_speaking` (the cross-process `say` check), and the client defers to that too. The
"listen" barge-in branch, which answered in text only, still does — it should silence Alex, not start
talking again — but its turn is now logged.

**Checks.** `tests/alex` + `tests/server/test_routes.py` → **187 passed, 2 failed** (`pdfinfo` is not
installed — the only failure left in the PDF deliverable test; the gold-rate persona test is now
deterministic and passes). Frontend **131 tests**, `tsc --noEmit` clean. Live: services healthy after
`alex down/up`, time answers on both the Face and Matrix paths, one conversation line per turn.

**The same bug hid in recall.** "What did we do two months ago?" was answered "I do not have access
to our past conversation history" while hybrid retrieval existed and worked. Retrieval was simply
never put in front of the model. `dialogue.is_recall_question()` now recognises recall by shape
("what did we do…", "do you remember…", "last time…", "…months ago"), `recall_context()` collects the
top hybrid-retrieval rows *plus* recent ledger tasks with status, evidence and artifact paths (task
rows carry no artifacts, so artifact documents are looked up by task id), and the answer is instructed
to cite date, outcome and path, or say plainly that the period is not covered.

Live: "What did we do two months ago?" → "I have no records of work from two months ago; my oldest
available log is from November 15, 2026, which covered a failed lock test and an online Diwali market
research task." "What did we do today?" → names the day's real tasks and their outcomes. Tests:
`tests/alex/test_clock_and_recall.py` (20 checks).

## The echo, corrected: my previous fix was not enough — the UI still had a second voice 2026-11-17

The earlier change added a *guard* around UI autoplay (ask the server whether it is speaking, skip if
so). It was the wrong shape of fix. The second playback path still existed, and any timing hole,
failed fetch or unseen speaker left it free to play — which is exactly what was still being heard.

**Measured first, changed second.** One chat request, sampled every 300 ms: a single `say` for
22:24:28→22:24:33, Face `spoken` 0→1, Matrix `spoken` 0. So the server says one line once. The double
was entirely client-side.

**What actually changed now:**
1. **Autoplay deleted, not guarded.** `ChatArea` no longer plays a finished reply at all. The Face
   speaks every Alex reply through `say` before streaming it; the server is the only voice. The
   per-message "Speak" button remains for deliberate replay.
2. **The dead toggle is gone.** Settings no longer offers "Speak replies automatically", because it
   would now do nothing — the reply is already spoken by the server. Leaving a switch that silently
   does nothing is how this bug survived a "fix" in the first place.
3. **The speaker refuses duplicates.** `Speaker.speak()` will not queue the same sanitized line while
   it is already speaking, nor within 3 s of having just finished it. Two callers (a chat reply and a
   task event, or a repeated request) can no longer produce the same sentence twice, a beat apart.
   Different lines are unaffected.

**Verified.** `tests/alex/test_voice_dedupe.py` (3 checks: identical line refused, different line
spoken, sanitising stable) plus the full `tests/alex` + `tests/server/test_routes.py` →
**211 passed, 1 failed** (the `pdfinfo`-less PDF test). Frontend **121 tests**, `tsc --noEmit` clean
(the 10 autoplay-gating tests went with the code they tested). Live: two rapid chat turns produced
one `say` at a time and two different replies, each spoken once; `spoken` advanced by exactly 2.
Built bundle verified from its own assets: `dist/assets/index-*.js` (22:28) contains the conversation
panel and no longer contains the autoplay setting; installed to `/Applications/OpenJarvis.app` at
22:28:30.

## Phase sweep, 2026-11-17 evening: four defects found by testing instead of reading

The remaining checklist rows were "implemented, unverified". Testing them found four real defects, each of
which would have looked fine in code review and none of which a human ear or eye would have diagnosed.

**4.8 — intent rates were dead on arrival.** The configured rates were 155 (failed) and 175 (done).
Rendered to file, both produced byte-identical audio (58 900 bytes), while 150 produced 63 868 — so the
rate flag worked, those two values simply landed in the same bucket. "Done" and "failed" genuinely
sounded the same. Worse, `_alex_speak()` called `voice.speak(text)` with **no intent at all**, so every
chat reply used the default 175 and the whole per-intent table never reached the speaker. Rates are now
~10 % apart (failed 130 … answer 200), pitch is carried per intent (`say [[pbas N]]`: 38 calm for failure,
54 bright for completion), and `_alex_speak` passes its intent through. Verified live: the running `say`
process reads `say -v Samantha -r 200 [[pbas 52]] …` for an answer, and the same sentence renders 2.567 s
at `186/pbas 54` versus 2.923 s at `130/pbas 38`.

**4.10 — passes on content.** Five forced failures (rate limit, dropped connection, stale heartbeat,
malformed provider JSON, permission error) produced five distinct plain-language replies, none leaking
`Error`, `Exception`, `Traceback`, `429`, `JSON`, `Errno` or a class name.

**4.9 — measured, not assumed.** `voice.speak()` → `say` process alive: **25 ms**.

**The dialogue session had two bugs that lost user requests.** A pending clarification question owned
*every* following turn: ask "what should I make?", then ask something else, and that something else was
stored as the topic and dispatched as a task. The user's real question vanished into a task title. And
turns were not serialised, so two arriving together shared one `Session` and spliced their text: the
task title `what did we do two m on what did we do with the Dupont renewal?` is exactly that splice. Both
are fixed — turns are atomic per session, a new question abandons stale slots, and recall questions are
answered from records rather than dispatched. Two junk tasks and their rows were deleted from the ledger
and the retrieval index (13 events, 1 step, 1 document each).

**Recall could not name a file, and denied having files at all.** Deliverables are filed in the artifact
store keyed by task, not in `tasks.artifacts_json`, so `recall_context` never saw them; and
"what files did we make for it?" did not match the recall pattern, so it was answered "I don't have
access to your file system" while the paths sat in the database. Recall now merges `artifacts_for_task()`
and its pattern covers files/documents/artifacts/PDFs. Live: "what did we do with the Dupont renewal?"
→ task id, date, outcome and both artifact paths.

**8.2 — autostart actually works now.** `com.openjarvis.alex.plist` existed but was never installed, so a
reboot brought back only Face. Installed after substituting the real paths; `launchctl bootstrap` ran
`alex up`, exited 0, and left the tree healthy with no duplicate Face. The tray's "Health: starting..."
item was a frozen string; it now polls 8000/8700/8642 every 5 s and labels the real state.

**Research is grounded, not canned.** Asked for the current OpenJDK LTS, Alex answered Java 25 with patch
25.0.5 (+8, October 2026) and cited sources. Cross-checked against the OpenJDK wiki (`25.0.5+8 (GA),
October 20th 2026`) and Oracle's release notes — correct build and date, so the answer came from the web.

**8.3 soak is running** (`Storage/logs/soak-20261117-2239.csv`): a live chat turn every ~2 min for an
hour, sampling pressure, per-layer RSS, free memory, storage and turn latency. Early samples: 48–50 %
free (never red), Face RSS 320–589 MB oscillating with GC, Matrix 67–94 MB, storage flat at 15 MB, turns
45–77 ms. The 15 min offline tail was deliberately left out of the automation.

**Late 2026-11-17 — two voices, and a voice answering its own silence.** The user reported two different
voices talking over each other and, separately, Alex starting conversations nobody had. Both were real
and neither was the autoplay that had already been removed.

*The second voice was a second process.* `alex/face/voice.py` says "the only thing in the app that
speaks", but Face (:8000), Matrix (:8700) and the Hermes runtime are **processes**, and each imported its
own copy of that module. Every process had a private queue, a private `say` and no idea the others
existed, so two of them could start a line in the same millisecond. The queue could never have fixed
this; the state was in the wrong place. Speech is now one machine-wide resource: `Storage/run/voice.lock`
is held around the `say` process itself, and `Storage/run/voice.last.json` records what was said and by
which process, so a duplicate arriving from another process is refused for 6 s (the claim is written
before spawning and refreshed on completion, so a duplicate queued behind a long line is still caught).
The last raw `say` — the wake-word fallback in `wake.py` — is gone; if the speaker is unavailable the
greeting is silent rather than doubled.

Measured with two real processes on the live machine: two **different** long lines started 50 ms apart →
max concurrent `say` = **1**, both spoken once (`spoken 1` each), 2 distinct `say` PIDs — serialised, never
overlapping. Two **identical** lines started 50 ms apart → **1** `say` process total, `spoken 1` vs
`spoken 0`. A normal live chat turn ("What date is it?" → "Today is Tuesday, 17 November 2026.") produced
exactly one `say` process, max concurrent 1. `tests/alex/test_silence_and_one_voice.py` (9 tests) pins the
claim/expiry rules and that four concurrent holders of the lock never overlap; `test_voice_dedupe.py`
still passes (12 passed together).

*The self-talk was Whisper describing silence.* The transcriptions the user pointed at are the proof:
`Okay.  Okay.  Okay.  Okay.  Okay.  Okay.  Okay.  Okay.` and `You`, both from 21-second recordings of
nobody speaking. Whisper does not return "" for room tone; it returns the most likely sentence, and the
listening session counted that as speech. It then submitted the turn, Alex answered "I understand.", the
answer was recorded as a new question, and the loop continued. The guard has three layers: the take must
carry speech energy (`MIN_SPEECH_RMS`), Whisper segments flagged `no_speech_prob > 0.6` or scored
`avg_logprob < -1.0` are discarded, and the text must not be a known silence artifact (repeated filler,
or a fragment that is never an instruction on its own). Replaying the offending recordings through the
real recogniser now returns `''` for both, and for two further "Okay." takes; `"thank you"` at normal
volume survives while the same words in a quiet take do not.

**Face had been dead for 146 launches, and the pid file said otherwise.** `~/.openjarvis/server.pid`
contained `794`, a server that had exited long ago; macOS had since reused 794 for Docker. The liveness
check was `os.kill(pid, 0)` on non-Linux, so a *recycled* PID looked like a live server and every launch
aborted with `RuntimeError: Another server is already registered (PID 794)`. Nothing was listening on
:8000 while the file looked healthy. `_registered_pid_alive` now reads the process's own command line on
macOS/Windows and treats a registration as stale when that process is not a server (falling back to
liveness only when the command cannot be read). After clearing the stale state, `launchctl kickstart`
brought Face up on pid 28968 with `{"status":"ok"}`; `jarvis alex down && jarvis alex up` then reported
all three layers healthy (8000/8700/8642 = 200).

**Default turn is 10 seconds.** The microphone's default maximum is now `MIC_DEFAULT_TIMEOUT = 10.0`
(was a hard-coded 25 s); "listen to this" still gets the long 25 s budget. Tests: `tests/alex` +
`tests/cli` daemon suites + `tests/server/test_routes.py` → **296 passed, 1 skipped, 1 failed**, the
single failure being the pre-existing `test_write_text_pdf_creates_a_readable_pdf`, which needs `pdfinfo`
(not installed on this machine).

**Still blocked, not unverified-but-claimed:** every mail step (5.8, the Phase 3 essay→mail gate, the
Phase 5 send gate) needs SMTP credentials, and none are configured; every microphone step (3.8 GUI
close, 4.2, 4.6, 4.8's by-ear check, and the Phase 4 gates) needs someone at the machine with a mic.

**Phase 3's second-task gate failed first.** "Make a Diwali card PDF" replied "What should it be about?" —
topic extraction only knew the "about X" shape, so a subject the user had just spoken was thrown away and
the request became a question. The leftover-phrase fallback fixed it: after the imperative ("make") and
the deliverable word ("card", "PDF") are removed, "Diwali" remains and becomes the topic; a genuinely
subjectless "write an essay" still asks. Retested live: essay dispatched, card dispatched alongside it
("Starting that alongside the other one: card on Diwali"), two hermes tasks in the ledger.

## Voice agent signed off — and what Astra 6.1 changed, 2026-11-18

The user closed the voice work: *"voice agent is fixed"*. The last open gate — *Alex does not answer
its own voice* — is now ticked on their live confirmation, and the remaining duplicate path was closed
by ChatGPT (the user calls the model **Astra 6.1**) before the handover. **The voice code is frozen on
purpose:** it works, it has a written handover note in `VOICE_AGENT_NOTES.md`, and it should not be
reworked while the rest of the plan is in flight.

**What Astra 6.1 changed.** The per-message speaker button was the last place a second voice could
come from: `SpeakMessageButton` → `tts.ts` synthesised the reply into a browser `Audio` element, so a
replay was a second speaker next to the server's `say`. `tts.ts` now asks `/v1/speech/tts/health`
first; on macOS Face answers `{"available": true, "voice_id": "Samantha", "native_alex": true}`, and
from then on replay POSTs `/v1/alex/voice/say`, follows it with `/v1/alex/voice/status` every 250 ms,
and stops with `/v1/alex/voice/stop` — which calls `voice.barge_in(local_only=True)`, so the UI can
cancel its own replay without killing a line another process owns. Browser audio remains the path for
a server that is not Alex, but not for Face. The working tree's timestamps show the edit:
`frontend/src/lib/tts.ts` and `alex/face/voice.py` at 00:28:58, `tts.test.ts` at 00:29, the static
bundle rebuilt at 00:29, and Face restarted at 00:30 (pid 36353).

**Checked here, not taken on trust:** `/v1/speech/tts/health` → `{"available":true,"voice_id":"Samantha","native_alex":true}`;
`/v1/alex/voice/status` → `speaking: false`, `queued: 0`, `spoken: 9`, one `last` line,
`system_speaking: false`; `frontend/src/lib/tts.test.ts` → **18 passed**, seven of them the new
native-replay paths (no browser `Audio`, no `synthesize`, health detection awaited, no browser fallback
when health fails, repeated clicks collapsed, an in-flight stop ordered before the next message, and
silence when the server declines during an automatic reply). **Not checked:** I did not hear the
audio; the by-ear half of the gate is the user's confirmation. The microphone-only rows — 4.2's ten
turns, 4.6's wake firing, and the spoken gate lines — stay open because this fix did not cover them.

**Written down for the next upgrade.** `VOICE_AGENT_NOTES.md` records the invariants (one `say` per
machine, replay never opens a browser audio path on Face, silence rejected by energy + Whisper flags +
artifact filter, a 10 s default mic turn, cross-process state in `Storage/run/`, stops are local), the
files involved, and the tests that must stay green — so a future model upgrade can change the assistant
without re-introducing the two voices, the self-talk, or the dead Face registration fixed this week.

## Understanding before acting — and done only when verified, 2026-11-18

**The three screenshots were one line of code.** `server/routes.py` owned a play shortcut that ran
*before* Alex's dialogue: it opened `youtube.com/results?search_query=<the whole sentence>` and replied
`"Playing " + song.title() + " on YouTube"` without ever starting a video. That is why
"I want you to play attention by Charlie Puth on YouTube." became a search for the instruction itself
(`/results?search_query=i want you to play attention by charlie puth on youtube.`), "Play it on
YouTube." became `/results?search_query=it on youtube`, and the answer said "Playing…" over a page of
thumbnails. Two smaller causes sat behind it: `classify.py` did not accept "I want you to play …" at
all, so the utterance never reached the executor, and the quick-answer prompt contained the sentence
"You cannot perform actions", which is exactly what produced "I cannot check your inventory".

**Playback now does what it says.** The Face route calls `executor.play_song` on the *subject* —
wrappers ("I want you to", "can you", "please") and a trailing "on YouTube" are stripped — and builds
its reply from the player's verified title, not from the request. "Play it" is no longer intercepted by
the route; it flows to the dialogue, where `_resolve_song_reference` uses the song the thread
remembers. A bare name after playback ("Charlie Puth.") is treated as naming the artist and is played,
instead of being answered with a biography. Live: the right video played and the reply quoted its real
title; "Play it on YouTube." restarted that same tab instead of searching for the word "it".

**A search instruction is understood before it is executed.** New `alex/web.py` parses the request —
`understand_search_request("google about harry potter series on chrome")` returns
`{query: "harry potter series", engine: "google"}` and returns `None` for a genuine question like "what
is the harry potter series?" — opens Chrome on `google.com/search?q=harry+potter+series`, collects
result pages, reads the top two, and summarises them with `[n]` citations through the local gateway
(extractive fallback when the gateway is down). One thing had to be faced rather than pretended:
Google answers a plain HTTP client with a **JavaScript shell** — 93 KB, zero `<h3>`, zero `/url?q=`
links, and no result text — so server-side discovery uses Bing's server-rendered HTML (10 `b_algo`
results, real URLs decoded from its `u=a1…` redirect) while the visible tab stays the Google search the
user asked for. Live, end to end through `:8000`: Chrome showed `google.com/search?q=harry+potter+series`
and the reply was a real summary of the Wikipedia book page and the HBO series page, with citations. A
run whose pages could not be read answered "I opened the search for 'harry potter series' but could not
read any result page, so I have nothing to summarise from." with `verified: false` — the honest branch,
not a guess.

**"Done" now needs a second opinion.** `_run_task` called `complete_task(verified=True)` after any
non-trivial Hermes reply, so the worker graded its own homework. `verify_completion()` now runs a
separate short Hermes turn on `<task_id>-verify` that must answer `VERIFIED:` or `NOT VERIFIED:` after
inspecting the artifacts and state; an unverified result is retried once and then closed as `failed`
with a `verification` event, never `done`. The play reflex reports the player's own `verified` flag
instead of asserting success. `task_started` was removed from `speech_policy.ALLOWED_EVENTS`, so a
dispatched task is silent until it is verified done, blocked, needs approval, or fails. The single
interim chat line ("On it: … I'll tell you when it's finished.") is kept on purpose: it is one
acknowledgement, not progress chatter.

**Conversation context and the register are recorded, not implied.** `alex/threads.py` keeps one JSON
file per conversation (`Storage/conversations/<thread_id>.json`, every turn dated, `_active.json`
mapping session → thread); a thread idle under two hours is still the current conversation, and after
30 days untouched the JSON is discarded while its distilled short-term (skill + procedure) and
long-term (summary, artifacts) rows stay in SQLite. `alex/matrix/tasks.py` gives every task a register
row with its collaterals, exported at `GET /api/tasks/register.csv` and `GET /api/tasks/register`, and
`DELETE /api/tasks/register/{task_id}` removes a task's own folder and files without touching a shared
parent.

**Checked here, not taken on trust.** `tests/alex` + `tests/server/test_routes.py` → **253 passed**, the
single failure being the pre-existing `test_write_text_pdf_creates_a_readable_pdf` (needs `pdfinfo`,
not installed). New coverage: `test_web_research.py` (5 — subject extraction, question rejection,
search-then-read, unreadable-pages-not-verified, dialogue wiring), `test_completion_evidence.py` (bogus
"done" steered once; an unverified verdict never produces `verified=True`; the acknowledgement still
precedes the network probe), `test_play_route.py` (3), and the updated `test_play_song_execution.py`.
`tests/server` as a whole still has **9 pre-existing failures**, all `ModuleNotFoundError:
openjarvis_rust`; they are not caused by these edits and were not fixed here. The four smoke tasks and
five smoke threads created by today's live checks were deleted through the register endpoint.

**Not checked, and not claimed:** no multi-minute Hermes task was run through the new verification gate
(its retry/fail paths are unit-tested only); the desktop UI was not clicked through, so the reply text
was read from the API rather than the window; no audio was heard. The single acknowledgement line is a
deliberate choice the user may still want removed.
