#!/usr/bin/env python3
"""Smoke tests for local agent tools."""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.capability_mapping_tools import capability_family, infer_capability_from_signal
from tools.data_gap_tools import classify_data_gap, data_gap_actions, looks_synthetic_query
from tools.index_analysis_tools import diff_index_settings
from tools.metric_tools import metric_value
from tools.owner_tools import build_escalation_path, resolve_owner_chain
from tools.synonym_tools import propose_synonym_mappings


class AgentToolsTest(unittest.TestCase):
    def test_capability_mapping(self):
        capability = infer_capability_from_signal("zero_result_cluster")
        self.assertEqual(capability, "semantic_search")
        self.assertEqual(capability_family("zero_result_cluster", capability), "semantic_retrieval")

    def test_blank_query_mapping(self):
        capability = infer_capability_from_signal("empty_query")
        self.assertEqual(capability, "browse_intent")
        self.assertEqual(capability_family("empty_query", capability), "search_experience")

        owners = resolve_owner_chain("browse_intent")
        self.assertEqual(owners["primary_owner"], "Search experience owner")

    def test_signal_payload_fallbacks(self):
        low_result_count = infer_capability_from_signal(
            {
                "type": "low_result_count",
                "source": "search_api",
                "summary": "Search returned fewer products than the minimum result threshold.",
                "recommendedAction": "Review recall, filters, searchable attributes, and synonym coverage.",
                "metrics": {"minResults": 3, "matchCount": 2},
            }
        )
        self.assertEqual(low_result_count, "search_relevance")
        self.assertEqual(capability_family("low_result_count", low_result_count), "search_experience")

        missing_facets = infer_capability_from_signal(
            {
                "type": "missing_facets",
                "source": "search_api",
                "summary": "Search requested facets but the response contains no facet data.",
                "recommendedAction": "Check facet configuration, filterable fields, and tenant search config.",
                "metrics": {"withFacets": True, "matchCount": 2},
            }
        )
        self.assertEqual(missing_facets, "search_api")
        self.assertEqual(capability_family("missing_facets", missing_facets), "search_experience")

    def test_data_gap_classification(self):
        self.assertTrue(looks_synthetic_query("definitelymissing shoes"))
        gap_type, reason, confidence = classify_data_gap(
            incident_query="hybrid work backpack",
            baseline_docs=10,
            candidate_docs=10,
            baseline_results=0,
            candidate_results=0,
            shadow_status="ok",
            setting_diff={},
        )
        self.assertEqual(gap_type, "query_vocabulary_gap")
        self.assertEqual(confidence, "high")
        self.assertTrue(data_gap_actions(gap_type=gap_type, incident_query="hybrid work backpack"))
        self.assertTrue(data_gap_actions(gap_type="insufficient_shadow_evidence", incident_query="hybrid work backpack"))

    def test_index_diff_and_metric(self):
        diff = diff_index_settings(
            {"searchableAttributes": ["title"], "synonyms": {}},
            {"searchableAttributes": ["title", "description"], "synonyms": {}},
        )
        self.assertIn("searchableAttributes", diff)
        self.assertEqual(metric_value({"ctr": {"value": "0.12"}}, "ctr"), 0.12)

    def test_owner_chain(self):
        owners = resolve_owner_chain("catalog")
        path = build_escalation_path(**owners)
        self.assertEqual(path[0], "Catalog data owner")

        catalog_completeness = resolve_owner_chain("catalog_completeness")
        self.assertEqual(catalog_completeness["primary_owner"], "Catalog data owner")

        search_relevance = resolve_owner_chain("search_relevance")
        self.assertEqual(search_relevance["primary_owner"], "Search relevance owner")

    def test_synonym_proposal(self):
        sample = json.loads((REPO_ROOT / "Sample_Input" / "example-input.json").read_text())
        catalog = json.loads((REPO_ROOT / "src" / "ocs-api-calls" / "sample_runtime" / "catalog.json").read_text())
        mappings = propose_synonym_mappings(
            sample["query"],
            catalog,
            sample.get("queryLogs", []),
        )
        self.assertTrue(mappings)

        backpack = next((mapping for mapping in mappings if mapping["term"] == "backpack"), None)
        self.assertIsNotNone(backpack)
        self.assertIn("bag", backpack["synonyms"])


if __name__ == "__main__":
    unittest.main()
