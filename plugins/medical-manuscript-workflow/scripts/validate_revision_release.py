from __future__ import annotations

import argparse
from typing import Any

try:
    from .validate_reviewer_coverage import coverage_issues
    from .workflow_common import cli_result, issue, load_json
except ImportError:
    from validate_reviewer_coverage import coverage_issues
    from workflow_common import cli_result, issue, load_json


def release_issues(ledger: dict[str, Any]) -> list[dict[str, Any]]:
    issues = coverage_issues(ledger)
    reviewers = ledger.get("reviewers", [])
    if not isinstance(reviewers, list):
        return issues

    for reviewer_index, reviewer in enumerate(reviewers):
        if not isinstance(reviewer, dict):
            continue
        comments = reviewer.get("comments", [])
        if not isinstance(comments, list):
            continue
        expected_order = 1
        for comment_index, comment in enumerate(comments):
            if not isinstance(comment, dict):
                continue
            base = f"reviewers[{reviewer_index}].comments[{comment_index}]"
            if comment.get("order") != expected_order:
                issues.append(issue("invalid_comment_order", "Comments must remain in contiguous source order.", f"{base}.order"))
            expected_order += 1

            decision = comment.get("decision") if isinstance(comment.get("decision"), dict) else {}
            state = decision.get("state")
            if state in {"pending", "deferred", None}:
                issues.append(issue("nonterminal_decision", "Every Comment needs a release-terminal decision.", f"{base}.decision.state"))
            if state in {"approved", "rejected", "conditional_approved"} and not decision.get("decided_at"):
                issues.append(issue("missing_decision_time", "A terminal decision needs a decision timestamp.", f"{base}.decision.decided_at"))

            conditional_ready = state == "conditional_approved" and bool(decision.get("conditions")) and decision.get("conditions_met") is True
            if state == "conditional_approved" and not conditional_ready:
                issues.append(issue("unresolved_conditions", "Conditional approval requires recorded conditions and confirmation that they were met.", f"{base}.decision"))
            approved = state == "approved" or conditional_ready

            implementation = comment.get("implementation") if isinstance(comment.get("implementation"), dict) else {}
            if approved:
                if implementation.get("status") != "verified":
                    issues.append(issue("implementation_not_verified", "Approved changes must reach verified implementation status.", f"{base}.implementation.status"))
                evidence = implementation.get("evidence")
                if not isinstance(evidence, list) or not evidence:
                    issues.append(issue("missing_implementation_evidence", "Approved changes require at least one implementation evidence record.", f"{base}.implementation.evidence"))
            elif state == "rejected" and implementation.get("status") != "not_applicable":
                issues.append(issue("rejected_change_has_implementation", "Rejected Comments must record implementation as not applicable.", f"{base}.implementation.status"))

            response = comment.get("response")
            if not isinstance(response, str) or not response.strip():
                issues.append(issue("missing_response", "Every Comment requires a substantive Response.", f"{base}.response"))

            location = comment.get("location") if isinstance(comment.get("location"), dict) else {}
            if approved:
                if location.get("status") != "verified":
                    issues.append(issue("location_not_verified", "Approved changes require a verified Location of Revision.", f"{base}.location.status"))
                entries = location.get("entries")
                if not isinstance(entries, list) or not entries:
                    issues.append(issue("missing_location_entries", "Approved changes require at least one location entry.", f"{base}.location.entries"))
            elif state == "rejected" and location.get("status") not in {"not_applicable", "verified"}:
                issues.append(issue("invalid_rejected_location", "Rejected Comments need a verified location or an explicit not-applicable status.", f"{base}.location.status"))

            if state in {"approved", "rejected"} or conditional_ready:
                if comment.get("status") != "closed":
                    issues.append(issue("comment_not_closed", "Release-terminal Comments must be closed.", f"{base}.status"))
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Reviewer revision release state.")
    parser.add_argument("ledger", help="Path to reviewer ledger JSON")
    args = parser.parse_args()
    return cli_result(release_issues(load_json(args.ledger)))


if __name__ == "__main__":
    raise SystemExit(main())
