from __future__ import annotations

import argparse
from typing import Any

try:
    from .workflow_common import cli_result, compressed_false_spans, issue, load_json
except ImportError:
    from workflow_common import cli_result, compressed_false_spans, issue, load_json


def _validate_span(
    source: str,
    span: Any,
    excerpt: Any,
    base_path: str,
) -> tuple[list[dict[str, Any]], tuple[int, int] | None]:
    issues: list[dict[str, Any]] = []
    if not isinstance(span, dict):
        return [issue("invalid_span", "Source span must be an object.", base_path)], None
    start = span.get("start")
    end = span.get("end")
    if (
        not isinstance(start, int)
        or isinstance(start, bool)
        or not isinstance(end, int)
        or isinstance(end, bool)
        or start < 0
        or end <= start
        or end > len(source)
    ):
        issues.append(
            issue(
                "invalid_span",
                "Source span must be a valid half-open interval within the original text.",
                base_path,
                span=span,
                source_length=len(source),
            )
        )
        return issues, None
    expected = source[start:end]
    if excerpt != expected:
        issues.append(
            issue(
                "verbatim_mismatch",
                "Stored verbatim text does not match the declared source slice.",
                base_path,
                span={"start": start, "end": end},
                expected=expected,
                actual=excerpt,
            )
        )
    return issues, (start, end)


def coverage_issues(ledger: dict[str, Any]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    reviewers = ledger.get("reviewers")
    if not isinstance(reviewers, list) or not reviewers:
        return [issue("missing_reviewers", "At least one Reviewer is required.", "reviewers")]

    seen_reviewer_ids: set[str] = set()
    for reviewer_index, reviewer in enumerate(reviewers):
        reviewer_path = f"reviewers[{reviewer_index}]"
        if not isinstance(reviewer, dict):
            issues.append(issue("invalid_reviewer", "Reviewer record must be an object.", reviewer_path))
            continue
        reviewer_id = reviewer.get("reviewer_id")
        if reviewer_id in seen_reviewer_ids:
            issues.append(issue("duplicate_reviewer_id", "Reviewer IDs must be unique.", f"{reviewer_path}.reviewer_id"))
        if isinstance(reviewer_id, str):
            seen_reviewer_ids.add(reviewer_id)

        source = reviewer.get("source_text")
        if not isinstance(source, str) or not source:
            issues.append(issue("missing_source_text", "Reviewer source text is required.", f"{reviewer_path}.source_text"))
            continue
        covered = [False] * len(source)
        seen_comment_ids: set[str] = set()

        comments = reviewer.get("comments", [])
        if not isinstance(comments, list) or not comments:
            issues.append(issue("missing_comments", "At least one atomic Comment is required.", f"{reviewer_path}.comments"))
            comments = []
        for comment_index, comment in enumerate(comments):
            comment_path = f"{reviewer_path}.comments[{comment_index}]"
            if not isinstance(comment, dict):
                issues.append(issue("invalid_comment", "Comment record must be an object.", comment_path))
                continue
            comment_id = comment.get("comment_id")
            if comment_id in seen_comment_ids:
                issues.append(issue("duplicate_comment_id", "Comment IDs must be unique within a Reviewer.", f"{comment_path}.comment_id"))
            if isinstance(comment_id, str):
                seen_comment_ids.add(comment_id)
            span_issues, valid_span = _validate_span(
                source,
                comment.get("source_span"),
                comment.get("verbatim_comment"),
                f"{comment_path}.source_span",
            )
            issues.extend(span_issues)
            if valid_span:
                for position in range(*valid_span):
                    covered[position] = True

        segments = reviewer.get("non_action_segments", [])
        if not isinstance(segments, list):
            issues.append(issue("invalid_non_action_segments", "Non-action segments must be an array.", f"{reviewer_path}.non_action_segments"))
            segments = []
        for segment_index, segment in enumerate(segments):
            segment_path = f"{reviewer_path}.non_action_segments[{segment_index}]"
            if not isinstance(segment, dict):
                issues.append(issue("invalid_non_action_segment", "Non-action segment must be an object.", segment_path))
                continue
            span_issues, valid_span = _validate_span(
                source,
                segment.get("source_span"),
                segment.get("verbatim_text"),
                f"{segment_path}.source_span",
            )
            issues.extend(span_issues)
            if valid_span:
                for position in range(*valid_span):
                    covered[position] = True

        for uncovered in compressed_false_spans(covered):
            issues.append(
                issue(
                    "uncovered_source",
                    "Every source character must belong to a Comment or declared non-action segment.",
                    f"{reviewer_path}.source_text",
                    span=uncovered,
                    text=source[uncovered["start"] : uncovered["end"]],
                )
            )
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate 100 percent Reviewer source coverage.")
    parser.add_argument("ledger", help="Path to reviewer ledger JSON")
    args = parser.parse_args()
    return cli_result(coverage_issues(load_json(args.ledger)))


if __name__ == "__main__":
    raise SystemExit(main())
