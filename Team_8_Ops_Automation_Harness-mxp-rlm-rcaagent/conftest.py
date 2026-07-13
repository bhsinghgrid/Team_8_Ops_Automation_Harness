import os
import sys

# Ensure the application package is importable for tests
ROOT = os.path.dirname(__file__)
PROJECT_ROOT = os.path.join(ROOT, "Magellan-rca-engine-backend")
if PROJECT_ROOT not in sys.path:
	sys.path.insert(0, PROJECT_ROOT)

