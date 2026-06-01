from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from .analytics import calculate_report_stats, render_report_stats
from .evaluation import (
    EvalResult,
    build_eval_summary,
    evaluate_extractor,
    evaluate_report,
    load_eval_cases,
    render_eval_summary,
)
from .extraction import (
    EXTRACTION_SYSTEM_PROMPT,
    extraction_json_schema,
    strict_extraction_json_schema,
)
from .llm_extractor import build_extraction_user_prompt
from .models import EndoscopyType
from .nomenclature import export_nomenclature
from .openai_client import DEFAULT_OPENAI_MODEL
from .pipeline import DEMO_INPUT, build_extractor
from .render import render_report


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the endoscopy report structuring prototype."
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run the built-in synthetic gastroscopy demo.",
    )
    parser.add_argument(
        "--schema",
        action="store_true",
        help="Print the LLM extraction JSON schema and exit.",
    )
    parser.add_argument(
        "--strict-schema",
        action="store_true",
        help="Print the strict provider JSON schema and exit.",
    )
    parser.add_argument(
        "--nomenclature",
        action="store_true",
        help="Print zones, finding types, labels, and synonyms as JSON.",
    )
    parser.add_argument(
        "--prompt",
        action="store_true",
        help="Print the LLM extraction prompts for the provided input and exit.",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Print report statistics after the rendered report.",
    )
    parser.add_argument(
        "--eval",
        metavar="PATH",
        help="Run synthetic extractor evaluation against a JSON case file.",
    )
    parser.add_argument(
        "--live-smoke",
        nargs="?",
        const="eval_cases/synthetic_endoscopy.json",
        metavar="PATH",
        help=(
            "Run an explicit OpenAI live smoke test against a synthetic JSON "
            "case file. Defaults to eval_cases/synthetic_endoscopy.json."
        ),
    )
    parser.add_argument(
        "--provider",
        choices=["synthetic", "openai"],
        default="synthetic",
        help="Extraction provider to use for report generation.",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_OPENAI_MODEL,
        help="OpenAI model to use when --provider openai is selected.",
    )
    parser.add_argument(
        "--text",
        help="Free-form doctor's note. If omitted, stdin is used.",
    )
    parser.add_argument(
        "--exam-type",
        choices=[item.value for item in EndoscopyType],
        default=EndoscopyType.GASTROSCOPY.value,
        help="Endoscopy type for the report.",
    )
    args = parser.parse_args(argv)

    if args.schema:
        print(json.dumps(extraction_json_schema(), ensure_ascii=False, indent=2))
        return 0

    if args.strict_schema:
        print(json.dumps(strict_extraction_json_schema(), ensure_ascii=False, indent=2))
        return 0

    if args.nomenclature:
        print(json.dumps(export_nomenclature(), ensure_ascii=False, indent=2))
        return 0

    if args.live_smoke:
        if args.provider != "openai":
            parser.error("--live-smoke requires --provider openai")
        return _run_live_smoke(Path(args.live_smoke), args.model)

    if args.eval:
        cases = load_eval_cases(Path(args.eval))
        summary = evaluate_extractor(build_extractor("synthetic"), cases)
        print(render_eval_summary(summary))
        return 0 if summary.passed_cases == summary.total_cases else 1

    raw_input = _raw_input_from_args(args.text, args.demo)
    if not raw_input:
        parser.error("provide --demo, --text, or stdin input")

    if args.prompt:
        print("SYSTEM PROMPT")
        print(EXTRACTION_SYSTEM_PROMPT)
        print()
        print("USER PROMPT")
        print(
            build_extraction_user_prompt(
                raw_input=raw_input,
                exam_type=EndoscopyType(args.exam_type),
            )
        )
        return 0

    report = build_extractor(args.provider, args.model).extract(
        raw_input=raw_input,
        exam_type=EndoscopyType(args.exam_type),
    )
    print(render_report(report))
    if args.stats:
        print()
        print(render_report_stats(calculate_report_stats(report)))
    return 0


def _raw_input_from_args(text: Optional[str], demo: bool) -> str:
    if demo:
        return DEMO_INPUT
    if text is not None:
        return text
    if not sys.stdin.isatty():
        return sys.stdin.read().strip()
    return ""


def _run_live_smoke(path: Path, model: str) -> int:
    cases = load_eval_cases(path)
    try:
        extractor = build_extractor("openai", model)
    except Exception as exc:  # noqa: BLE001 - setup errors should be readable in CLI.
        print(f"Live smoke setup failed: {exc}", file=sys.stderr)
        return 1

    results = []

    for case in cases:
        print(f"Live smoke case: {case.case_id}")
        try:
            report = extractor.extract(
                raw_input=case.raw_input,
                exam_type=case.exam_type,
                indication=case.indication,
            )
            print(render_report(report))
            print()
            print(render_report_stats(calculate_report_stats(report)))
            results.append(evaluate_report(case, report))
        except Exception as exc:  # noqa: BLE001 - CLI should surface live failures.
            results.append(_failed_live_result(case, str(exc)))
            print(f"Extraction failed: {exc}")
        print()

    summary = build_eval_summary(results)
    print(render_eval_summary(summary))
    return 0 if summary.passed_cases == summary.total_cases else 1


def _failed_live_result(case, error: str) -> EvalResult:
    expected_count = sum(
        len(finding.observations) for finding in case.expected_findings
    )
    return EvalResult(
        case_id=case.case_id,
        passed=False,
        expected_observations=expected_count,
        actual_observations=0,
        matched_observations=0,
        error=error,
    )


if __name__ == "__main__":
    raise SystemExit(main())
