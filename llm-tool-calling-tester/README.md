# LLM Tool Calling Tester

Tests local LLM models for tool calling capabilities required by autonomous research agents.

## Features

- **5 Test Scenarios**:
  - Basic tool calling
  - Tool output reasoning
  - Multi-tool calling
  - JSON mode reliability
  - Streaming tool calls

- **Smart Recommendations**:
  - Recommended (90-100%): All capabilities for autonomous agent
  - Partial Support (50-89%): Some capabilities
  - No Tool Calling (0-49%): Lacks tool calling

- **Output**:
  - Console summary with model categorization
  - JSON report with detailed test results

## Installation

```bash
# Create virtual environment
cd llm-tool-calling-tester
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Quick Test (Basic Tool Calling Only)
```bash
python -m llm_tool_calling_tester.main --quick
```

### Full Test (All 5 Capabilities)
```bash
python -m llm_tool_calling_tester.main
```

### Test Specific Models
```bash
# Only deepseek models
python -m llm_tool_calling_tester.main --filter "deepseek"

# Only qwen models
python -m llm_tool_calling_tester.main --filter "qwen"

# Single model
python -m llm_tool_calling_tester.main --filter "^qwen3-max$"
```

### Custom API Endpoint
```bash
python -m llm_tool_calling_tester.main --api-url http://localhost:8080/v1
```

## CLI Options

| Option | Description | Default |
|--------|-------------|----------|
| `--api-url` | API base URL | http://localhost:8317/v1 |
| `--max-workers` | Max parallel workers | 5 |
| `--filter` | Filter models by regex pattern | None |
| `--quick` | Quick mode (basic test only) | False |

## Example Output

```
================================================================================
MODEL TESTING RESULTS (50 models tested)
================================================================================

✅ Recommended for Autonomous Agent (5 models):
  - qwen3-max (basic:✓, reasoning:✓, multi:✓, json:✓, stream:✓) - Score: 100.0
  - deepseek-v3.2 (basic:✓, reasoning:✓, multi:✓, json:✗, stream:✓) - Score: 90.0
  ...

⚠️ Partial Support (15 models):
  - gemini-2.5-pro (basic:✗, reasoning:✗, multi:✓, json:✗, stream:✓) - Score: 30.0
  ...

❌ No Tool Calling (30 models):
  - raptor-mini (basic:✗, reasoning:✗, multi:✗, json:✗, stream:✗)
  ...

📈 Test Statistics:
  - Total: 50
  - Recommended: 5
  - Partial Support: 15
  - No Tool Calling: 30

💡 Recommendations for Autonomous Research Agent:
  1. qwen3-max (Score: 100.0, Latency: 14842ms)
  2. deepseek-v3.2 (Score: 90.0, Latency: 7758ms)
  3. gemini-2.5-pro (Score: 80.0, Latency: 12500ms)

================================================================================
📄 Full report saved to: output/model_capabilities_20260113_052929.json
```

## Scoring Algorithm

Weights for autonomous research agent suitability:

| Test | Weight | Description |
|------|--------|-------------|
| Basic tool calling | 25% | Can model call tools at all |
| Tool output reasoning | 35% | Can model process tool results |
| Multi-tool calling | 25% | Can model call multiple tools at once |
| JSON mode | 10% | Can model produce valid JSON |
| Streaming tool calls | 5% | Can model stream tool calls |

## Output Files

- **Console Summary**: Printed to terminal
- **JSON Report**: `output/model_capabilities_<timestamp>.json`
  - Summary statistics
  - Per-model test results with latencies
  - Test metadata (API URL, weights, etc.)

## Notes

- Models with HTTP 429 rate limit errors are marked as FAILED
- Models with "model_not_supported" errors are skipped
- Test duration: ~8-15 minutes for 50 models (full mode)
