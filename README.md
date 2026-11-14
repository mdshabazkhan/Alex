# Project Alex (Azarath v3)
### The Trinity Architecture: Jarvis (Face & UI) × Matrix (Supervisor & Gateway) × Hermes (Complex Worker)

Project Alex is an autonomous operating system companion for Apple Silicon macOS, engineered specifically for a 16 GB unified memory budget with zero memory pressure, token waste, or mid-task disruptions.

---

## 1. The Trinity Roles

| Component | Responsibility | Executing Actions? |
|---|---|---|
| **Jarvis** | The Face and Interactive UI. Wake word, fast-path deterministic controls (<1s, 0 tokens), active progress bar & percentage, recent tasks dashboard. Speaks **only** for critical updates. | **Yes** (basic Mac actions only) |
| **Matrix** | The Brainstem & Heart. Acts as non-executing observer, guide, doctor, and model gateway (Port 8700). Strips secrets, enforces guardrails, pins sticky gateway sessions (no mid-task switching), logs telemetry into `ledger.db`, exports Excel reports. | **No** (never directly actuates) |
| **Hermes** | The Heavy Worker. Executes complex autonomous tasks: web research, browser automation via dedicated Chrome profile, coding, multi-step subagents. Routes all model calls through Matrix. | **Yes** (complex tasks only) |

---

## 2. Directory Layout & Designated Storage

```
Friday/ (Alex Root)
├── Alex_Safety_Guardrails.md      # Human-editable master safety guardrails
├── docker-compose.yml             # Docker gateway container definitions
├── config/
│   ├── guardrails.yaml            # Machine-enforced safety rules
│   ├── profiles.yaml              # Gateway routes, budgets & sticky session policy
│   ├── reflexes.yaml              # Instant fast-path actions (<1s, 0 tokens)
│   └── settings.yaml              # System storage and voice filter settings
├── matrix/
│   ├── api.py                     # FastAPI supervisor on 127.0.0.1:8700
│   ├── gateway.py                 # Sticky session OpenAI-compatible gateway (/v1)
│   ├── policy.py                  # Guardrails engine (deny > approve > notify > allow)
│   ├── store.py                   # SQLite WAL ledger (ledger.db) & tasks
│   ├── doctor.py                  # Error classification & steering advice
│   └── reports.py                 # 6-sheet Excel report generator
├── jarvis/
│   ├── main.py                    # Voice/CLI intake loop
│   ├── ui.py                      # Active dashboard with live progress bar & recent tasks
│   ├── reflex.py                  # Fast-path matcher (Wi-Fi, volume, apps, dark mode)
│   ├── voice_filter.py            # Filters audio: only speaks on critical events
│   └── matrix_client.py           # Async HTTP client to Matrix
├── hermes/
│   ├── SOUL.md                    # Agent persona ("sir", STEP n/N format)
│   ├── config.yaml                # Pinned to Matrix gateway (127.0.0.1:8700/v1)
│   └── plugins/
│       └── matrix_bridge.py       # pre_tool_call policy checks & post_tool_call auditing
├── storage/                       # Designated data storage
│   ├── workspace/                 # Agent sandboxed workspace
│   ├── data/                      # Persistent ledger.db
│   ├── reports/                   # Excel telemetry workbooks
│   └── logs/                      # Service logs
├── scripts/
│   ├── alex-boot.sh               # Boot script: verifies Docker & services
│   └── com.azarath.alex.boot.plist# macOS LaunchAgent for boot startup
└── evals/
    ├── test_alex_pipeline.py      # Acceptance test suite
    └── test_jarvis_ui_integration.py # Integration test suite
```

---

## 3. Quick Start

### 1. Launch Matrix Supervision API & Gateway (Port 8700)
```bash
./venv/bin/python3 -m matrix.api
```

### 2. Launch Jarvis Interactive Dashboard & Voice Console
```bash
# Terminal 1: Live UI dashboard with active progress bar and recent tasks
./venv/bin/python3 -m jarvis.ui

# Terminal 2: Interactive command console
./venv/bin/python3 -m jarvis.main
```

### 3. Run Acceptance Test Suite
```bash
./venv/bin/python3 -m unittest evals/test_alex_pipeline.py evals/test_jarvis_ui_integration.py
```

### 4. System Boot Setup (macOS)
To ensure Docker and Alex start on system boot:
```bash
cp scripts/com.azarath.alex.boot.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.azarath.alex.boot.plist
```
