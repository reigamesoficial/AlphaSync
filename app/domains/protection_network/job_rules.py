from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any


def _normalize_text(value: str | None) -> str:
    if not value:
        return ""

    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.lower().strip()
    value = re.sub(r"\s+", " ", value)
    return value


def _deep_get(source: dict[str, Any], *keys: str, default=None):
    current: Any = source
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
        if current is None:
            return default
    return current


@dataclass(slots=True)
class ProtectionNetworkJobRuleResult:
    blocked: bool = False
    message: str | None = None
    matched_rule_name: str | None = None
    price_per_m2_override: float | None = None
    minimum_order_value_override: float | None = None
    visit_fee_override: float | None = None
    allowed_mesh_types: list[str] | None = None
    forced_mesh_type: str | None = None
    allowed_colors: list[str] | None = None
    extra_context: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "blocked": self.blocked,
            "message": self.message,
            "matched_rule_name": self.matched_rule_name,
            "price_per_m2_override": self.price_per_m2_override,
            "minimum_order_value_override": self.minimum_order_value_override,
            "visit_fee_override": self.visit_fee_override,
            "allowed_mesh_types": self.allowed_mesh_types,
            "forced_mesh_type": self.forced_mesh_type,
            "allowed_colors": self.allowed_colors,
            "extra_context": self.extra_context or {},
        }


def get_job_rules_config(company) -> dict[str, Any]:
    extra_settings = {}
    if getattr(company, "settings", None) and getattr(company.settings, "extra_settings", None):
        extra_settings = company.settings.extra_settings or {}

    return _deep_get(extra_settings, "job_rules", default={}) or {}


def _rule_matches_address(rule: dict[str, Any], normalized_address: str) -> bool:
    terms = rule.get("match_terms") or []
    if not terms:
        return False

    normalized_terms = [_normalize_text(term) for term in terms if term]
    return any(term and term in normalized_address for term in normalized_terms)


def resolve_address_rule(company, address: str | None) -> ProtectionNetworkJobRuleResult:
    normalized_address = _normalize_text(address)
    if not normalized_address:
        return ProtectionNetworkJobRuleResult()

    job_rules_cfg = get_job_rules_config(company)
    special_addresses = job_rules_cfg.get("special_addresses") or []

    for rule in special_addresses:
        if not isinstance(rule, dict):
            continue

        if not _rule_matches_address(rule, normalized_address):
            continue

        return ProtectionNetworkJobRuleResult(
            blocked=bool(rule.get("blocked", False)),
            message=rule.get("message"),
            matched_rule_name=rule.get("name"),
            price_per_m2_override=rule.get("price_per_m2_override"),
            minimum_order_value_override=rule.get("minimum_order_value_override"),
            visit_fee_override=rule.get("visit_fee_override"),
            allowed_mesh_types=rule.get("allowed_mesh_types"),
            forced_mesh_type=rule.get("forced_mesh_type"),
            allowed_colors=rule.get("allowed_colors"),
            extra_context=rule.get("extra_context") or {},
        )

    return ProtectionNetworkJobRuleResult()


def validate_color_for_rule(
    *,
    selected_color: str,
    rule_result: ProtectionNetworkJobRuleResult,
) -> tuple[bool, str | None]:
    if not rule_result.allowed_colors:
        return True, None

    normalized_selected = _normalize_text(selected_color)
    normalized_allowed = {_normalize_text(color) for color in rule_result.allowed_colors}

    if normalized_selected in normalized_allowed:
        return True, None

    return (
        False,
        f"Para este endereço, as cores permitidas são: {', '.join(rule_result.allowed_colors)}.",
    )


def validate_mesh_for_rule(
    *,
    selected_mesh: str,
    rule_result: ProtectionNetworkJobRuleResult,
) -> tuple[bool, str | None]:
    if rule_result.forced_mesh_type:
        if _normalize_text(selected_mesh) != _normalize_text(rule_result.forced_mesh_type):
            return (
                False,
                f"Para este endereço, a malha obrigatória é {rule_result.forced_mesh_type}.",
            )

    if rule_result.allowed_mesh_types:
        normalized_selected = _normalize_text(selected_mesh)
        normalized_allowed = {_normalize_text(mesh) for mesh in rule_result.allowed_mesh_types}
        if normalized_selected not in normalized_allowed:
            return (
                False,
                f"Para este endereço, as malhas permitidas são: {', '.join(rule_result.allowed_mesh_types)}.",
            )

    return True, None