from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from filelock import FileLock

from app.schemas.signal_schema import RuleDiffRequest


class RuleStateError(ValueError):
    pass


class RuleStateManager:

    def __init__(self, rules_path: Optional[Path] = None):
        self.rules_path = rules_path or Path(__file__).resolve().parents[2] / "mock-data" / "rules" / "rules.json"
        self.lock = FileLock(str(self.rules_path) + ".lock")

    def load_rules(self) -> List[Dict[str, Any]]:
        with self.lock:
            return deepcopy(self._read_state().get("rules", []))

    def get_rule(self, rule_id: str) -> Optional[Dict[str, Any]]:
        with self.lock:
            for rule in self._read_state().get("rules", []):
                if rule.get("rule_id") == rule_id:
                    return deepcopy(rule)
        return None

    def save_rule(self, rule: Dict[str, Any]) -> None:
        with self.lock:
            state = self._read_state()
            rules = state.setdefault("rules", [])
            for index, existing in enumerate(rules):
                if existing.get("rule_id") == rule.get("rule_id"):
                    rules[index] = deepcopy(rule)
                    break
            else:
                rules.append(deepcopy(rule))
            self._bump_version(state)
            self._write_state(state)

    def delete_rule(self, rule_id: str) -> bool:
        with self.lock:
            state = self._read_state()
            rules = state.setdefault("rules", [])
            original_count = len(rules)
            state["rules"] = [rule for rule in rules if rule.get("rule_id") != rule_id]
            if len(state["rules"]) == original_count:
                return False
            self._bump_version(state)
            self._write_state(state)
            return True

    def apply_diff(self, signal: RuleDiffRequest) -> Optional[Dict[str, Any]]:
        operation = signal.operation.upper()
        with self.lock:
            state = self._read_state()
            rules = state.setdefault("rules", [])
            rule_index = self._find_rule_index(rules, signal.rule_id)

            if operation == "INSERT":
                if rule_index is not None:
                    raise RuleStateError(f"Rule {signal.rule_id} already exists")
                updated_rule = self._rule_from_after_state(signal)
                rules.append(updated_rule)
                self._bump_version(state)
                self._write_state(state)
                return deepcopy(updated_rule)

            if operation == "UPDATE":
                if rule_index is None:
                    raise RuleStateError(f"Rule {signal.rule_id} was not found")
                if not signal.after_state:
                    raise RuleStateError(f"UPDATE for rule {signal.rule_id} requires after_state")

                updated_rule = deepcopy(rules[rule_index])
                fields = signal.changed_fields or list(signal.after_state.keys())
                for field in fields:
                    if field in signal.after_state:
                        updated_rule[field] = deepcopy(signal.after_state[field])
                rules[rule_index] = updated_rule
                self._bump_version(state)
                self._write_state(state)
                return deepcopy(updated_rule)

            if operation == "DELETE":
                if rule_index is None:
                    raise RuleStateError(f"Rule {signal.rule_id} was not found")
                deleted_rule = deepcopy(rules.pop(rule_index))
                self._bump_version(state)
                self._write_state(state)
                return deleted_rule

            raise RuleStateError(f"Unsupported rule operation {signal.operation}")

    def _rule_from_after_state(self, signal: RuleDiffRequest) -> Dict[str, Any]:
        if not signal.after_state:
            raise RuleStateError(f"INSERT for rule {signal.rule_id} requires after_state")
        rule = deepcopy(signal.after_state)
        rule.setdefault("rule_id", signal.rule_id)
        rule.setdefault("rule_type", signal.rule_type)
        rule.setdefault("created_by", signal.author)
        return rule

    def _find_rule_index(self, rules: List[Dict[str, Any]], rule_id: str) -> Optional[int]:
        for index, rule in enumerate(rules):
            if rule.get("rule_id") == rule_id:
                return index
        return None

    def _read_state(self) -> Dict[str, Any]:
        return json.loads(self.rules_path.read_text(encoding="utf-8"))

    def _write_state(self, state: Dict[str, Any]) -> None:
        self.rules_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.rules_path.with_suffix(self.rules_path.suffix + ".tmp")
        temp_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
        temp_path.replace(self.rules_path)

    def _bump_version(self, state: Dict[str, Any]) -> None:
        state["version"] = int(state.get("version") or 0) + 1
        state["last_updated"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
