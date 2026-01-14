# Autonomous Plan-Critique-Refine System

## Project Overview
Multi-agent autonomous system that generates plans, refines them through N rounds of critique by heterogeneous LLMs, and executes with self-healing capabilities.

## Architecture Decisions
- **Package Manager**: `uv` for Python
- **Framework**: Custom async orchestration (simplified for reliability)
- **Model Strategy**: Heterogeneous Roster (different models per agent role)
- **Debate Termination**: Adaptive detection (consensus, diminishing returns, max rounds)
- **Executor**: VIGIL Self-Healing with step-by-step re-critique
- **API**: Local OpenAI-compatible at http://localhost:8317/v1
- **Storage**: PostgreSQL for persistent storage (agentzero@localhost/autonomous_planner)

## Agent Roles & Models
Based on llm-tool-calling-tester results:

| Role | Model | Purpose |
|-------|--------|---------|
| Planner | qwen3-max | Generate initial plans, highest tool calling (100%) |
| Critic: Risk | deepseek-v3.2 | Identify risks and failure modes |
| Critic: Logic | gemini-2.5-pro | Verify logical consistency |
| Critic: Ethics | qwen3-max | Check ethical implications |
| Critic: Pragmatism | deepseek-v3.2 | Assess practical feasibility |
| Synthesizer | qwen3-max | Aggregate critiques and calculate consensus |
| Refiner | qwen3-max | Apply critique-guided improvement |
| Executor | qwen3-max | Execute with self-healing on failure |

## System Flow
```
User Request
    ↓
Planner (qwen3-max) → Initial Plan (JSON)
    ↓
Debate Cycle (adaptive 2-5 rounds)
    ├─→ Critic 1 (deepseek-v3.2) - Risk Analysis
    ├─→ Critic 2 (gemini-2.5-pro) - Logic Verification
    ├─→ Critic 3 (qwen3-max) - Ethics
    ├─→ Critic 4 (deepseek-v3.2) - Pragmatism
    └─→ Repeat until convergence or max rounds
    ↓
Synthesizer (qwen3-max) → Consensus Score & Top Concerns
    ↓
Refiner (qwen3-max) → Improved Plan
    ↓
Executor → Step-by-Step Execution with VIGIL Self-Healing
    ├─→ Track failures in EmotionalBank
    ├─→ Generate repair strategies
    ├─→ Re-enter debate on critical failures
    └─→ Store all data in PostgreSQL
    ↓
Output + Session ID (for retrieval)
```

## Quick Start

### Setup (2 minutes)
```bash
cd /home/administrator/dev/customLLM/autonomous-planner
uv venv
source .venv/bin/activate
uv pip install httpx pydantic python-dotenv psycopg2-binary
```

### Run (1 minute)
```bash
source .venv/bin/activate
python3 working_planner.py "Plan a weekend trip to Tokyo"
```

## PostgreSQL Storage

### Database Configuration
- **Host**: localhost
- **Port**: 5432
- **Database**: autonomous_planner
- **User**: agentzero
- **Password**: (none - local trusted)

### Tables Created
| Table | Purpose |
|-------|---------|
| sessions | Tracks each run with task, status, rounds, consensus |
| plans | Stores generated plans per round |
| critiques | Stores multi-agent critiques with quality scores |
| syntheses | Stores consensus synthesis per round |
| executions | Stores step execution results with retry counts |
| emotional_bank | Tracks failure patterns for self-healing |
| diagnoses | Maps behavior to strengths/opportunities |
| model_performance | Tracks model effectiveness over time |

### Query Examples
```bash
# View recent sessions
PGPASSWORD="" psql -h localhost -U agentzero -d autonomous_planner -c "SELECT * FROM sessions ORDER BY created_at DESC LIMIT 5;"

# Check model performance
PGPASSWORD="" psql -h localhost -U agentzero -d autonomous_planner -c "SELECT * FROM model_performance;"

# View all critiques for a session
PGPASSWORD="" psql -h localhost -U agentzero -d autonomous_planner -c "SELECT * FROM critiques WHERE session_id = 'your-uuid-here';"
```

