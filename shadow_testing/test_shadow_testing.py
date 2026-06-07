#!/usr/bin/env python3
"""Unit tests for the shadow-testing comparison helpers."""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from shadow_testing.shadow_compare import build_shadow_report


class ShadowTestingTest(unittest.TestCase):
    def test_build_shadow_report(self):
        payload = json.loads((ROOT / "Sample_Input" / "example-input.json").read_text())
        report = build_shadow_report(
            query=payload["query"],
            payload=payload,
        )
        self.assertEqual(report["shadowFramework"], "Diffy")
        self.assertEqual(report["gapType"], "query_vocabulary_gap")
        self.assertEqual(report["assessment"]["state"], "warn")
        self.assertIn("docsDelta", report["comparisonSummary"])
        self.assertGreater(report["comparisonSummary"]["candidateRawResponseDiffCount"], 0)
        self.assertGreater(
            report["comparisonSummary"]["candidateRawResponseDiffCount"],
            report["comparisonSummary"]["candidateResponseDiffCount"],
        )
        self.assertGreater(report["responseDiffSummary"]["diffCount"], 0)
        self.assertGreater(report["noiseDiffSummary"]["diffCount"], 0)
        self.assertEqual(report["assessment"]["secondaryMode"], "explicit")
        self.assertTrue(report["actions"])


if __name__ == "__main__":
    unittest.main()
