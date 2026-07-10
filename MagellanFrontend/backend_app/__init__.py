from pathlib import Path

# Allow `backend_app` package imports to resolve modules moved to the MagellanFrontend root.
__path__.append(str(Path(__file__).resolve().parent.parent))

from pathlib import Path

# Preserve compatibility for imports like `from backend_app import app`
# while the real backend modules live in the repo root `backend/` folder.
__path__.append(str(Path(__file__).resolve().parent.parent.parent / "backend"))

from .app import app

__all__ = ["app"]