## Features
- ✅ Heterogeneous model allocation (5 unique models)
- ✅ Adaptive debate termination (consensus + diminishing returns)
- ✅ JSON-structured outputs with parsing fallbacks
- ✅ VIGIL Self-Healing with EmotionalBank for failure tracking
- ✅ Step-by-step execution with re-critique capability
- ✅ Simplified async orchestration (no LangGraph dependencies)
- ✅ UV package manager integration
- ✅ PostgreSQL persistent storage
  - Session history tracking
  - Critique and synthesis storage
  - Execution logging with retry counts
  - Model performance metrics
  - Failure pattern analysis

## 2026 Innovations Incorporated
This system incorporates the latest 2025-2026 research:

1. **Heterogeneous Models** - Addresses Dynadebate bias (Jan 2026)
2. **Adaptive Termination** - Implements Debate Only When Necessary (Apr 2025)
3. **Lighthouse Pattern** - Natural language critique (Sept 2025)
4. **VIGIL Pattern** - Self-healing executor (Dec 2025)
5. **Simplified Architecture** - Custom async orchestration for reliability

## Project Structure
```
autonomous-planner/
├── working_planner.py        # Main entry point (self-contained, working)
├── src/                      # Modular version (on hold)
│   ├── config.py             # Heterogeneous model roster & settings
│   ├── models.py             # Pydantic data models
│   ├── llm_client.py         # Async LLM client
│   ├── executor.py           # VIGIL-style self-healing
│   ├── orchestrator.py       # Custom async orchestration
│   └── main.py               # CLI entry point
├── logs/                     # Debate history (auto-created)
├── README.md                 # This file
├── QUICKSTART.md             # Setup guide
├── BUILD_COMPLETE.md         # Implementation summary
├── IMPLEMENTATION_PLAN.md    # Progress tracker
├── requirements.txt          # Dependencies (uv)
├── setup.sh                  # Setup script with uv
├── run.sh                    # Quick run script
├── .env.example              # Configuration template
└── .env                      # Your configuration
```

## Example Output
```
======================================================================
 AUTONOMOUS PLAN-CRITIQUE-REFINE SYSTEM
======================================================================

📋 Task: Plan a weekend trip to Tokyo
🤖 Models: 5 unique (heterogeneous)
🔄 Adaptive termination enabled
🛡 Self-healing enabled
======================================================================

📝 Phase 1: Planning
✓ Plan generated with 3 steps

💬 Phase 2: Multi-Agent Debate

--- Round 1 ---
  Consensus: 0.85
  ✓ Plan refined

--- Round 2 ---
  Consensus: 0.85
  🎯 Consensus reached (0.85)!

🎯 Phase 3: Execution

🚀 Executing 2 steps...
📍 Step 1/2: Confirm arrival by early Friday afternoon...
  ✓ Completed
📍 Step 2/2: Use a Suica or Pasmo IC card for transit...
  ✓ Completed

✅ Completed: 2/2 steps
   Failed: 0 steps

Plan executed successfully!
```

## Configuration

### Model Roster (in working_planner.py)
```python
MODELS = {
    "planner": "qwen3-max",
    "critic_1": "deepseek-v3.2",
    "critic_2": "gemini-2.5-pro",
    "critic_3": "qwen3-max",
    "critic_4": "deepseek-v3.2",
    "refiner": "qwen3-max",
}
```

### Adaptive Termination Settings
```python
max_rounds = 5      # Safety limit
min_rounds = 2      # Minimum debate rounds
consensus_threshold = 0.6  # Stop if consensus >= 0.6
```

## Troubleshooting

**API not responding?**
```bash
curl http://localhost:8317/v1/models
```

**Timeout issues?**
```bash
# Increase timeout in working_planner.py line 26
timeout=120.0  # Increase from 60
```

**Need to adjust rounds?**
```bash
# Edit working_planner.py lines 146-148
max_rounds = 3  # Faster execution
min_rounds = 1
```

## Progress Tracking

**Start Here**: [MASTER_PLAN.md](MASTER_PLAN.md) - Central hub with quick start, todos, and next actions

