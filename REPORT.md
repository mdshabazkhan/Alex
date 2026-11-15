# Alex merge — progress report

_Last updated: 2026-11-14 (unsupervised session). Read this top box first._

**Resume:** [jump to Resume](#resume-here). **Everything below is committed.**

---

## Status at a glance

| Phase | Progress | State | Last commit |
|---|---|---|---|
| 0 Freeze & baseline | 4 / 4 | **Done** | `084274eb` |
| 1 One repo, one app | 8 / 8 | **Done** | `05b06464` |
| 2 Ledger truth | 7 / 7 | **Done** (+3 bug fixes) | `1406106a`, `aec2f506`, `d9e5e9b9` |
| 3 Face ↔ Trinity wiring | 6 / 8 | **In progress** | `6e7f3a56` |
| 4 Voice + human delivery | 3 / 10 | **In progress** | `3630cfad` |
| 5 Hermes becomes real | 0 / 8 | Not started | — |
| 6 Memory: short-term ⇄ long-term | 0 / 14 | Not started | — |
| 7 Logs, dashboard & report | 0 / 5 | Not started | — |
| 8 Hardening & acceptance | 0 / 5 | Not started | — |

Work tree: clean for `src/openjarvis/alex`, `config/`, `docs/`.
Services: Face `:8000`, Matrix `:8700`, Hermes `:8642` — all `/health` green.

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

Your two-layer model is now designed in `docs/BLUEPRINT.md` **§A7** and built as **Phase 6 (14 steps)**.
Nothing is implemented yet — this is the plan, the blueprint and the storage tree.

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
