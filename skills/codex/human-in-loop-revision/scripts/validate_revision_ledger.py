#!/usr/bin/env python3
"""校验人在回路式正式修订台账与决定门。

仅使用 Python 标准库。脚本负责确定性结构和状态检查；语义定位、回应
充分性及正式文件内容仍需人工复核。
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable


STAGE_ORDER = {"structure": 0, "analysis": 1, "execution": 2, "release": 3}
DECISIONS = {"pending", "approved", "rejected", "deferred"}
IMPLEMENTATION_STATES = {"not_started", "in_progress", "completed", "not_required"}
RESPONSE_STATES = {"not_started", "draft", "completed", "not_required"}
VERIFICATION_STATES = {"not_started", "in_progress", "completed"}
LOCATION_STATES = {"found", "distributed", "no_direct_location", "unresolved"}
ACTION_TYPES = {
    "direct_content_revision",
    "evidence_research",
    "data_or_computation",
    "visual_or_structure",
    "response_only",
    "decision_required",
    "blocked",
    "other",
}
RELATION_TYPES = {
    "duplicate",
    "overlap",
    "contains",
    "depends_on",
    "conflicts_with",
    "prerequisite_for",
    "propagates_to",
    "same_issue",
}
DISPOSITIONS = {
    "pending",
    "accepted",
    "partially_accepted",
    "rejected",
    "explained",
    "deferred",
    "no_response_required",
}
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$")
PLACEHOLDER_RE = re.compile(r"(?:TODO|TBD|待确认|待补充|待完善|<填写|\[填写)", re.IGNORECASE)


@dataclass
class Diagnostic:
    severity: str
    code: str
    path: str
    message: str


class LedgerValidator:
    def __init__(self, stage: str, verify_files: bool = False, base_dir: Path | None = None) -> None:
        self.stage = stage
        self.level = STAGE_ORDER[stage]
        self.verify_files = verify_files
        self.base_dir = base_dir or Path.cwd()
        self.diagnostics: list[Diagnostic] = []
        self.item_ids: set[str] = set()
        self.source_artifact_ids: set[str] = set()
        self.all_artifact_ids: set[str] = set()
        self.change_owner: dict[str, str] = {}
        self.item_change_ids: dict[str, set[str]] = {}
        self.response_refs: list[tuple[str, str, str]] = []
        self.decision_maker_id = ""

    def error(self, code: str, path: str, message: str) -> None:
        self.diagnostics.append(Diagnostic("error", code, path, message))

    def warn(self, code: str, path: str, message: str) -> None:
        self.diagnostics.append(Diagnostic("warning", code, path, message))

    def require_dict(self, value: Any, path: str) -> dict[str, Any] | None:
        if not isinstance(value, dict):
            self.error("TYPE_OBJECT", path, "必须是 JSON 对象。")
            return None
        return value

    def require_list(self, value: Any, path: str) -> list[Any] | None:
        if not isinstance(value, list):
            self.error("TYPE_ARRAY", path, "必须是 JSON 数组。")
            return None
        return value

    def require_keys(self, obj: dict[str, Any], keys: Iterable[str], path: str) -> None:
        for key in keys:
            if key not in obj:
                self.error("MISSING_FIELD", f"{path}.{key}", "缺少必填字段。")

    def nonempty(self, value: Any, path: str, code: str = "EMPTY_FIELD") -> bool:
        if not isinstance(value, str) or not value.strip():
            self.error(code, path, "必须填写非空字符串。")
            return False
        return True

    def valid_time(self, value: Any, path: str) -> bool:
        if not isinstance(value, str) or not ISO_RE.match(value):
            self.error("INVALID_TIME", path, "必须使用含时区的 ISO-8601 时间。")
            return False
        return True

    def valid_hash(self, value: Any, path: str, allow_empty: bool = False) -> bool:
        if allow_empty and (value is None or value == ""):
            return True
        if not isinstance(value, str) or not SHA256_RE.match(value):
            self.error("INVALID_SHA256", path, "必须是 64 位十六进制 SHA-256。")
            return False
        return True

    def enum(self, value: Any, allowed: set[str], path: str, code: str) -> bool:
        if value not in allowed:
            self.error(code, path, f"无效值 {value!r}；允许值：{', '.join(sorted(allowed))}。")
            return False
        return True

    def validate(self, ledger: Any, gates: list[Any]) -> list[Diagnostic]:
        root = self.require_dict(ledger, "$")
        if root is None:
            return self.diagnostics
        self.require_keys(
            root,
            ["protocol", "protocol_version", "ledger_id", "task", "source_lock", "working_artifacts", "items", "release"],
            "$",
        )
        if root.get("protocol") != "formal-revision-interchange":
            self.error("PROTOCOL", "$.protocol", "协议标识必须为 formal-revision-interchange。")
        version = root.get("protocol_version")
        if not isinstance(version, str) or version.split(".", 1)[0] != "1":
            self.error("PROTOCOL_VERSION", "$.protocol_version", "仅支持主版本 1。")
        self.nonempty(root.get("ledger_id"), "$.ledger_id")
        if self.level >= STAGE_ORDER["analysis"] and root.get("template") is True:
            self.error("TEMPLATE_ACTIVE", "$.template", "模板必须复制、填写并设为 false 后才能进入分析阶段。")

        self._validate_task(root.get("task"))
        self._validate_source_lock(root.get("source_lock"))
        self._validate_working_artifacts(root.get("working_artifacts"))
        self._validate_items(root.get("items"))
        self._validate_cross_references(root.get("items"))
        gate_map = self._validate_gates(gates, root)
        self._validate_execution_coverage(root.get("items"), gate_map, bool(gates))
        self._validate_release(root)
        return self.diagnostics

    def _validate_task(self, value: Any) -> None:
        task = self.require_dict(value, "$.task")
        if task is None:
            return
        self.require_keys(task, ["title", "scope", "status", "decision_maker"], "$.task")
        decision_maker = self.require_dict(task.get("decision_maker"), "$.task.decision_maker")
        if decision_maker is not None:
            self.require_keys(decision_maker, ["id", "role", "authority_scope"], "$.task.decision_maker")
            if isinstance(decision_maker.get("id"), str):
                self.decision_maker_id = decision_maker.get("id", "")
        if self.level >= STAGE_ORDER["analysis"]:
            self.nonempty(task.get("title"), "$.task.title")
            self.nonempty(task.get("scope"), "$.task.scope")
            if decision_maker is not None:
                self.nonempty(decision_maker.get("id"), "$.task.decision_maker.id", "DECISION_MAKER_MISSING")
                self.nonempty(decision_maker.get("role"), "$.task.decision_maker.role", "DECISION_MAKER_MISSING")
                self.nonempty(decision_maker.get("authority_scope"), "$.task.decision_maker.authority_scope")

    def _validate_source_lock(self, value: Any) -> None:
        lock = self.require_dict(value, "$.source_lock")
        if lock is None:
            return
        self.require_keys(lock, ["locked", "locked_at", "locked_by", "artifacts"], "$.source_lock")
        artifacts = self.require_list(lock.get("artifacts"), "$.source_lock.artifacts")
        if artifacts is None:
            return
        if self.level >= STAGE_ORDER["analysis"]:
            if lock.get("locked") is not True:
                self.error("SOURCE_NOT_LOCKED", "$.source_lock.locked", "进入分析阶段前必须锁定源文件。")
            self.valid_time(lock.get("locked_at"), "$.source_lock.locked_at")
            self.nonempty(lock.get("locked_by"), "$.source_lock.locked_by")
            if not artifacts:
                self.error("SOURCE_EMPTY", "$.source_lock.artifacts", "至少登记一个源文件。")
        for index, artifact in enumerate(artifacts):
            path = f"$.source_lock.artifacts[{index}]"
            obj = self.require_dict(artifact, path)
            if obj is None:
                continue
            self.require_keys(obj, ["artifact_id", "role", "path_or_uri", "version", "content_sha256", "lock_note"], path)
            artifact_id = obj.get("artifact_id")
            if isinstance(artifact_id, str) and artifact_id:
                if artifact_id in self.all_artifact_ids:
                    self.error("ARTIFACT_ID_DUPLICATE", f"{path}.artifact_id", f"重复文件标识：{artifact_id}。")
                self.source_artifact_ids.add(artifact_id)
                self.all_artifact_ids.add(artifact_id)
            else:
                self.error("ARTIFACT_ID_EMPTY", f"{path}.artifact_id", "文件标识不能为空。")
            if self.level >= STAGE_ORDER["analysis"]:
                self.nonempty(obj.get("path_or_uri"), f"{path}.path_or_uri")
                has_hash = isinstance(obj.get("content_sha256"), str) and bool(obj.get("content_sha256"))
                if has_hash:
                    hash_valid = self.valid_hash(obj.get("content_sha256"), f"{path}.content_sha256")
                    if hash_valid and self.verify_files:
                        self._verify_local_file_hash(obj.get("path_or_uri"), obj.get("content_sha256"), path)
                elif not (obj.get("version") and obj.get("lock_note")):
                    self.error("SOURCE_VERSION_EVIDENCE", path, "必须提供内容摘要值；无法计算时同时提供稳定版本和锁定说明。")

    def _verify_local_file_hash(self, location: Any, expected: str, path: str) -> None:
        if not isinstance(location, str) or not location:
            return
        if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", location):
            self.warn("SOURCE_URI_NOT_HASHED", f"{path}.path_or_uri", "远程 URI 无法由本地脚本复算摘要值。")
            return
        candidate = Path(location)
        if not candidate.is_absolute():
            candidate = self.base_dir / candidate
        if not candidate.exists() or not candidate.is_file():
            self.error("SOURCE_FILE_MISSING", f"{path}.path_or_uri", f"无法读取本地源文件：{candidate}。")
            return
        digest = hashlib.sha256()
        try:
            with candidate.open("rb") as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(block)
        except OSError as exc:
            self.error("SOURCE_FILE_READ", f"{path}.path_or_uri", f"读取源文件失败：{exc}。")
            return
        if digest.hexdigest().lower() != expected.lower():
            self.error("SOURCE_FILE_HASH_MISMATCH", f"{path}.content_sha256", "本地源文件内容与锁定摘要值不一致。")

    def _validate_working_artifacts(self, value: Any) -> None:
        artifacts = self.require_list(value, "$.working_artifacts")
        if artifacts is None:
            return
        for index, artifact in enumerate(artifacts):
            path = f"$.working_artifacts[{index}]"
            obj = self.require_dict(artifact, path)
            if obj is None:
                continue
            self.require_keys(obj, ["artifact_id", "source_artifact_id", "path_or_uri", "status", "content_sha256"], path)
            artifact_id = obj.get("artifact_id")
            if isinstance(artifact_id, str) and artifact_id:
                if artifact_id in self.all_artifact_ids:
                    self.error("ARTIFACT_ID_DUPLICATE", f"{path}.artifact_id", f"重复文件标识：{artifact_id}。")
                self.all_artifact_ids.add(artifact_id)
            else:
                self.error("ARTIFACT_ID_EMPTY", f"{path}.artifact_id", "文件标识不能为空。")
            source_id = obj.get("source_artifact_id")
            if source_id and source_id not in self.source_artifact_ids:
                self.error("SOURCE_ARTIFACT_UNKNOWN", f"{path}.source_artifact_id", f"未知源文件标识：{source_id}。")
            if self.level >= STAGE_ORDER["execution"] and obj.get("status") != "not_created":
                self.nonempty(obj.get("path_or_uri"), f"{path}.path_or_uri")

    def _validate_items(self, value: Any) -> None:
        items = self.require_list(value, "$.items")
        if items is None:
            return
        if not items:
            self.error("ITEMS_EMPTY", "$.items", "至少登记一条反馈。")
            return
        sequences: set[int] = set()
        for index, item in enumerate(items):
            path = f"$.items[{index}]"
            obj = self.require_dict(item, path)
            if obj is None:
                continue
            self.require_keys(
                obj,
                [
                    "item_id", "sequence", "source", "semantic_location", "interpretation", "classification",
                    "relations", "consultations", "recommendation", "decision", "implementation",
                    "formal_response", "verification", "export_policy",
                ],
                path,
            )
            item_id = obj.get("item_id")
            if isinstance(item_id, str) and item_id:
                if item_id in self.item_ids:
                    self.error("ITEM_ID_DUPLICATE", f"{path}.item_id", f"重复条目标识：{item_id}。")
                self.item_ids.add(item_id)
            else:
                self.error("ITEM_ID_EMPTY", f"{path}.item_id", "条目标识不能为空。")
                item_id = f"<index:{index}>"
            sequence = obj.get("sequence")
            if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 1:
                self.error("SEQUENCE_INVALID", f"{path}.sequence", "顺序必须是大于零的整数。")
            elif sequence in sequences:
                self.error("SEQUENCE_DUPLICATE", f"{path}.sequence", f"重复顺序：{sequence}。")
            else:
                sequences.add(sequence)
            self._validate_item_sections(obj, path, item_id)

    def _validate_item_sections(self, item: dict[str, Any], path: str, item_id: str) -> None:
        source = self.require_dict(item.get("source"), f"{path}.source")
        if source is not None:
            self.require_keys(source, ["artifact_id", "verbatim", "sha256", "raw_snapshot_ref", "normalization_note"], f"{path}.source")
            artifact_id = source.get("artifact_id")
            if artifact_id and artifact_id not in self.source_artifact_ids:
                self.error("FEEDBACK_ARTIFACT_UNKNOWN", f"{path}.source.artifact_id", f"未知反馈来源文件：{artifact_id}。")
            if self.level >= STAGE_ORDER["analysis"]:
                if self.nonempty(source.get("verbatim"), f"{path}.source.verbatim", "VERBATIM_EMPTY"):
                    expected = hashlib.sha256(source["verbatim"].encode("utf-8")).hexdigest()
                    if source.get("sha256") != expected:
                        self.error("SOURCE_HASH_MISMATCH", f"{path}.source.sha256", "原文摘要值与 verbatim 不一致，原文可能已改变。")
                else:
                    self.valid_hash(source.get("sha256"), f"{path}.source.sha256")
                self.nonempty(source.get("raw_snapshot_ref"), f"{path}.source.raw_snapshot_ref")

        location = self.require_dict(item.get("semantic_location"), f"{path}.semantic_location")
        location_state = None
        if location is not None:
            self.require_keys(location, ["status", "artifact_ids", "anchors", "coordinate_reliability", "rationale", "ambiguities"], f"{path}.semantic_location")
            location_state = location.get("status")
            self.enum(location_state, LOCATION_STATES, f"{path}.semantic_location.status", "LOCATION_STATUS")
            artifact_ids = self.require_list(location.get("artifact_ids"), f"{path}.semantic_location.artifact_ids") or []
            for pos, artifact_id in enumerate(artifact_ids):
                if artifact_id not in self.source_artifact_ids:
                    self.error("LOCATION_ARTIFACT_UNKNOWN", f"{path}.semantic_location.artifact_ids[{pos}]", f"未知基线文件：{artifact_id}。")
            anchors = self.require_list(location.get("anchors"), f"{path}.semantic_location.anchors") or []
            if self.level >= STAGE_ORDER["analysis"]:
                self.nonempty(location.get("rationale"), f"{path}.semantic_location.rationale")
                if location_state in {"found", "distributed"} and not anchors:
                    self.error("SEMANTIC_ANCHOR_EMPTY", f"{path}.semantic_location.anchors", "已定位条目必须记录至少一个语义锚点。")
                if location_state == "unresolved":
                    self.warn("LOCATION_UNRESOLVED", f"{path}.semantic_location.status", "定位仍未解决；只能在受阻或待决状态下继续。")

        interpretation = self.require_dict(item.get("interpretation"), f"{path}.interpretation")
        if interpretation is not None:
            self.require_keys(interpretation, ["core_issue", "requested_outcome", "constraints"], f"{path}.interpretation")
            if self.level >= STAGE_ORDER["analysis"]:
                self.nonempty(interpretation.get("core_issue"), f"{path}.interpretation.core_issue")
                self.nonempty(interpretation.get("requested_outcome"), f"{path}.interpretation.requested_outcome")

        classification = self.require_dict(item.get("classification"), f"{path}.classification")
        action_types: set[str] = set()
        if classification is not None:
            self.require_keys(classification, ["action_types", "requires_decision", "risk_level"], f"{path}.classification")
            actions = self.require_list(classification.get("action_types"), f"{path}.classification.action_types") or []
            action_types = {value for value in actions if isinstance(value, str)}
            for pos, action in enumerate(actions):
                if action not in ACTION_TYPES:
                    self.error("ACTION_TYPE", f"{path}.classification.action_types[{pos}]", f"未知行动分类：{action!r}。")
            if self.level >= STAGE_ORDER["analysis"] and not actions:
                self.error("ACTION_TYPE_EMPTY", f"{path}.classification.action_types", "分析阶段必须完成分类分流。")
            if location_state == "unresolved" and self.level >= STAGE_ORDER["analysis"] and not ({"blocked", "decision_required"} & action_types):
                self.error("UNRESOLVED_NOT_ROUTED", f"{path}.classification.action_types", "定位未解决时必须分流为 blocked 或 decision_required。")

        relations = self.require_list(item.get("relations"), f"{path}.relations") or []
        for rel_index, relation in enumerate(relations):
            rel_path = f"{path}.relations[{rel_index}]"
            rel = self.require_dict(relation, rel_path)
            if rel is None:
                continue
            self.require_keys(rel, ["type", "target_item_id", "rationale"], rel_path)
            self.enum(rel.get("type"), RELATION_TYPES, f"{rel_path}.type", "RELATION_TYPE")
            if rel.get("target_item_id") == item_id:
                self.error("RELATION_SELF", f"{rel_path}.target_item_id", "条目不能与自身建立关系。")
            if self.level >= STAGE_ORDER["analysis"]:
                self.nonempty(rel.get("rationale"), f"{rel_path}.rationale")

        consultations = self.require_list(item.get("consultations"), f"{path}.consultations") or []
        for con_index, consultation in enumerate(consultations):
            con_path = f"{path}.consultations[{con_index}]"
            con = self.require_dict(consultation, con_path)
            if con is None:
                continue
            self.require_keys(con, ["source_id", "source_role", "authority", "opinion"], con_path)
            if con.get("authority") != "advisory":
                self.error("CONSULTATION_AUTHORITY", f"{con_path}.authority", "咨询意见必须标记为 advisory，禁止赋予最终决定权。")
            if self.level >= STAGE_ORDER["analysis"]:
                self.nonempty(con.get("opinion"), f"{con_path}.opinion")

        recommendation = self.require_dict(item.get("recommendation"), f"{path}.recommendation")
        if recommendation is not None:
            self.require_keys(recommendation, ["proposed_action", "affected_artifact_ids", "dependencies", "risks", "rationale"], f"{path}.recommendation")
            affected = self.require_list(recommendation.get("affected_artifact_ids"), f"{path}.recommendation.affected_artifact_ids") or []
            for pos, artifact_id in enumerate(affected):
                if artifact_id not in self.all_artifact_ids:
                    self.error("AFFECTED_ARTIFACT_UNKNOWN", f"{path}.recommendation.affected_artifact_ids[{pos}]", f"未知受影响文件：{artifact_id}。")
            if self.level >= STAGE_ORDER["analysis"]:
                self.nonempty(recommendation.get("proposed_action"), f"{path}.recommendation.proposed_action")
                self.nonempty(recommendation.get("rationale"), f"{path}.recommendation.rationale")

        decision = self.require_dict(item.get("decision"), f"{path}.decision")
        decision_state = None
        if decision is not None:
            self.require_keys(decision, ["status", "decided_by", "decided_at", "instruction", "approved_artifact_ids", "conditions", "decision_gate_id"], f"{path}.decision")
            decision_state = decision.get("status")
            self.enum(decision_state, DECISIONS, f"{path}.decision.status", "DECISION_STATUS")
            if decision_state in {"approved", "rejected", "deferred"}:
                self.nonempty(decision.get("decided_by"), f"{path}.decision.decided_by")
                self.valid_time(decision.get("decided_at"), f"{path}.decision.decided_at")
                self.nonempty(decision.get("instruction"), f"{path}.decision.instruction")
                if self.decision_maker_id and decision.get("decided_by") != self.decision_maker_id:
                    self.error("DECISION_MAKER_MISMATCH", f"{path}.decision.decided_by", "条目决定人不符合台账登记的责任决策者。")
            if decision_state == "approved":
                self.nonempty(decision.get("decision_gate_id"), f"{path}.decision.decision_gate_id")

        implementation = self.require_dict(item.get("implementation"), f"{path}.implementation")
        implementation_state = None
        changes: list[Any] = []
        if implementation is not None:
            self.require_keys(implementation, ["status", "implemented_by", "implemented_at", "changes"], f"{path}.implementation")
            implementation_state = implementation.get("status")
            self.enum(implementation_state, IMPLEMENTATION_STATES, f"{path}.implementation.status", "IMPLEMENTATION_STATUS")
            changes = self.require_list(implementation.get("changes"), f"{path}.implementation.changes") or []
            if implementation_state in {"in_progress", "completed"}:
                self.nonempty(implementation.get("implemented_by"), f"{path}.implementation.implemented_by")
                self.valid_time(implementation.get("implemented_at"), f"{path}.implementation.implemented_at")
            if implementation_state != "not_started" and decision_state != "approved":
                self.error("UNAPPROVED_CHANGE", f"{path}.implementation.status", "存在实施活动，但条目未获责任决策者批准。")
            if decision_state in {"rejected", "deferred"} and changes:
                self.error("DECISION_CHANGE_CONFLICT", f"{path}.implementation.changes", "拒绝或延后条目不得包含实际变更。")
            if implementation_state == "completed" and not changes and "response_only" not in action_types:
                self.warn("COMPLETED_WITHOUT_CHANGE", f"{path}.implementation.changes", "实施状态为 completed，但没有变更记录。")
            self.item_change_ids[item_id] = set()
            for change_index, change in enumerate(changes):
                change_path = f"{path}.implementation.changes[{change_index}]"
                chg = self.require_dict(change, change_path)
                if chg is None:
                    continue
                self.require_keys(chg, ["change_id", "artifact_id", "location", "change_type", "before", "after", "decision_gate_id"], change_path)
                change_id = chg.get("change_id")
                if not isinstance(change_id, str) or not change_id:
                    self.error("CHANGE_ID_EMPTY", f"{change_path}.change_id", "变更编号不能为空。")
                elif change_id in self.change_owner:
                    self.error("CHANGE_ID_DUPLICATE", f"{change_path}.change_id", f"重复变更编号：{change_id}。")
                else:
                    self.change_owner[change_id] = item_id
                    self.item_change_ids[item_id].add(change_id)
                if chg.get("artifact_id") not in self.all_artifact_ids:
                    self.error("CHANGE_ARTIFACT_UNKNOWN", f"{change_path}.artifact_id", f"未知变更目标文件：{chg.get('artifact_id')}。")
                self.nonempty(chg.get("location"), f"{change_path}.location")
                self.nonempty(chg.get("change_type"), f"{change_path}.change_type")
                self.nonempty(chg.get("decision_gate_id"), f"{change_path}.decision_gate_id")
                if decision is not None and decision.get("decision_gate_id") and chg.get("decision_gate_id") != decision.get("decision_gate_id"):
                    self.error("CHANGE_GATE_MISMATCH", f"{change_path}.decision_gate_id", "变更引用的决定门与条目决定不一致。")
                approved_artifacts = set(decision.get("approved_artifact_ids", [])) if isinstance(decision, dict) else set()
                if decision_state == "approved" and approved_artifacts and chg.get("artifact_id") not in approved_artifacts:
                    self.error("CHANGE_OUTSIDE_APPROVED_ARTIFACTS", f"{change_path}.artifact_id", "变更目标超出条目批准的文件范围。")

        response = self.require_dict(item.get("formal_response"), f"{path}.formal_response")
        if response is not None:
            self.require_keys(response, ["required", "status", "text", "disposition", "change_ids", "locations"], f"{path}.formal_response")
            response_state = response.get("status")
            self.enum(response_state, RESPONSE_STATES, f"{path}.formal_response.status", "RESPONSE_STATUS")
            self.enum(response.get("disposition"), DISPOSITIONS, f"{path}.formal_response.disposition", "RESPONSE_DISPOSITION")
            refs = self.require_list(response.get("change_ids"), f"{path}.formal_response.change_ids") or []
            for ref_index, change_id in enumerate(refs):
                self.response_refs.append((item_id, str(change_id), f"{path}.formal_response.change_ids[{ref_index}]"))
            if response.get("required") is True and response_state == "completed":
                self.nonempty(response.get("text"), f"{path}.formal_response.text")
            if response.get("required") is False and response_state not in {"not_required", "not_started"}:
                self.warn("UNNEEDED_RESPONSE", f"{path}.formal_response.status", "回应被标记为非必需，但状态显示已编写。")

        verification = self.require_dict(item.get("verification"), f"{path}.verification")
        if verification is not None:
            self.require_keys(verification, ["status", "verified_by", "verified_at", "checks", "notes"], f"{path}.verification")
            self.enum(verification.get("status"), VERIFICATION_STATES, f"{path}.verification.status", "VERIFICATION_STATUS")

    def _validate_cross_references(self, value: Any) -> None:
        items = value if isinstance(value, list) else []
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                continue
            item_id = item.get("item_id")
            for rel_index, relation in enumerate(item.get("relations", [])):
                if not isinstance(relation, dict):
                    continue
                target = relation.get("target_item_id")
                if target not in self.item_ids:
                    self.error("RELATION_TARGET_UNKNOWN", f"$.items[{index}].relations[{rel_index}].target_item_id", f"未知关联条目：{target}。")
        for item_id, change_id, path in self.response_refs:
            if change_id not in self.change_owner:
                self.error("RESPONSE_CHANGE_UNKNOWN", path, f"回应引用未知变更编号：{change_id}。")
            elif self.change_owner[change_id] != item_id:
                self.error("RESPONSE_CHANGE_WRONG_ITEM", path, f"变更 {change_id} 属于其他反馈条目。")

    def _validate_gates(self, gates: list[Any], ledger: dict[str, Any]) -> dict[str, dict[str, Any]]:
        gate_map: dict[str, dict[str, Any]] = {}
        for gate_index, gate_value in enumerate(gates):
            base = f"$gate[{gate_index}]"
            gate = self.require_dict(gate_value, base)
            if gate is None:
                continue
            self.require_keys(gate, ["protocol", "protocol_version", "gate_id", "ledger_id", "decision_maker", "scope", "preconditions", "unresolved_conflicts", "decision", "execution_allowed", "attestation"], base)
            gate_id = gate.get("gate_id")
            if not isinstance(gate_id, str) or not gate_id:
                self.error("GATE_ID_EMPTY", f"{base}.gate_id", "决定门编号不能为空。")
                continue
            if gate_id in gate_map:
                self.error("GATE_ID_DUPLICATE", f"{base}.gate_id", f"重复决定门编号：{gate_id}。")
            gate_map[gate_id] = gate
            if gate.get("ledger_id") != ledger.get("ledger_id"):
                self.error("GATE_LEDGER_MISMATCH", f"{base}.ledger_id", "决定门与台账标识不一致。")
            if gate.get("protocol") != "formal-revision-interchange":
                self.error("GATE_PROTOCOL", f"{base}.protocol", "决定门协议标识无效。")
            gate_decision_maker = self.require_dict(gate.get("decision_maker"), f"{base}.decision_maker") or {}
            self.require_keys(gate_decision_maker, ["id", "role", "authority_scope"], f"{base}.decision_maker")
            if self.level >= STAGE_ORDER["execution"] and gate.get("template") is True:
                self.error("GATE_TEMPLATE_ACTIVE", f"{base}.template", "模板决定门不能授权实施。")
            scope = self.require_dict(gate.get("scope"), f"{base}.scope") or {}
            scope_items = set(scope.get("item_ids", [])) if isinstance(scope.get("item_ids"), list) else set()
            scope_artifacts = set(scope.get("artifact_ids", [])) if isinstance(scope.get("artifact_ids"), list) else set()
            for item_id in scope_items:
                if item_id not in self.item_ids:
                    self.error("GATE_ITEM_UNKNOWN", f"{base}.scope.item_ids", f"决定门包含未知条目：{item_id}。")
            for artifact_id in scope_artifacts:
                if artifact_id not in self.all_artifact_ids:
                    self.error("GATE_ARTIFACT_UNKNOWN", f"{base}.scope.artifact_ids", f"决定门包含未知文件：{artifact_id}。")
            decision = self.require_dict(gate.get("decision"), f"{base}.decision") or {}
            approved = set(decision.get("approved_item_ids", [])) if isinstance(decision.get("approved_item_ids"), list) else set()
            rejected = set(decision.get("rejected_item_ids", [])) if isinstance(decision.get("rejected_item_ids"), list) else set()
            deferred = set(decision.get("deferred_item_ids", [])) if isinstance(decision.get("deferred_item_ids"), list) else set()
            if (approved & rejected) or (approved & deferred) or (rejected & deferred):
                self.error("GATE_DECISION_OVERLAP", f"{base}.decision", "批准、拒绝和延后条目不得重叠。")
            if not (approved | rejected | deferred).issubset(scope_items):
                self.error("GATE_DECISION_OUTSIDE_SCOPE", f"{base}.decision", "决定条目超出决定门范围。")
            if self.level >= STAGE_ORDER["execution"] and gate.get("execution_allowed") is True:
                self.nonempty(gate_decision_maker.get("id"), f"{base}.decision_maker.id")
                self.nonempty(gate_decision_maker.get("role"), f"{base}.decision_maker.role")
                self.nonempty(gate_decision_maker.get("authority_scope"), f"{base}.decision_maker.authority_scope")
                if self.decision_maker_id and gate_decision_maker.get("id") != self.decision_maker_id:
                    self.error("GATE_DECISION_MAKER_MISMATCH", f"{base}.decision_maker.id", "决定门责任人不符合台账登记。")
                preconditions = self.require_dict(gate.get("preconditions"), f"{base}.preconditions") or {}
                for key in ("source_lock_verified", "analysis_complete", "relations_reviewed", "conditions_satisfied"):
                    if preconditions.get(key) is not True:
                        self.error("GATE_PRECONDITION", f"{base}.preconditions.{key}", "允许实施前必须为 true。")
                conflicts = gate.get("unresolved_conflicts")
                if not isinstance(conflicts, list) or conflicts:
                    self.error("GATE_CONFLICTS", f"{base}.unresolved_conflicts", "允许实施时不得存在未解决冲突。")
                if decision.get("status") not in {"approved", "partial_approval"}:
                    self.error("GATE_DECISION_STATUS", f"{base}.decision.status", "允许实施时决定状态必须为 approved 或 partial_approval。")
                self.nonempty(decision.get("issued_by"), f"{base}.decision.issued_by")
                self.valid_time(decision.get("issued_at"), f"{base}.decision.issued_at")
                self.nonempty(decision.get("instruction"), f"{base}.decision.instruction")
                if gate_decision_maker.get("id") and decision.get("issued_by") != gate_decision_maker.get("id"):
                    self.error("GATE_ISSUER_MISMATCH", f"{base}.decision.issued_by", "决定签发人不符合决定门登记的责任决策者。")
                self.nonempty(gate.get("attestation"), f"{base}.attestation")
        return gate_map

    def _validate_execution_coverage(self, value: Any, gate_map: dict[str, dict[str, Any]], gates_provided: bool) -> None:
        items = value if isinstance(value, list) else []
        if self.level >= STAGE_ORDER["execution"] and not gates_provided:
            self.warn("GATE_FILE_NOT_PROVIDED", "$", "未提供独立决定门文件；仅依据条目级决定记录核查。")
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                continue
            implementation = item.get("implementation", {})
            decision = item.get("decision", {})
            impl_state = implementation.get("status") if isinstance(implementation, dict) else None
            if impl_state not in {"in_progress", "completed"}:
                continue
            gate_id = decision.get("decision_gate_id") if isinstance(decision, dict) else None
            if not gates_provided:
                continue
            gate = gate_map.get(gate_id)
            if gate is None:
                self.error("IMPLEMENTATION_GATE_MISSING", f"$.items[{index}].decision.decision_gate_id", f"找不到实施所引用的决定门：{gate_id}。")
                continue
            approved = set(gate.get("decision", {}).get("approved_item_ids", []))
            if item.get("item_id") not in approved:
                self.error("IMPLEMENTATION_OUTSIDE_GATE", f"$.items[{index}].implementation", "实施条目未列入决定门批准范围。")
            if gate.get("execution_allowed") is not True:
                self.error("GATE_CLOSED", f"$.items[{index}].implementation", "决定门未允许实施。")

    def _validate_release(self, ledger: dict[str, Any]) -> None:
        if self.level < STAGE_ORDER["release"]:
            return
        items = ledger.get("items", []) if isinstance(ledger.get("items"), list) else []
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                continue
            path = f"$.items[{index}]"
            decision = item.get("decision", {})
            implementation = item.get("implementation", {})
            response = item.get("formal_response", {})
            verification = item.get("verification", {})
            decision_state = decision.get("status")
            implementation_state = implementation.get("status")
            if decision_state == "pending":
                self.error("RELEASE_PENDING_DECISION", f"{path}.decision.status", "释放前不得存在待决条目；请明确批准、拒绝或延后。")
            if decision_state == "approved" and implementation_state not in {"completed", "not_required"}:
                self.error("RELEASE_IMPLEMENTATION_INCOMPLETE", f"{path}.implementation.status", "已批准条目尚未完成实施。")
            if decision_state in {"rejected", "deferred"} and implementation_state not in {"not_started", "not_required"}:
                self.error("RELEASE_DECISION_CONFLICT", f"{path}.implementation.status", "拒绝或延后条目存在实施活动。")
            required = response.get("required") is True
            if required and response.get("status") != "completed":
                self.error("RELEASE_RESPONSE_INCOMPLETE", f"{path}.formal_response.status", "需要回应的条目尚未完成正式回应。")
            if not required and response.get("status") != "not_required":
                self.error("RELEASE_RESPONSE_STATUS", f"{path}.formal_response.status", "无需回应的条目在释放时应标记为 not_required。")
            if required and isinstance(response.get("text"), str) and PLACEHOLDER_RE.search(response.get("text", "")):
                self.error("RESPONSE_PLACEHOLDER", f"{path}.formal_response.text", "正式回应仍含临时占位符。")
            actual_changes = self.item_change_ids.get(str(item.get("item_id")), set())
            response_changes = set(response.get("change_ids", [])) if isinstance(response.get("change_ids"), list) else set()
            if required and actual_changes != response_changes:
                missing = sorted(actual_changes - response_changes)
                extra = sorted(response_changes - actual_changes)
                self.error("RESPONSE_CHANGE_SET_MISMATCH", f"{path}.formal_response.change_ids", f"回应与实改链接不一致；遗漏={missing}，多余={extra}。")
            locations = response.get("locations", []) if isinstance(response.get("locations"), list) else []
            if response_changes and not any(isinstance(loc, str) and loc.strip() for loc in locations):
                self.error("RESPONSE_LOCATION_EMPTY", f"{path}.formal_response.locations", "回应引用实际变更时必须提供可核查位置。")
            if verification.get("status") != "completed":
                self.error("RELEASE_VERIFICATION_INCOMPLETE", f"{path}.verification.status", "条目核查尚未完成。")
            else:
                self.nonempty(verification.get("verified_by"), f"{path}.verification.verified_by")
                self.valid_time(verification.get("verified_at"), f"{path}.verification.verified_at")
        release = self.require_dict(ledger.get("release"), "$.release")
        if release is None:
            return
        if release.get("status") not in {"verified", "released"}:
            self.error("RELEASE_STATUS", "$.release.status", "release 阶段的总状态必须为 verified 或 released。")
        self.nonempty(release.get("verified_by"), "$.release.verified_by")
        self.valid_time(release.get("verified_at"), "$.release.verified_at")
        if release.get("status") == "released":
            self.nonempty(release.get("released_by"), "$.release.released_by")
            self.valid_time(release.get("released_at"), "$.release.released_at")


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        raise ValueError(f"文件不存在：{path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON 语法错误：{path}:{exc.lineno}:{exc.colno}：{exc.msg}") from exc
    except OSError as exc:
        raise ValueError(f"无法读取文件：{path}：{exc}") from exc


def make_valid_fixture() -> tuple[dict[str, Any], dict[str, Any]]:
    verbatim = "请统一核心术语，并同步更新关联附件。"
    now = "2026-01-02T03:04:05Z"
    ledger: dict[str, Any] = {
        "protocol": "formal-revision-interchange",
        "protocol_version": "1.0",
        "template": False,
        "ledger_id": "LEDGER-TEST",
        "task": {
            "title": "正式文件修订测试",
            "scope": "主文件及其附件",
            "status": "verified",
            "created_at": now,
            "updated_at": now,
            "decision_maker": {"id": "OWNER-1", "role": "责任负责人", "authority_scope": "全部测试材料"},
            "formal_recipient": "外部接收方",
        },
        "source_lock": {
            "locked": True,
            "locked_at": now,
            "locked_by": "OP-1",
            "artifacts": [
                {"artifact_id": "ART-1", "role": "baseline", "path_or_uri": "baseline.docx", "version": "v1", "content_sha256": "0" * 64, "lock_note": ""},
                {"artifact_id": "FB-1", "role": "feedback_source", "path_or_uri": "feedback.docx", "version": "v1", "content_sha256": "1" * 64, "lock_note": ""},
            ],
        },
        "working_artifacts": [
            {"artifact_id": "WORK-1", "source_artifact_id": "ART-1", "path_or_uri": "working.docx", "status": "completed", "content_sha256": "2" * 64}
        ],
        "items": [
            {
                "item_id": "ITEM-1",
                "sequence": 1,
                "source": {
                    "artifact_id": "FB-1", "source_label": "反馈方", "original_locator": "第1条",
                    "verbatim": verbatim, "sha256": hashlib.sha256(verbatim.encode("utf-8")).hexdigest(),
                    "raw_snapshot_ref": "feedback.docx#1", "normalization_note": "",
                },
                "translation": {"required": False, "status": "not_required", "text": ""},
                "semantic_location": {
                    "status": "distributed", "artifact_ids": ["ART-1"], "anchors": ["核心术语"],
                    "coordinate_reliability": "verified", "original_coordinates": "第2节",
                    "rationale": "该术语同时出现在主文件和附件。", "ambiguities": [],
                },
                "interpretation": {"core_issue": "术语不一致", "requested_outcome": "统一术语并同步附件", "constraints": []},
                "classification": {
                    "action_types": ["direct_content_revision", "visual_or_structure"],
                    "requires_external_research": False, "requires_data_or_computation": False,
                    "requires_visual_or_structure_change": True, "requires_decision": True, "risk_level": "low",
                },
                "relations": [],
                "consultations": [],
                "recommendation": {
                    "proposed_action": "统一术语并同步附件标签", "alternatives": [],
                    "affected_artifact_ids": ["WORK-1"], "dependencies": [], "risks": [],
                    "rationale": "统一后可消除跨文件歧义。",
                },
                "decision": {
                    "status": "approved", "decided_by": "OWNER-1", "decided_at": now,
                    "instruction": "按建议统一", "approved_artifact_ids": ["WORK-1"],
                    "conditions": [], "decision_gate_id": "GATE-1",
                },
                "implementation": {
                    "status": "completed", "implemented_by": "OP-1", "implemented_at": now,
                    "changes": [
                        {"change_id": "CHG-1", "artifact_id": "WORK-1", "location": "第2节及附件标签", "change_type": "replace", "before": "旧术语", "after": "统一术语", "decision_gate_id": "GATE-1"}
                    ],
                },
                "formal_response": {
                    "required": True, "status": "completed", "text": "已统一相关术语并同步附件。",
                    "disposition": "accepted", "change_ids": ["CHG-1"], "locations": ["第2节及附件标签"],
                },
                "verification": {"status": "completed", "verified_by": "QA-1", "verified_at": now, "checks": ["术语一致"], "notes": ""},
                "export_policy": {"default": "internal_only", "formal_response_allowed_fields": ["formal_response.text"], "deliverable_allowed_fields": [], "restricted_fields": ["consultations"]},
            }
        ],
        "release": {"status": "verified", "verified_by": "QA-1", "verified_at": now, "released_by": "", "released_at": None, "notes": ""},
    }
    gate: dict[str, Any] = {
        "protocol": "formal-revision-interchange", "protocol_version": "1.0", "template": False,
        "gate_id": "GATE-1", "ledger_id": "LEDGER-TEST", "generated_at": now,
        "decision_maker": {"id": "OWNER-1", "role": "责任负责人", "authority_scope": "全部测试材料"},
        "scope": {"item_ids": ["ITEM-1"], "artifact_ids": ["WORK-1"]},
        "preconditions": {"source_lock_verified": True, "analysis_complete": True, "relations_reviewed": True, "conditions_satisfied": True},
        "unresolved_conflicts": [],
        "decision": {"status": "approved", "approved_item_ids": ["ITEM-1"], "rejected_item_ids": [], "deferred_item_ids": [], "conditions": [], "issued_by": "OWNER-1", "issued_at": now, "instruction": "按建议统一"},
        "execution_allowed": True,
        "attestation": "责任决策者已确认范围和实施条件。",
    }
    return ledger, gate


def run_self_test() -> int:
    valid_ledger, valid_gate = make_valid_fixture()
    valid_validator = LedgerValidator("release")
    valid_diags = valid_validator.validate(valid_ledger, [valid_gate])
    valid_errors = [diag for diag in valid_diags if diag.severity == "error"]
    if valid_errors:
        print("[自测失败] 有效样例被错误拒绝：")
        print_diagnostics(valid_diags)
        return 1

    invalid = copy.deepcopy(valid_ledger)
    invalid["items"][0]["source"]["sha256"] = "f" * 64
    invalid["items"][0]["decision"]["status"] = "pending"
    invalid["items"][0]["relations"] = [{"type": "depends_on", "target_item_id": "MISSING", "rationale": "测试"}]
    invalid["items"][0]["formal_response"]["change_ids"] = ["UNKNOWN"]
    invalid_validator = LedgerValidator("release")
    invalid_diags = invalid_validator.validate(invalid, [valid_gate])
    codes = {diag.code for diag in invalid_diags if diag.severity == "error"}
    expected = {"SOURCE_HASH_MISMATCH", "UNAPPROVED_CHANGE", "RELATION_TARGET_UNKNOWN", "RESPONSE_CHANGE_UNKNOWN"}
    missing = sorted(expected - codes)
    if missing:
        print(f"[自测失败] 无效样例未触发预期诊断：{', '.join(missing)}")
        print_diagnostics(invalid_diags)
        return 1
    print("[自测通过] 有效样例通过 release 校验。")
    print("[自测通过] 无效样例被识别，核心错误码：" + ", ".join(sorted(expected)))
    return 0


def print_diagnostics(diagnostics: list[Diagnostic]) -> None:
    labels = {"error": "错误", "warning": "警告"}
    for diag in diagnostics:
        print(f"[{labels.get(diag.severity, diag.severity)}] {diag.code} {diag.path}: {diag.message}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="校验正式修订台账、决定门和回应—实改证据链。")
    parser.add_argument("ledger", nargs="?", type=Path, help="修订台账 JSON 文件")
    parser.add_argument("--decision-gate", action="append", default=[], type=Path, help="决定门 JSON；可重复提供")
    parser.add_argument("--stage", choices=tuple(STAGE_ORDER), default="analysis", help="校验阶段，默认 analysis")
    parser.add_argument("--strict", action="store_true", help="将警告视为失败")
    parser.add_argument("--verify-files", action="store_true", help="复算可访问的本地源文件 SHA-256")
    parser.add_argument("--json", action="store_true", dest="json_output", help="以 JSON 输出诊断")
    parser.add_argument("--self-test", action="store_true", help="运行内置正反样例自测")
    args = parser.parse_args(argv)

    if args.self_test:
        return run_self_test()
    if args.ledger is None:
        parser.error("请提供台账路径，或使用 --self-test。")

    try:
        ledger = load_json(args.ledger)
        gates = [load_json(path) for path in args.decision_gate]
    except ValueError as exc:
        print(f"[错误] JSON_INPUT $: {exc}", file=sys.stderr)
        return 2

    validator = LedgerValidator(args.stage, verify_files=args.verify_files, base_dir=args.ledger.parent)
    diagnostics = validator.validate(ledger, gates)
    errors = [diag for diag in diagnostics if diag.severity == "error"]
    warnings = [diag for diag in diagnostics if diag.severity == "warning"]
    passed = not errors and not (args.strict and warnings)

    if args.json_output:
        print(json.dumps({"passed": passed, "stage": args.stage, "errors": len(errors), "warnings": len(warnings), "diagnostics": [asdict(diag) for diag in diagnostics]}, ensure_ascii=False, indent=2))
    else:
        if diagnostics:
            print_diagnostics(diagnostics)
        print(f"校验结果：{'通过' if passed else '未通过'}；阶段={args.stage}；错误={len(errors)}；警告={len(warnings)}。")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