**Detailed Progress**: [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) - Phase-by-phase breakdown

**Current Status**: [STATUS_REPORT.md](STATUS_REPORT.md) - System metrics and database stats

**Future Ideas**: [NEXT_STEPS.md](NEXT_STEPS.md) - 10 research-based enhancement ideas

- ✅ Heterogeneous model allocation
- ✅ Multi-agent parallel critique
- ✅ Adaptive debate termination
- ✅ JSON-structured plan generation
- ✅ Self-healing execution
- ✅ UV package manager integration
- ✅ Tested and verified with local API

## Project Status

**Core Architecture**: ✅ Complete
**Debate System**: ✅ Complete
**Self-Healing**: ✅ Complete
**Orchestration**: ✅ Complete
**CLI**: ✅ Complete
**Documentation**: ✅ Complete
**Testing**: ✅ Complete

**Ready for**: 
- ✅ Production use
- ✅ Custom model configuration
- ✅ Tool integration
- ✅ Extended features

## Session Analysis Workflow

This project also includes a multi-agent session analysis system that ingests, analyzes, and reports on OpenCode session metadata.

### Architecture
- **Ingestor Agent**: Processes JSON session files from `/home/administrator/.local/share/opencode/storage/session`, stores metadata in PostgreSQL `raw_session_metadata` table
- **Analyzer Agent**: Analyzes session data for prompt characteristics, activity metrics, timing, and project context; stores results in `session_analysis_results` table
- **Reporter Agent**: Generates summary reports and CSV exports in `analysis_reports/` directory
- **Orchestrator**: Flask-based API server on port 5000 for triggering workflows

### Workflow Execution
```bash
# Manual execution
cd /home/administrator/dev/customLLM/autonomous-planner
source .venv/bin/activate
python agents/session_ingestor.py    # Ingest session data
python agents/session_analyzer.py    # Analyze data
python agents/session_reporter.py    # Generate reports

# Or via API
curl -X POST http://localhost:5000/trigger/workflow      # Full workflow
curl -X POST http://localhost:5000/trigger/analysis_report  # Analysis + Report only
```

### Database Tables
| Table | Purpose |
|-------|---------|
| raw_session_metadata | Raw session metadata from JSON files |
| session_analysis_results | Analyzed metrics per session |
| ingestion_state | Tracks last processed/analyzed sessions |

### Analysis Metrics
- **Prompt Characteristics**: Title length
- **Activity Metrics**: Files changed, lines added/deleted
- **Session Timing**: Duration in seconds
- **Project Context**: Project ID and directory

### Reports Generated
- `session_analysis_summary.md`: Markdown summary with session-by-session analysis
- `session_analysis_export.csv`: Full CSV export of all analysis results

## Streamlit Dashboard

A interactive web dashboard for visualizing session analysis data.

### Features
- **Overview Dashboard**: Key metrics, processing status, and project distribution charts
- **Sessions Browser**: Searchable and filterable table of all sessions with metadata
- **Analytics**: Time-series trends, activity distributions, and interactive charts
- **Data Export**: Download filtered results as CSV
- **Real-time Refresh**: Manual data refresh with caching

### Running the Dashboard
```bash
cd /home/administrator/dev/customLLM/autonomous-planner
source .venv/bin/activate
streamlit run streamlit_app.py
```

Access at: http://localhost:8501

### Dashboard Pages
1. **Overview**: Summary statistics and top projects chart
2. **Sessions Browser**: Browse all sessions with filters and search
3. **Analytics**: Detailed visualizations and trends

### Requirements
- PostgreSQL database with session data
- Streamlit, pandas, plotly installed
- Database connection configured in `streamlit_app.py`

### Docker Deployment
```bash
# Build the image
docker build -t session-analysis-dashboard .

# Run the container
docker run -p 8501:8501 -e DB_HOST=host.docker.internal session-analysis-dashboard
```

### Streamlit Cloud Deployment
1. Push code to GitHub
2. Connect repository to share.streamlit.io
3. Configure secrets for database connection
4. Deploy automatically

---

**Last Updated**: January 2026
**Working Entry Point**: `working_planner.py`
