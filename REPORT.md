# Alex merge — progress report

_Last updated: 2026-11-14, unsupervised session. Read this top box first._

**Resume:** [jump to Resume](#resume-here). **Everything below is already committed.**

---

## Status at a glance

| Phase | Progress | State | Last commit |
|---|---|---|---|
| 0 Freeze & baseline | 4 / 4 | **Done** | `084274eb` |
| 1 One repo, one app | 8 / 8 | **Done** | `05b06464` |
| 2 Ledger truth | 7 / 7 | **Done** (+3 bug fixes) | `1406106a`, `aec2f506`, `d9e5e9b9` |
| 3 Face ↔ Trinity wiring | 3 / 8 | **In progress** | `2960a82f` |
| 4 Voice | 0 / 7 | Not started | — |
| 5 Hermes becomes real | 0 / 8 | Not started | — |
| 6 Memory & personality | 0 / 6 | Not started | — |
| 7 Logs, dashboard & report | 0 / 5 | Not started | — |
| 8 Hardening & acceptance | 0 / 4 | Not started | — |

Work tree: clean for `src/openjarvis/alex`, `config/`, `docs/`, `scripts/`.
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
  bridge *blocks* approve-required tools rather than running them; and a late worker can
  no longer overwrite your decision (`LOCK-001`/`LOCK-002`).
- **Real conversation.** `classify.py` routes every turn deterministically
  (31/31 labelled utterances, including the false-positive traps). `dialogue.py` runs
  verified reflex actions, answers through the gateway, and slot-fills complex requests.
  The hardcoded essay, the "₹7,850" gold rate and "Understood, Master Khan" are gone.
- **Answers survive broken gateways.** Hosted gateways currently return 401 (no keys in
  the native process); the gateway now falls back to local Ollama, so Alex still answers.

## Bugs found and fixed this session

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

## Known gaps (deliberate, tracked in CHECKLIST)

| Gap | Why | Where |
|---|---|---|
| 3.2 real hardware action not executed | toggling Bluetooth/Wi-Fi while you sleep changes your machine | you: ask "turn off bluetooth" |
| Approve does not wake a parked worker | no worker waits at the gate yet | 3.4 / 5.5 |
| 3.4 milestones, 3.6 speech wiring, 3.7 queue names, 3.8 Tauri close | next Phase 3 items | Phase 3 |
| Approval-required tools are blocked, not paused | fail-closed until parking exists | 5.5 |
| UI does not render `evidence` or call real clear | Logs page rewrite | 7.1 / 7.2 |
| Voice/STT/TTS untouched | needs you at the machine to verify | Phase 4 |

---

## Verification performed (commands actually run)

- Phase 0 — one `:8000` owner; 10/10 DB backups `integrity_check = ok`; port map; blueprint commit.
- Phase 1 — import from `/tmp`; 24 routes; 10 registry tools + MCP server returns the same 10;
  `alex down` → no listeners; `up` → 3/3 healthy; wheel contains 22 `alex/` entries; grep clean.
- Phase 2 — clear `21 tasks / 61 model_calls` → 0 rows; 7 event types; steps 1..5; approve/
  reject/stop/steer with rule IDs; Doctor row `rate_limit` ×2; `TIMEOUT-001` sweep; 0 running.
- Approval fixes — no worker → `awaiting_worker` and survives `sweep(0)`; worker → `running`;
  `mail.send` → blocked + `awaiting_approval`; finished task → 409; 7/7 lock assertions.
- Phase 3 — 31/31 utterances; spy fallback proves no model call on rule hits; live
  `/api/alex/chat` answers via Ollama (`tokens_in=51, tokens_out=128`); slot question →
  task `T-20261115-29EC00`; `grep 7,850`/`Master Khan` empty.

## Not verified (be sceptical here)

- **No real macOS action executed** (dry-run only) — Bluetooth/Wi-Fi/volume paths are unproven on hardware.
- **No microphone, speaker or Tauri window touched** — Phase 4 is entirely unstarted.
- **No real Hermes run** — the worker is still Matrix's built-in path, not `hermes-agent`.
- **No frontend change** — the Logs page still reads client state only; `evidence` is API-only.

---

## Resume here

1. `openjarvis alex status` → expect three healthy lines. If not: `openjarvis alex up`.
2. `cd ~/.openjarvis/src && git log --oneline -5` → confirm `2960a82f` at the top for Phase 3.
3. Next Phase 3 items, in order: **3.6** wire `speech_policy` to task events (smallest, verifiable),
   **3.4** milestone emission, **3.7** queue naming, **3.8** Tauri close command, then the Phase 3 gate.
4. Ask **"turn off bluetooth"** to close 3.2 on real hardware.
5. Tick `CHECKLIST.md` only when each "Done when" holds; append date + commit. Update this report at
   every phase boundary.
