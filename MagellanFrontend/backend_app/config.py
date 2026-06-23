import os
from pathlib import Path


def load_env_file(env_path: str = ".env") -> None:
    path = Path(env_path)
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


load_env_file()


FASTAPI_HOST = os.getenv("FASTAPI_HOST", "127.0.0.1")
FASTAPI_PORT = os.getenv("FASTAPI_PORT", "8000")
PUBLIC_BACKEND_URL = os.getenv("PUBLIC_BACKEND_URL", f"http://{FASTAPI_HOST}:{FASTAPI_PORT}")

TEMPORAL_ADDRESS = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
TEMPORAL_NAMESPACE = os.getenv("TEMPORAL_NAMESPACE", "default")
TEMPORAL_WORKFLOWS_URL = os.getenv(
    "TEMPORAL_WORKFLOWS_URL",
    "http://localhost:8233/namespaces/default/workflows",
)
TEMPORAL_TASK_QUEUE = os.getenv("TEMPORAL_TASK_QUEUE", "").strip()
TEMPORAL_ACTION_WORKFLOW_TYPE = os.getenv("TEMPORAL_ACTION_WORKFLOW_TYPE", "").strip()
TEMPORAL_APPROVAL_SIGNAL_NAME = os.getenv("TEMPORAL_APPROVAL_SIGNAL_NAME", "record_approval").strip()
TEMPORAL_APPROVAL_STAGE = os.getenv("TEMPORAL_APPROVAL_STAGE", "post_fix_plan_pre_apply").strip()
TEMPORAL_TLS_ENABLED = os.getenv("TEMPORAL_TLS_ENABLED", "false").lower() == "true"
TEMPORAL_CONNECTION_TIMEOUT_SECONDS = float(os.getenv("TEMPORAL_CONNECTION_TIMEOUT_SECONDS", "5"))

BACKEND_REQUEST_TIMEOUT_SECONDS = float(os.getenv("BACKEND_REQUEST_TIMEOUT_SECONDS", "8"))
DATA_SOURCE_URLS = {
    "runbooks": os.getenv("RUNBOOKS_API_URL", "").strip(),
    "audit": os.getenv("AUDIT_API_URL", "").strip(),
    "query_clusters": os.getenv("QUERY_CLUSTERS_API_URL", "").strip(),
}
RUNBOOK_ACTION_API_URL = os.getenv("RUNBOOK_ACTION_API_URL", "").strip()
DATA_API_BEARER_TOKEN = os.getenv("DATA_API_BEARER_TOKEN", "").strip()

FRONTEND_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "FRONTEND_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]

FRONTEND_ORIGIN_REGEX = os.getenv(
    "FRONTEND_ORIGIN_REGEX",
    r"http://(localhost|127\.0\.0\.1|0\.0\.0\.0):[0-9]+",
)
