# Alex merge — progress report

## Voice overlap repair — 2026-11-18

- Alex now has one native speech path, using **Samantha**. The browser audio fallback cannot start while Alex voice detection is pending or unavailable, so it cannot overlap native speech.
- Repeated speaker presses for the same message are ignored. Stop waits for any in-flight native stop before another message starts, and a queued line is cancelled even if it is waiting for the shared system voice lock.
- Verification: frontend voice suite **18 / 18**, full frontend suite **128 / 128**, and Alex/server suite **250 / 250** passed. A live concurrent playback probe accepted one of two simultaneous requests, observed one `say` process using Samantha, and left no active or queued speech after Stop. Physical-speaker listening was confirmed by the user afterward.

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
| 4 Voice + human delivery | 4 / 10 | **In progress** (4.2/4.6 built, not yet observed live) | `40b96cf5` |
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

---

# Phase 5 — Hermes becomes real (route re-done 2026-11-16)

## Where the checklist actually stands
`CHECKLIST.md` line 40 still reads `| 5 | Hermes becomes real | 4–5 d | 0 / 8 | Not started | — |`
and all eight 5.x boxes are unticked. Nothing in this section is ticked: the 5.1 "Done when"
(one run, ≥3 distinct toolsets, real artifacts) has **not** been observed yet.

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
