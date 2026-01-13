from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from enum import Enum


class TestStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"


class TestResult(BaseModel):
    test_name: str
    status: TestStatus
    latency_ms: int = Field(default=0)
    error_message: Optional[str] = None
    details: Optional[dict] = None


class ModelTestResults(BaseModel):
    model_id: str
    owned_by: str
    tests: dict[str, TestResult]
    overall_score: float = Field(ge=0, le=100)
    recommendation: Literal["recommended", "partial_support", "no_tool_calling"]
    total_latency_ms: int
    is_gpt_model: bool = False


class ToolDefinition(BaseModel):
    type: str = "function"
    function: dict


class ToolCall(BaseModel):
    id: str
    type: str = "function"
    function: dict


class ChatMessage(BaseModel):
    role: str
    content: Optional[str] = None
    tool_calls: Optional[list[ToolCall]] = None
    tool_call_id: Optional[str] = None


class ChatCompletionRequest(BaseModel):
    model: str
    messages: list[ChatMessage]
    tools: Optional[list[ToolDefinition]] = None
    tool_choice: Optional[str] = "auto"
    temperature: float = 0.7
    max_tokens: int = 1000
    stream: bool = False


class TestSummary(BaseModel):
    timestamp: str
    api_endpoint: str
    total_models: int
    tested_models: int
    recommended: list[str]
    partial_support: list[str]
    no_tool_calling: list[str]
    gpt_models_summary: dict[str, dict[str, TestResult]]
    test_statistics: dict[str, int]


class FullReport(BaseModel):
    summary: TestSummary
    results: list[ModelTestResults]
    metadata: dict[str, str]
