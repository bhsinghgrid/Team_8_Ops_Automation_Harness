import os
import json
import subprocess

# This assumes the Catalog Analysis Agent can be run from a command-line script.
# We will need to adapt this to how the agent is actually invoked.
# For now, let's assume a script `run_catalog_agent.py` exists.
CATALOG_AGENT_SCRIPT = "run_catalog_agent.py" 

class EvaluationHarness:
    def __init__(self, dataset_path):
        self.dataset_path = dataset_path
        self.test_cases = []
        self.results = []

    def load_test_cases(self):
        """Loads test cases from the dataset directory."""
        print("Loading test cases...")
        for filename in os.listdir(self.dataset_path):
            if filename.endswith(".json"):
                filepath = os.path.join(self.dataset_path, filename)
                self.test_cases.append({
                    "name": filename,
                    "filepath": filepath,
                    "expected_outcome": self.get_expected_outcome(filename)
                })
        print(f"Loaded {len(self.test_cases)} test cases.")

    def get_expected_outcome(self, filename):
        """Defines the ground truth for each test case."""
        if filename == "missing_fields.json":
            return {"status": "error", "analysis": "missing_fields"}
        elif filename == "invalid_schema.json":
            return {"status": "error", "analysis": "invalid_schema"}
        elif filename == "malformed.json":
            return {"status": "error", "analysis": "malformed_json"}
        elif filename == "valid.json":
            return {"status": "success", "analysis": "valid"}
        else:
            return {"status": "unknown", "analysis": "unknown"}

    def run_agent(self, filepath):
        """Runs the agent on a given file and returns the output."""
        # This is a placeholder for how the agent might be invoked.
        # We'll need to replace this with the actual command.
        try:
            # We'll need to create `run_catalog_agent.py`
            # that takes a filepath and prints JSON output.
            env = os.environ.copy()
            env["PYTHONPATH"] = "."
            result = subprocess.run(
                ["python3", CATALOG_AGENT_SCRIPT, filepath],
                capture_output=True,
                text=True,
                check=True,
                env=env
            )
            return json.loads(result.stdout)
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            details = str(e)
            if isinstance(e, subprocess.CalledProcessError):
                details += f"\nSTDERR: {e.stderr}"
            return {"status": "error", "analysis": "agent_crash", "details": details}


    def run_evaluation(self):
        """Runs the evaluation across all test cases."""
        if not self.test_cases:
            print("No test cases loaded. Please run load_test_cases() first.")
            return

        for case in self.test_cases:
            print(f"--- Running test case: {case['name']} ---")
            actual_outcome = self.run_agent(case['filepath'])
            
            # The agent returns a dataclass, so we just check one of its fields
            passed = actual_outcome.get("root_cause_candidate") == case["expected_outcome"].get("analysis")

            self.results.append({
                "test_case": case['name'],
                "passed": passed,
                "expected": case['expected_outcome'],
                "actual": actual_outcome
            })
            print(f"Result: {'PASS' if passed else 'FAIL'}")

    def generate_report(self):
        """Generates a summary report of the evaluation results."""
        print("\n--- Evaluation Report ---")
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r['passed'])
        
        if total_tests == 0:
            print("No results to report.")
            return

        print(f"Total tests run: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {passed_tests / total_tests:.2%}")

        print("\n--- Failed Tests ---")
        for result in self.results:
            if not result['passed']:
                print(f"  - Test Case: {result['test_case']}")
                print(f"    Expected: {result['expected']}")
                print(f"    Actual:   {result['actual']}")

if __name__ == "__main__":
    harness = EvaluationHarness("evaluation/dataset/catalog")
    harness.load_test_cases()
    harness.run_evaluation() 
    harness.generate_report()
