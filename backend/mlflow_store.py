import json
import os
import tempfile
from typing import Dict, Any

import mlflow
from mlflow.tracking import MlflowClient


DEFAULT_EXPERIMENT = "Unified Search AI Repair Workflows"


def _tracking_uri() -> str:
    base = os.environ.get("MLFLOW_TRACKING_URI", "http://127.0.0.1:5001")
    # Support basic auth when MLflow server requires it. Use env vars
    # MLFLOW_TRACKING_USERNAME and MLFLOW_TRACKING_PASSWORD (used elsewhere in repo).
    user = os.environ.get("MLFLOW_TRACKING_USERNAME") or os.environ.get("MLFLOW_TRACKING_USER")
    pwd = os.environ.get("MLFLOW_TRACKING_PASSWORD") or os.environ.get("MLFLOW_TRACKING_PASSWORD")
    if user and pwd and base.startswith("http") and "@" not in base:
        # Insert credentials into the URI: http://user:pass@host:port
        parts = base.split("://", 1)
        return f"{parts[0]}://{user}:{pwd}@{parts[1]}"
    return base


def ensure_experiment(name: str = DEFAULT_EXPERIMENT) -> MlflowClient:
    mlflow.set_tracking_uri(_tracking_uri())
    client = MlflowClient()
    exp = client.get_experiment_by_name(name)
    if exp is None:
        client.create_experiment(name)
    return client


def _ensure_workflow_run(client: MlflowClient, workflow_id: str, experiment_name: str = DEFAULT_EXPERIMENT) -> str:
    exp = client.get_experiment_by_name(experiment_name)
    exp_id = exp.experiment_id
    # search for existing run tagged with workflow_id
    runs = client.search_runs([exp_id], filter_string=f"tags.workflow_id = '{workflow_id}'", max_results=1)
    if runs:
        return runs[0].info.run_id

    # create a parent run representing the workflow
    created = client.create_run(exp_id, tags={"workflow_id": workflow_id}, run_name=workflow_id)
    return created.info.run_id


def log_activity_to_mlflow(activity: Dict[str, Any], experiment_name: str = DEFAULT_EXPERIMENT) -> dict:
    """
    Logs a single activity dict into MLflow as a nested run under a workflow-level run.
    Returns a small dict with run ids for verification.
    """
    client = ensure_experiment(experiment_name)
    workflow_id = activity.get("workflow_id", "unknown-workflow")
    parent_run_id = _ensure_workflow_run(client, workflow_id, experiment_name)

    # create a nested run for this activity
    exp = client.get_experiment_by_name(experiment_name)
    run = client.create_run(exp.experiment_id, parent_run_id=parent_run_id, tags={"activity_id": activity.get("activity_id", "")}, run_name=f"activity-{activity.get('activity_id','')}")
    run_id = run.info.run_id

    # log simple metadata as params
    client.log_param(run_id, "workflow_id", workflow_id)
    client.log_param(run_id, "activity_id", activity.get("activity_id", ""))
    client.log_param(run_id, "activity_name", activity.get("activity_name", ""))
    if activity.get("received_at"):
        client.log_param(run_id, "received_at", activity.get("received_at"))

    # log the result payload as an artifact json file
    result = activity.get("result", {})
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tf:
            json.dump(result, tf, indent=2)
            temp_path = tf.name
        client.log_artifact(run_id, temp_path, artifact_path="results")
    finally:
        try:
            os.remove(temp_path)
        except Exception:
            pass

    return {"workflow_run_id": parent_run_id, "activity_run_id": run_id}


def log_workflow_to_mlflow(workflow_id: str, summary: Dict[str, Any], experiment_name: str = DEFAULT_EXPERIMENT) -> dict:
    """
    Logs a workflow-level summary into MLflow. Creates or finds a workflow run and
    logs the provided `summary` as an artifact and tags/params.
    """
    client = ensure_experiment(experiment_name)
    parent_run_id = _ensure_workflow_run(client, workflow_id, experiment_name)

    # Log summary as params and artifact
    try:
        if isinstance(summary, dict):
            for k, v in summary.items():
                # Only log scalar-ish parameters (convert non-scalar to JSON tag)
                if isinstance(v, (str, int, float, bool)):
                    client.log_param(parent_run_id, str(k), str(v))
            # Save full JSON summary as artifact
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tf:
                json.dump(summary, tf, indent=2)
                temp_path = tf.name
            client.log_artifact(parent_run_id, temp_path, artifact_path="workflow_summary")
            try:
                os.remove(temp_path)
            except Exception:
                pass
    except Exception:
        # best-effort logging
        pass

    return {"workflow_run_id": parent_run_id}
