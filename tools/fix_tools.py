"""Deterministic fix-plan tools for the FixPlanAgent pipeline.

These helpers keep the planning, verification, and artifact-writing steps
separate so the agent can compose them in sequence without needing a database
or long-term memory for this repo's current workflow.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from environment.AgentsRLM.ocs_api_calls_fix_loader import load_fix_module


_fix_module = load_fix_module()


def normalize_catalog(catalog: Any) -> dict[str, Any]:
    if isinstance(catalog, dict):
        payload = dict(catalog)
        payload.setdefault("products", [])
        return payload
    if isinstance(catalog, list):
        return {"products": catalog}
    return {"products": []}


def build_fix_plan(query, signals, catalog):
    return _fix_module.build_plan(query, signals, catalog)


def save_fix_files(out_dir: Path, plan):
    _fix_module.save_json(out_dir / "fix-plan.json", plan)
    _fix_module.save_json(out_dir / "catalog-patch.json", plan["catalogPatch"])
    _fix_module.save_json(out_dir / "embedding-refresh-patch.json", plan["embeddingPatch"])
    _fix_module.save_json(out_dir / "autocomplete-synonyms-patch.json", plan["autocompletePatch"])
    _fix_module.save_json(out_dir / "merchandising-rule-patch.json", plan["merchandisingPatch"])


def verify_fix_plan(plan: dict[str, Any]) -> dict[str, Any]:
    checks = [
        {
            "name": "fix_order_defined",
            "passed": bool(plan.get("fixOrder")),
            "details": f"{len(plan.get('fixOrder', []))} steps defined",
        },
        {
            "name": "catalog_patch_structured",
            "passed": isinstance(plan.get("catalogPatch", {}).get("searchableFields", {}).get("add"), list),
            "details": f"{len(plan.get('catalogPatch', {}).get('searchableFields', {}).get('add', []))} searchable field additions planned",
        },
        {
            "name": "autocomplete_patch_structured",
            "passed": isinstance(plan.get("autocompletePatch", {}).get("synonymMappings"), list)
            and isinstance(plan.get("autocompletePatch", {}).get("enableSynonyms"), bool),
            "details": f"{len(plan.get('autocompletePatch', {}).get('synonymMappings', []))} synonym mappings prepared",
        },
        {
            "name": "embedding_patch_structured",
            "passed": isinstance(plan.get("embeddingPatch", {}).get("affectedProductIds"), list)
            and isinstance(plan.get("embeddingPatch", {}).get("refreshEmbeddings"), bool),
            "details": f"{len(plan.get('embeddingPatch', {}).get('affectedProductIds', []))} products queued for embedding refresh",
        },
        {
            "name": "merchandising_patch_structured",
            "passed": isinstance(plan.get("merchandisingPatch", {}).get("rules"), list),
            "details": f"{len(plan.get('merchandisingPatch', {}).get('rules', []))} merchandising rules prepared",
        },
    ]
    status = "ok" if all(check["passed"] for check in checks) else "failed"
    return {
        "status": status,
        "checks": checks,
    }


def _build_applied_catalog(catalog: Any, plan: dict[str, Any]) -> dict[str, Any]:
    payload = normalize_catalog(catalog)
    payload["appliedSearchConfiguration"] = {
        "searchableFields": plan.get("catalogPatch", {})
        .get("searchableFields", {})
        .get("add", []),
        "synonymsEnabled": bool(plan.get("autocompletePatch", {}).get("enableSynonyms")),
        "synonymCount": len(plan.get("autocompletePatch", {}).get("synonymMappings", [])),
        "embeddingRefreshEnabled": bool(plan.get("embeddingPatch", {}).get("refreshEmbeddings")),
        "embeddingRefreshCount": len(plan.get("embeddingPatch", {}).get("affectedProductIds", [])),
        "merchandisingRuleCount": len(plan.get("merchandisingPatch", {}).get("rules", [])),
        "fixOrder": list(plan.get("fixOrder", [])),
    }
    return payload


def apply_fix_plan(
    plan: dict[str, Any],
    *,
    catalog: Any = None,
    fix_dir: str | Path | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Write the fix artifacts and return an execution/verification report."""

    fix_dir_path = Path(fix_dir or "ocs-api-calls/fixes/generated-remediation")
    verification = verify_fix_plan(plan)
    applied_catalog = _build_applied_catalog(catalog, plan)
    report = {
        "status": verification["status"],
        "dryRun": dry_run,
        "applied": not dry_run,
        "artifactDir": str(fix_dir_path),
        "fixOrder": list(plan.get("fixOrder", [])),
        "appliedSearchConfiguration": applied_catalog.get("appliedSearchConfiguration", {}),
        "artifacts": [],
        "verification": verification,
    }

    if dry_run:
        return report

    fix_dir_path.mkdir(parents=True, exist_ok=True)
    save_fix_files(fix_dir_path, plan)

    catalog_snapshot_path = fix_dir_path / "catalog-applied.json"
    report_path = fix_dir_path / "apply-report.json"
    _fix_module.save_json(catalog_snapshot_path, applied_catalog)

    artifacts = [
        {"path": str(fix_dir_path / "fix-plan.json"), "type": "fix-plan"},
        {"path": str(fix_dir_path / "catalog-patch.json"), "type": "catalog-patch"},
        {"path": str(fix_dir_path / "embedding-refresh-patch.json"), "type": "embedding-refresh-patch"},
        {"path": str(fix_dir_path / "autocomplete-synonyms-patch.json"), "type": "autocomplete-patch"},
        {"path": str(fix_dir_path / "merchandising-rule-patch.json"), "type": "merchandising-patch"},
        {"path": str(catalog_snapshot_path), "type": "applied-catalog"},
        {"path": str(report_path), "type": "apply-report"},
    ]

    report["artifacts"] = artifacts
    report["catalogSnapshot"] = str(catalog_snapshot_path)
    report["reportPath"] = str(report_path)
    _fix_module.save_json(report_path, report)
    return report
