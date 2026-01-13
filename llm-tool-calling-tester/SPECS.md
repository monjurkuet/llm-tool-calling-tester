# LLM Tool Calling Tester - Technical Specifications

## Overview

This tool tests local LLM models for their tool calling capabilities, which are essential for autonomous research agents. It provides scored recommendations based on 5 test scenarios.

## Architecture

### Project Structure

```
llm-tool-calling-tester/
├── src/
│   └── llm_tool_calling_tester/
│       ├── __init__.py       # Package exports
│       ├── config.py         # Configuration constants
│       ├── main.py           # CLI and test orchestration
│       ├── models.py         # Pydantic data models
│       ├── tester.py         # Test execution logic
│       └── tools.py          # Test tool definitions
├── output/                   # Test reports
├── .venv/                    # Virtual environment
├── requirements.txt          # Dependencies
└── README.md                # User documentation
```

## Components

### 1. Models (`models.py`)

**Data Models:**
- `TestStatus`: Enum for test results (PASSED, FAILED, ERROR, SKIPPED)
- `TestResult`: Individual test outcome with latency and error details
- `ModelTestResults`: Complete test results for a model with scoring
- `ToolDefinition`: Schema for function calling tools
- `ToolCall`: Schema for tool call invocations
- `ChatMessage`: Chat completion message format
- `ChatCompletionRequest`: OpenAI-compatible API request format
- `TestSummary`: High-level test statistics
- `FullReport`: Complete test report with metadata

### 2. Tester (`tester.py`)

**ModelTester Class:**
- `chat_completion()`: Execute chat completion requests with retries
- `_stream_response()`: Handle streaming responses
- `test_basic_tool_calling()`: Test if model can call tools
- `test_tool_output_reasoning()`: Test if model can process tool results
- `test_multi_tool_calling()`: Test if model can call multiple tools
- `test_json_mode()`: Test if model produces valid JSON
- `test_streaming_tool_calls()`: Test if model supports streaming tool calls
- `run_all_tests()`: Execute all 5 tests sequentially

### 3. Main (`main.py`)

**ModelTestRunner Class:**
- `fetch_models()`: Get available models from API
- `filter_models()`: Filter models by pattern, excludes GPT models
- `calculate_score()`: Calculate weighted score based on test results
- `get_recommendation()`: Map score to recommendation category
- `test_model()`: Execute tests for a single model
- `run_tests()`: Test all filtered models
- `generate_summary()`: Aggregate test statistics
- `print_console_summary()`: Display formatted results
- `save_json_report()`: Persist detailed JSON report

### 4. Tools (`tools.py`)

**Test Tools:**
- `WEATHER_TOOL`: Get weather for a city
- `CALCULATOR_TOOL`: Perform math calculations
- `SEARCH_TOOL`: Search the web
- `get_test_tools()`: Return all test tools
- `get_mock_tool_response()`: Provide mock responses for tools

### 5. Config (`config.py`)

**Configuration:**
- API endpoints and timeouts
- Retry and rate limiting settings
- Database connection settings (unused)
- Test weights and thresholds
- Output directory

## Test Scenarios

### 1. Basic Tool Calling
Tests if the model can recognize when to call a tool and generate proper tool call format.

**Input:** User asks for weather in Tokyo
**Expected:** Model returns `tool_calls` with `get_weather` function

### 2. Tool Output Reasoning
Tests if the model can process tool output and generate a natural language response.

**Input:** Model receives tool response with weather data
**Expected:** Model generates natural language summary of weather

### 3. Multi-Tool Calling
Tests if the model can call multiple tools in a single response.

**Input:** User asks for weather AND calculation
**Expected:** Model returns 2+ tool calls

### 4. JSON Mode
Tests if the model can produce valid JSON with specific structure.

**Input:** User requests JSON with name, age, city fields
**Expected:** Valid JSON with all required fields

### 5. Streaming Tool Calls
Tests if the model supports streaming tool call responses.

**Input:** Same as basic tool calling but with `stream: true`
**Expected:** Tool calls appear in stream chunks

## Scoring System

**Weights:**
- Tool output reasoning: 35%
- Basic tool calling: 25%
- Multi-tool calling: 25%
- JSON mode: 10%
- Streaming tool calls: 5%

**Thresholds:**
- Recommended: ≥90%
- Partial Support: ≥50%
- No Tool Calling: <50%

## API Compatibility

The tool expects an OpenAI-compatible API at `/v1/chat/completions` with:
- Chat completions endpoint
- Tool calling support (`tools`, `tool_choice` parameters)
- Streaming support (`stream: true` parameter)
- Standard response format with `choices`, `message`, `tool_calls`

## Error Handling

- **Timeouts:** Retry with exponential backoff (up to MAX_RETRIES)
- **Rate Limits (429):** Mark as FAILED
- **Model Not Supported:** Mark as SKIPPED
- **Other Errors:** Mark as ERROR with details

## Dependencies

- `httpx==0.27.0`: Async HTTP client
- `pydantic==2.7.0`: Data validation
- `python-dateutil==2.9.0`: Date utilities
- `tqdm==4.66.0`: Progress bars

## Environment Variables

- `MODEL_TESTER_API_URL`: API base URL (default: http://localhost:8317/v1)
- `MODEL_TESTER_TIMEOUT`: Request timeout in seconds (default: 30)
- `MODEL_TESTER_MAX_WORKERS`: Max parallel workers (default: 5)
- `MODEL_TESTER_DB_*`: Database settings (unused, legacy)

## Output Format

### JSON Report Structure

```json
{
  "summary": {
    "timestamp": "ISO-8601",
    "api_endpoint": "http://localhost:8317/v1",
    "total_models": 50,
    "tested_models": 45,
    "recommended": ["model1", "model2"],
    "partial_support": ["model3"],
    "no_tool_calling": ["model4"],
    "test_statistics": {...}
  },
  "results": [
    {
      "model_id": "model1",
      "owned_by": "provider",
      "tests": {
        "basic_tool_calling": {...},
        ...
      },
      "overall_score": 95.0,
      "recommendation": "recommended",
      "total_latency_ms": 15000
    }
  ],
  "metadata": {...}
}
```

## Performance Characteristics

- **Sequential Testing:** Models tested one at a time (not parallel)
- **Timeout:** 30 seconds per request
- **Retries:** Up to 2 retries with exponential backoff
- **Typical Duration:** ~8-15 minutes for 50 models (full mode)

## Extensibility

To add new tests:
1. Add test method to `ModelTester` class in `tester.py`
2. Add test to `run_all_tests()` method
3. Add weight to `AUTONOMOUS_AGENT_WEIGHTS` in `config.py`
4. Update test display in `print_console_summary()`
