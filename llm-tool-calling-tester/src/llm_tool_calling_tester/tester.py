import json
import logging
import asyncio
import time
from typing import AsyncGenerator, Optional
import httpx
from .models import ChatCompletionRequest, ChatMessage, TestStatus, TestResult
from .tools import get_test_tools, get_mock_tool_response
from .config import API_BASE_URL, TIMEOUT_SECONDS, MAX_RETRIES, RETRY_DELAY

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ModelTester:
    def __init__(self, api_url: str = API_BASE_URL):
        self.api_url = api_url.rstrip("/")
        self.timeout = httpx.Timeout(TIMEOUT_SECONDS)

    async def chat_completion(
        self, request: ChatCompletionRequest, stream: bool = False
    ) -> Optional[dict]:
        url = f"{self.api_url}/chat/completions"
        headers = {"Content-Type": "application/json"}

        for attempt in range(MAX_RETRIES):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    if stream:
                        return await self._stream_response(
                            client, url, headers, request
                        )
                    else:
                        response = await client.post(
                            url,
                            headers=headers,
                            json=request.model_dump(exclude_none=True),
                        )
                        response.raise_for_status()
                        return response.json()
            except httpx.TimeoutException:
                logger.warning(f"Timeout attempt {attempt + 1}/{MAX_RETRIES}")
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAY * (2**attempt))
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Request failed: {error_msg}")
                if (
                    "model_not_supported" in error_msg.lower()
                    or "The requested model is not supported" in error_msg
                ):
                    return {"error": {"message": "Model not supported"}}
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAY * (2**attempt))
                else:
                    raise
        return None

    async def _stream_response(
        self,
        client: httpx.AsyncClient,
        url: str,
        headers: dict,
        request: ChatCompletionRequest,
    ) -> Optional[dict]:
        async with client.stream(
            "POST", url, headers=headers, json=request.model_dump(exclude_none=True)
        ) as response:
            response.raise_for_status()
            chunks = []
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        chunks.append(chunk)
                    except json.JSONDecodeError:
                        continue
            return {"chunks": chunks}

    async def test_basic_tool_calling(self, model: str) -> TestResult:
        start_time = time.time()
        try:
            request = ChatCompletionRequest(
                model=model,
                messages=[
                    ChatMessage(role="user", content="What's the weather in Tokyo?")
                ],
                tools=get_test_tools(),
                tool_choice="auto",
            )
            response = await self.chat_completion(request)

            if not response:
                return TestResult(
                    test_name="basic_tool_calling",
                    status=TestStatus.ERROR,
                    latency_ms=int((time.time() - start_time) * 1000),
                    error_message="No response from API",
                )

            if "error" in response:
                error_detail = response.get("error", {}).get("message", "Unknown error")
                return TestResult(
                    test_name="basic_tool_calling",
                    status=TestStatus.SKIPPED,
                    latency_ms=int((time.time() - start_time) * 1000),
                    error_message=f"Model not available: {error_detail}",
                )

            choices = response.get("choices", [])
            if not choices:
                return TestResult(
                    test_name="basic_tool_calling",
                    status=TestStatus.FAILED,
                    latency_ms=int((time.time() - start_time) * 1000),
                    error_message="No choices in response",
                )

            message = choices[0].get("message", {})
            tool_calls = message.get("tool_calls", [])

            if not tool_calls:
                return TestResult(
                    test_name="basic_tool_calling",
                    status=TestStatus.FAILED,
                    latency_ms=int((time.time() - start_time) * 1000),
                    error_message="No tool_calls in response",
                )

            logger.info(f"✓ {model}: Basic tool calling - PASSED")
            return TestResult(
                test_name="basic_tool_calling",
                status=TestStatus.PASSED,
                latency_ms=int((time.time() - start_time) * 1000),
                details={"tool_calls_count": len(tool_calls)},
            )

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.error(f"✗ {model}: Basic tool calling - FAILED: Rate limited")
                return TestResult(
                    test_name="basic_tool_calling",
                    status=TestStatus.FAILED,
                    latency_ms=int((time.time() - start_time) * 1000),
                    error_message="Rate limited by API",
                )
            logger.error(f"✗ {model}: Basic tool calling - FAILED: {str(e)}")
            return TestResult(
                test_name="basic_tool_calling",
                status=TestStatus.ERROR,
                latency_ms=int((time.time() - start_time) * 1000),
                error_message=str(e),
            )
        except Exception as e:
            logger.error(f"✗ {model}: Basic tool calling - FAILED: {str(e)}")
            return TestResult(
                test_name="basic_tool_calling",
                status=TestStatus.ERROR,
                latency_ms=int((time.time() - start_time) * 1000),
                error_message=str(e),
            )

    async def test_tool_output_reasoning(self, model: str) -> TestResult:
        start_time = time.time()
        try:
            request = ChatCompletionRequest(
                model=model,
                messages=[
                    ChatMessage(role="user", content="What's the weather in Tokyo?")
                ],
                tools=get_test_tools(),
                tool_choice="auto",
            )
            response = await self.chat_completion(request)

            if not response:
                return TestResult(
                    test_name="tool_output_reasoning",
                    status=TestStatus.ERROR,
                    latency_ms=int((time.time() - start_time) * 1000),
                    error_message="No response from API",
                )

            choices = response.get("choices", [])
            if not choices:
                return TestResult(
                    test_name="tool_output_reasoning",
                    status=TestStatus.FAILED,
                    latency_ms=int((time.time() - start_time) * 1000),
                    error_message="No choices in response",
                )

            tool_calls = choices[0].get("message", {}).get("tool_calls", [])
            if not tool_calls:
                return TestResult(
                    test_name="tool_output_reasoning",
                    status=TestStatus.FAILED,
                    latency_ms=int((time.time() - start_time) * 1000),
                    error_message="No tool_calls in first response",
                )

            tool_call = tool_calls[0]
            tool_name = tool_call.get("function", {}).get("name")
            tool_id = tool_call.get("id")

            mock_response = get_mock_tool_response(tool_name)

            followup_request = ChatCompletionRequest(
                model=model,
                messages=[
                    ChatMessage(role="user", content="What's the weather in Tokyo?"),
                    ChatMessage(role="assistant", content=None, tool_calls=[tool_call]),
                    ChatMessage(
                        role="tool",
                        content=json.dumps(mock_response),
                        tool_call_id=tool_id,
                    ),
                ],
                tools=get_test_tools(),
                tool_choice="auto",
            )

            followup_response = await self.chat_completion(followup_request)

            if not followup_response:
                return TestResult(
                    test_name="tool_output_reasoning",
                    status=TestStatus.FAILED,
                    latency_ms=int((time.time() - start_time) * 1000),
                    error_message="No followup response",
                )

            final_message = followup_response.get("choices", [{}])[0].get("message", {})
            final_content = final_message.get("content", "")

            if not final_content:
                return TestResult(
                    test_name="tool_output_reasoning",
                    status=TestStatus.FAILED,
                    latency_ms=int((time.time() - start_time) * 1000),
                    error_message="No final content after tool output",
                )

            logger.info(f"✓ {model}: Tool output reasoning - PASSED")
            return TestResult(
                test_name="tool_output_reasoning",
                status=TestStatus.PASSED,
                latency_ms=int((time.time() - start_time) * 1000),
                details={"final_content_length": len(final_content)},
            )

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.error(f"✗ {model}: Tool output reasoning - FAILED: Rate limited")
                return TestResult(
                    test_name="tool_output_reasoning",
                    status=TestStatus.FAILED,
                    latency_ms=int((time.time() - start_time) * 1000),
                    error_message="Rate limited by API",
                )
            logger.error(f"✗ {model}: Tool output reasoning - FAILED: {str(e)}")
            return TestResult(
                test_name="tool_output_reasoning",
                status=TestStatus.ERROR,
                latency_ms=int((time.time() - start_time) * 1000),
                error_message=str(e),
            )
        except Exception as e:
            logger.error(f"✗ {model}: Tool output reasoning - FAILED: {str(e)}")
            return TestResult(
                test_name="tool_output_reasoning",
                status=TestStatus.ERROR,
                latency_ms=int((time.time() - start_time) * 1000),
                error_message=str(e),
            )

    async def test_multi_tool_calling(self, model: str) -> TestResult:
        start_time = time.time()
        try:
            request = ChatCompletionRequest(
                model=model,
                messages=[
                    ChatMessage(
                        role="user",
                        content="Check the weather in Tokyo and calculate 15 + 27",
                    )
                ],
                tools=get_test_tools(),
                tool_choice="auto",
            )
            response = await self.chat_completion(request)

            if not response:
                return TestResult(
                    test_name="multi_tool_calling",
                    status=TestStatus.ERROR,
                    latency_ms=int((time.time() - start_time) * 1000),
                    error_message="No response from API",
                )

            tool_calls = (
                response.get("choices", [{}])[0]
                .get("message", {})
                .get("tool_calls", [])
            )

            if len(tool_calls) < 2:
                return TestResult(
                    test_name="multi_tool_calling",
                    status=TestStatus.FAILED,
                    latency_ms=int((time.time() - start_time) * 1000),
                    error_message=f"Expected at least 2 tool_calls, got {len(tool_calls)}",
                )

            tool_names = [tc.get("function", {}).get("name") for tc in tool_calls]
            if "get_weather" not in tool_names or "calculate" not in tool_names:
                return TestResult(
                    test_name="multi_tool_calling",
                    status=TestStatus.FAILED,
                    latency_ms=int((time.time() - start_time) * 1000),
                    error_message=f"Expected get_weather and calculate, got {tool_names}",
                )

            logger.info(f"✓ {model}: Multi-tool calling - PASSED")
            return TestResult(
                test_name="multi_tool_calling",
                status=TestStatus.PASSED,
                latency_ms=int((time.time() - start_time) * 1000),
                details={"tool_calls_count": len(tool_calls), "tool_names": tool_names},
            )

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.error(f"✗ {model}: Multi-tool calling - FAILED: Rate limited")
                return TestResult(
                    test_name="multi_tool_calling",
                    status=TestStatus.FAILED,
                    latency_ms=int((time.time() - start_time) * 1000),
                    error_message="Rate limited by API",
                )
            logger.error(f"✗ {model}: Multi-tool calling - FAILED: {str(e)}")
            return TestResult(
                test_name="multi_tool_calling",
                status=TestStatus.ERROR,
                latency_ms=int((time.time() - start_time) * 1000),
                error_message=str(e),
            )
        except Exception as e:
            logger.error(f"✗ {model}: Multi-tool calling - FAILED: {str(e)}")
            return TestResult(
                test_name="multi_tool_calling",
                status=TestStatus.ERROR,
                latency_ms=int((time.time() - start_time) * 1000),
                error_message=str(e),
            )

    async def test_json_mode(self, model: str) -> TestResult:
        start_time = time.time()
        try:
            request = ChatCompletionRequest(
                model=model,
                messages=[
                    ChatMessage(
                        role="user",
                        content="Return a JSON object with 'name', 'age', and 'city' fields for a fictional person",
                    )
                ],
            )

            response = await self.chat_completion(request)

            if not response:
                return TestResult(
                    test_name="json_mode",
                    status=TestStatus.ERROR,
                    latency_ms=int((time.time() - start_time) * 1000),
                    error_message="No response from API",
                )

            content = (
                response.get("choices", [{}])[0].get("message", {}).get("content", "")
            )

            if not content:
                return TestResult(
                    test_name="json_mode",
                    status=TestStatus.FAILED,
                    latency_ms=int((time.time() - start_time) * 1000),
                    error_message="No content in response",
                )

            try:
                json_obj = json.loads(content)
                required_fields = {"name", "age", "city"}
                if not required_fields.issubset(json_obj.keys()):
                    return TestResult(
                        test_name="json_mode",
                        status=TestStatus.FAILED,
                        latency_ms=int((time.time() - start_time) * 1000),
                        error_message=f"Missing fields: {required_fields - set(json_obj.keys())}",
                    )

                logger.info(f"✓ {model}: JSON mode - PASSED")
                return TestResult(
                    test_name="json_mode",
                    status=TestStatus.PASSED,
                    latency_ms=int((time.time() - start_time) * 1000),
                    details={"json_keys": list(json_obj.keys())},
                )
            except json.JSONDecodeError:
                return TestResult(
                    test_name="json_mode",
                    status=TestStatus.FAILED,
                    latency_ms=int((time.time() - start_time) * 1000),
                    error_message="Invalid JSON in response",
                )

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.error(f"✗ {model}: JSON mode - FAILED: Rate limited")
                return TestResult(
                    test_name="json_mode",
                    status=TestStatus.FAILED,
                    latency_ms=int((time.time() - start_time) * 1000),
                    error_message="Rate limited by API",
                )
            logger.error(f"✗ {model}: JSON mode - FAILED: {str(e)}")
            return TestResult(
                test_name="json_mode",
                status=TestStatus.ERROR,
                latency_ms=int((time.time() - start_time) * 1000),
                error_message=str(e),
            )
        except Exception as e:
            logger.error(f"✗ {model}: JSON mode - FAILED: {str(e)}")
            return TestResult(
                test_name="json_mode",
                status=TestStatus.ERROR,
                latency_ms=int((time.time() - start_time) * 1000),
                error_message=str(e),
            )

    async def test_streaming_tool_calls(self, model: str) -> TestResult:
        start_time = time.time()
        try:
            request = ChatCompletionRequest(
                model=model,
                messages=[
                    ChatMessage(role="user", content="What's the weather in Tokyo?")
                ],
                tools=get_test_tools(),
                tool_choice="auto",
                stream=True,
            )

            response = await self.chat_completion(request, stream=True)

            if not response:
                return TestResult(
                    test_name="streaming_tool_calls",
                    status=TestStatus.ERROR,
                    latency_ms=int((time.time() - start_time) * 1000),
                    error_message="No response from API",
                )

            chunks = response.get("chunks", [])
            if not chunks:
                return TestResult(
                    test_name="streaming_tool_calls",
                    status=TestStatus.FAILED,
                    latency_ms=int((time.time() - start_time) * 1000),
                    error_message="No chunks in streaming response",
                )

            has_tool_calls = False
            for chunk in chunks:
                delta = chunk.get("choices", [{}])[0].get("delta", {})
                if "tool_calls" in delta:
                    has_tool_calls = True
                    break

            if not has_tool_calls:
                return TestResult(
                    test_name="streaming_tool_calls",
                    status=TestStatus.FAILED,
                    latency_ms=int((time.time() - start_time) * 1000),
                    error_message="No tool_calls in streaming response",
                )

            logger.info(f"✓ {model}: Streaming tool calls - PASSED")
            return TestResult(
                test_name="streaming_tool_calls",
                status=TestStatus.PASSED,
                latency_ms=int((time.time() - start_time) * 1000),
                details={"chunks_received": len(chunks)},
            )

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.error(f"✗ {model}: Streaming tool calls - FAILED: Rate limited")
                return TestResult(
                    test_name="streaming_tool_calls",
                    status=TestStatus.FAILED,
                    latency_ms=int((time.time() - start_time) * 1000),
                    error_message="Rate limited by API",
                )
            logger.error(f"✗ {model}: Streaming tool calls - FAILED: {str(e)}")
            return TestResult(
                test_name="streaming_tool_calls",
                status=TestStatus.ERROR,
                latency_ms=int((time.time() - start_time) * 1000),
                error_message=str(e),
            )
        except Exception as e:
            logger.error(f"✗ {model}: Streaming tool calls - FAILED: {str(e)}")
            return TestResult(
                test_name="streaming_tool_calls",
                status=TestStatus.ERROR,
                latency_ms=int((time.time() - start_time) * 1000),
                error_message=str(e),
            )

    async def run_all_tests(self, model: str, owned_by: str) -> dict[str, TestResult]:
        tests = {
            "basic_tool_calling": await self.test_basic_tool_calling(model),
            "tool_output_reasoning": await self.test_tool_output_reasoning(model),
            "multi_tool_calling": await self.test_multi_tool_calling(model),
            "json_mode": await self.test_json_mode(model),
            "streaming_tool_calls": await self.test_streaming_tool_calls(model),
        }
        return tests
