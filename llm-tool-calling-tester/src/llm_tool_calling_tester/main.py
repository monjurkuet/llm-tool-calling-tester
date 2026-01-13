import argparse
import json
import os
import asyncio
import httpx
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from tqdm import tqdm
import time

from .tester import ModelTester
from .models import ModelTestResults, TestResult, TestStatus, FullReport, TestSummary
from .config import (
    API_BASE_URL,
    TIMEOUT_SECONDS,
    MAX_WORKERS,
    OUTPUT_DIR,
    RECOMMENDATION_THRESHOLDS,
    AUTONOMOUS_AGENT_WEIGHTS,
)


class ModelTestRunner:
    def __init__(
        self,
        api_url: str = API_BASE_URL,
        max_workers: int = MAX_WORKERS,
        filter_pattern: Optional[str] = None,
        quick_mode: bool = False,
    ):
        self.api_url = api_url
        self.max_workers = max_workers
        self.filter_pattern = filter_pattern
        self.quick_mode = quick_mode
        self.tester = ModelTester(api_url)

    async def fetch_models(self) -> List[dict]:
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
                response = await client.get(f"{self.api_url}/models")
                response.raise_for_status()
                data = response.json()
                return data.get("data", [])
        except Exception as e:
            print(f"Failed to fetch models: {str(e)}")
            return []

    def filter_models(self, models: List[dict]) -> List[dict]:
        filtered_models = []

        for model in models:
            model_id = model.get("id", "")

            if "gpt" in model_id.lower():
                continue

            if self.filter_pattern:
                import re

                if re.search(self.filter_pattern, model_id):
                    filtered_models.append(model)
            else:
                filtered_models.append(model)

        return filtered_models

    def calculate_score(self, tests: dict[str, TestResult]) -> float:
        if self.quick_mode:
            basic = tests.get("basic_tool_calling")
            if basic and basic.status == TestStatus.PASSED:
                return 100.0
            return 0.0

        score = 0.0
        test_names = list(AUTONOMOUS_AGENT_WEIGHTS.keys())

        for test_name, weight in AUTONOMOUS_AGENT_WEIGHTS.items():
            if test_name in tests:
                test = tests[test_name]
                if test.status == TestStatus.PASSED:
                    score += weight * 100

        return score

    def get_recommendation(self, score: float) -> str:
        if score >= RECOMMENDATION_THRESHOLDS["recommended"]:
            return "recommended"
        elif score >= RECOMMENDATION_THRESHOLDS["partial"]:
            return "partial_support"
        else:
            return "no_tool_calling"

    async def test_model(self, model: dict) -> Optional[ModelTestResults]:
        model_id = model.get("id", "unknown")
        owned_by = model.get("owned_by", "unknown")

        print(f"\n⚪ Testing: {model_id} ({owned_by})")

        if self.quick_mode:
            basic_test = await self.tester.test_basic_tool_calling(model_id)
            if basic_test.status == TestStatus.SKIPPED:
                print(f"  ⏭️ Skipped: {basic_test.error_message}")
                return None
            tests = {"basic_tool_calling": basic_test}
        else:
            tests = await self.tester.run_all_tests(model_id, owned_by)
            if any(test.status == TestStatus.SKIPPED for test in tests.values()):
                skipped_msg = next(
                    (
                        t.error_message
                        for t in tests.values()
                        if t.status == TestStatus.SKIPPED
                    ),
                    "Model not available",
                )
                print(f"  ⏭️ Skipped: {skipped_msg}")
                return None

            if any(test.status == TestStatus.ERROR for test in tests.values()):
                error_msg = next(
                    (
                        t.error_message
                        for t in tests.values()
                        if t.status == TestStatus.ERROR
                    ),
                    "Unknown error",
                )
                print(f"  ⚠️ Error: {error_msg}")
                return None

        score = self.calculate_score(tests)
        recommendation = self.get_recommendation(score)

        total_latency = sum(
            test.latency_ms
            for test in tests.values()
            if test.status != TestStatus.SKIPPED
        )

        return ModelTestResults(
            model_id=model_id,
            owned_by=owned_by,
            tests=tests,
            overall_score=score,
            recommendation=recommendation,
            total_latency_ms=total_latency,
            is_gpt_model=False,
        )

    async def run_tests(self) -> List[ModelTestResults]:
        models = await self.fetch_models()

        if not models:
            print("No models found to test")
            return []

        filtered_models = self.filter_models(models)

        print(f"\nTesting {len(filtered_models)} models...")
        if self.quick_mode:
            print("Quick mode: Only testing basic tool calling")

        results = []

        for model in tqdm(filtered_models, desc="Testing models"):
            result = await self.test_model(model)
            if result:
                results.append(result)

        return results

    def generate_summary(self, results: List[ModelTestResults]) -> TestSummary:
        recommended = [r.model_id for r in results if r.recommendation == "recommended"]
        partial = [r.model_id for r in results if r.recommendation == "partial_support"]
        no_tool = [r.model_id for r in results if r.recommendation == "no_tool_calling"]

        gpt_summary = {}

        test_stats = {
            "total": len(results),
            "recommended": len(recommended),
            "partial_support": len(partial),
            "no_tool_calling": len(no_tool),
            "gpt_models": 0,
        }

        return TestSummary(
            timestamp=datetime.utcnow().isoformat() + "Z",
            api_endpoint=self.api_url,
            total_models=len(results),
            tested_models=len([r for r in results if r.tests]),
            recommended=recommended,
            partial_support=partial,
            no_tool_calling=no_tool,
            gpt_models_summary=gpt_summary,
            test_statistics=test_stats,
        )

    def print_console_summary(
        self, summary: TestSummary, results: List[ModelTestResults]
    ):
        print("\n" + "=" * 80)
        print(f"MODEL TESTING RESULTS ({summary.total_models} models tested)")
        print("=" * 80)

        print(
            f"\n✅ Recommended for Autonomous Agent ({len(summary.recommended)} models):"
        )
        for model_id in summary.recommended:
            result = next(r for r in results if r.model_id == model_id)
            tests_str = ", ".join(
                [
                    f"{k}:{'✓' if v.status == TestStatus.PASSED else '✗'}"
                    for k, v in result.tests.items()
                    if k in AUTONOMOUS_AGENT_WEIGHTS
                ]
            )
            print(f"  - {model_id} ({tests_str}) - Score: {result.overall_score:.1f}")

        print(f"\n⚠️ Partial Support ({len(summary.partial_support)} models):")
        for model_id in summary.partial_support[:5]:
            result = next(r for r in results if r.model_id == model_id)
            tests_str = ", ".join(
                [
                    f"{k}:{'✓' if v.status == TestStatus.PASSED else '✗'}"
                    for k, v in result.tests.items()
                    if k in AUTONOMOUS_AGENT_WEIGHTS
                ]
            )
            print(f"  - {model_id} ({tests_str}) - Score: {result.overall_score:.1f}")

        if len(summary.partial_support) > 5:
            print(f"  ... and {len(summary.partial_support) - 5} more")

        print(f"\n❌ No Tool Calling ({len(summary.no_tool_calling)} models):")
        for model_id in summary.no_tool_calling[:5]:
            print(f"  - {model_id}")
        if len(summary.no_tool_calling) > 5:
            print(f"  ... and {len(summary.no_tool_calling) - 5} more")

        print(f"\n📈 Test Statistics:")
        print(f"  - Total: {summary.test_statistics['total']}")
        print(f"  - Recommended: {summary.test_statistics['recommended']}")
        print(f"  - Partial Support: {summary.test_statistics['partial_support']}")
        print(f"  - No Tool Calling: {summary.test_statistics['no_tool_calling']}")

        print("\n💡 Recommendations for Autonomous Research Agent:")
        top_models = sorted(
            [r for r in results if r.recommendation == "recommended"],
            key=lambda x: x.overall_score,
            reverse=True,
        )[:3]
        for i, model in enumerate(top_models, 1):
            print(
                f"  {i}. {model.model_id} (Score: {model.overall_score:.1f}, "
                f"Latency: {model.total_latency_ms}ms)"
            )

        print("=" * 80)

    def save_json_report(self, summary: TestSummary, results: List[ModelTestResults]):
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{OUTPUT_DIR}/model_capabilities_{timestamp}.json"

        report = FullReport(
            summary=summary,
            results=results,
            metadata={
                "api_url": self.api_url,
                "quick_mode": str(self.quick_mode),
                "test_weights": str(AUTONOMOUS_AGENT_WEIGHTS),
            },
        )

        with open(filename, "w") as f:
            f.write(report.model_dump_json(indent=2))

        print(f"\n📄 Full report saved to: {filename}")


def main():
    parser = argparse.ArgumentParser(
        description="Test local LLM models for tool calling capabilities"
    )
    parser.add_argument(
        "--api-url",
        default=API_BASE_URL,
        help="API base URL (default: http://localhost:8317/v1)",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=MAX_WORKERS,
        help="Maximum parallel workers (default: 5)",
    )
    parser.add_argument("--filter", type=str, help="Filter models by regex pattern")
    parser.add_argument(
        "--quick", action="store_true", help="Quick mode: only test basic tool calling"
    )

    args = parser.parse_args()

    runner = ModelTestRunner(
        api_url=args.api_url,
        max_workers=args.max_workers,
        filter_pattern=args.filter,
        quick_mode=args.quick,
    )

    results = asyncio.run(runner.run_tests())

    if not results:
        print("No results to report")
        return

    summary = runner.generate_summary(results)
    runner.print_console_summary(summary, results)
    runner.save_json_report(summary, results)


if __name__ == "__main__":
    main()
