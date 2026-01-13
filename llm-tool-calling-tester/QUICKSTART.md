# Quick Start Guide

Get the LLM Tool Calling Tester running in 3 steps.

## Step 1: Install Dependencies

```bash
cd llm-tool-calling-tester
source .venv/bin/activate
pip install -r requirements.txt
```

## Step 2: Verify Your API

Make sure your LLM API is running and accessible at `http://localhost:8317/v1` (or use `--api-url`).

## Step 3: Run Tests

```bash
# Quick test (1-2 minutes)
./run.sh --quick

# Full test (8-15 minutes for ~50 models)
./run.sh

# Test specific models
./run.sh --filter "qwen"
```

## Check Results

- **Console**: Summary appears in terminal
- **Detailed Report**: `output/model_capabilities_<timestamp>.json`

## Troubleshooting

**API not reachable?**
```bash
./run.sh --api-url http://your-api-url:port/v1
```

**Timeout errors?**
```bash
export MODEL_TESTER_TIMEOUT=60
./run.sh
```

**See all options:**
```bash
./run.sh --help
```
