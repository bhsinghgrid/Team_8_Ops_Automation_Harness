# Runbook_System_Final/deployments/activities.py
"""
Deployment-related Temporal Activities for applying fixes, canary monitoring, and rollbacks.
This module integrates with a mock Kubernetes client for realistic deployment management.
"""

from temporalio.activity import activity_method
import asyncio
from typing import List, Dict, Any
import random

# --- Mock Kubernetes Client (for demonstration purposes) ---
# In a real environment, you would use the official Kubernetes Python client
# to interact with your actual K8s cluster.
class MockKubernetesClient:
    def __init__(self):
        print("[K8s Mock Client]: Initialized.")

    async def apply_deployment(self, runbook_id: str, deployment_manifest: Dict[str, Any]) -> str:
        """Simulates applying a Kubernetes Deployment manifest."""
        print(f"[K8s Mock Client]: Applying deployment for runbook {runbook_id} (Manifest: {deployment_manifest.get('metadata',{})
.get('name')})...")
        await asyncio.sleep(2) # Simulate K8s API call latency
        return "DEPLOYMENT_APPLIED"

    async def get_deployment_status(self, runbook_id: str, deployment_name: str) -> Dict[str, Any]:
        """Simulates getting the status of a Kubernetes Deployment."""
        print(f"[K8s Mock Client]: Getting status for deployment {deployment_name} for runbook {runbook_id}...")
        await asyncio.sleep(1) # Simulate K8s API call latency
        # Simulate a successful deployment after a few calls
        if random.random() < 0.8: # 80% chance of a mock success
            return {"status": "Running", "replicas": 3, "readyReplicas": 3, "reason": "Mock: All pods ready"}
        return {"status": "Progressing", "replicas": 3, "readyReplicas": 2, "reason": "Mock: Waiting for pods"}

    async def rollback_deployment(self, runbook_id: str, deployment_name: str) -> str:
        """Simulates triggering a Kubernetes Deployment rollback."""
        print(f"[K8s Mock Client]: Initiating rollback for deployment {deployment_name} for runbook {runbook_id}...")
        await asyncio.sleep(3) # Simulate K8s API call latency
        return "ROLLBACK_INITIATED"

# Instantiate a single mock Kubernetes client for use by activities
k8s_client = MockKubernetesClient()

# --- Temporal Activities ---

@activity_method
async def apply_fix_activity(runbook_id: str, fix_steps: List[str]) -> str:
    """
    Applies the immediate fix steps defined in the runbook, simulating Kubernetes deployment.
    """
    activity_info = activity_method.info()
    print(f"[Deployment Activity] {activity_info.activity_type} for {runbook_id}: Applying fix steps...")
    
    # Simulate deploying a Kubernetes manifest based on the fix plan
    # In a real system, fix_steps might contain actual K8s YAML or helm commands
    deployment_name = f"magellan-app-{runbook_id[:8]}" # Define the deployment name consistently
    mock_deployment_manifest = {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {"name": deployment_name, "labels": {"runbookId": runbook_id}},
        "spec": {"replicas": 3, "template": {"spec": {"containers": [{"name": "app", "image": "your-search-app:candidate"}]}}}
    }
    deploy_status = await k8s_client.apply_deployment(runbook_id, mock_deployment_manifest)
    
    # Simulate waiting for the deployment to be ready in Kubernetes
    # deployment_name is already defined
    for i in range(1, 6): # Try up to 5 times
        status_response = await k8s_client.get_deployment_status(runbook_id, deployment_name)
        print(f"  [Deployment Activity] {runbook_id}: K8s Deployment status: {status_response.get('status')} ({status_response.get('readyReplicas')}/{status_response.get('replicas')} ready) - {status_response.get('reason')}")
        if status_response.get("status") == "Running" and status_response.get("readyReplicas") == status_response.get("replicas"):
            print(f"  [Deployment Activity] {runbook_id}: Kubernetes deployment {deployment_name} is ready after {i} checks.")
            break
        await asyncio.sleep(2) # Wait before checking again
    else:
        print(f"  [Deployment Activity] {runbook_id}: Kubernetes deployment {deployment_name} not ready in time after {i} checks.")

    print(f"[Deployment Activity] {activity_info.activity_type} for {runbook_id}: Fix steps (Kubernetes) applied.")
    return deploy_status

@activity_method
async def monitor_canary_activity(runbook_id: str, shadow_metrics: Dict[str, Any]) -> str:
    """
    Monitors a canary rollout for performance degradation, simulating integration with K8s and metrics systems.
    Measures error rate, latency, and compares against a stable baseline.
    """
    activity_info = activity_method.info()
    print(f"[Deployment Activity] {activity_info.activity_type} for {runbook_id}: Monitoring canary rollout...")
    print(f"  Analyzing shadow metrics (simulated live comparison): {shadow_metrics}")
    await asyncio.sleep(5) # Simulate real-time monitoring/data fetching from a metrics system

    # --- Simulated Canary Metrics (from article's "Metrics That Matter") ---
    # In a real system, these would come from Prometheus, Datadog, etc.
    stable_baseline_metrics = {
        "error_rate": 0.01,  # 1% errors
        "p99_latency_ms": 180, # 180ms
        "cpu_util_avg": 0.40, # 40% CPU
        "checkout_success_rate": 0.98 # 98% success
    }

    canary_observed_metrics = {
        "error_rate": shadow_metrics.get("errorRate", stable_baseline_metrics["error_rate"] * (1 + random.uniform(-0.1, 0.1))),
        "p99_latency_ms": shadow_metrics.get("latencyDeltaMs", 0) + stable_baseline_metrics["p99_latency_ms"],
        "cpu_util_avg": stable_baseline_metrics["cpu_util_avg"] * (1 + random.uniform(-0.05, 0.05)),
        "checkout_success_rate": stable_baseline_metrics["checkout_success_rate"] * (1 + random.uniform(-0.02, 0.02)),
    }
    
    print(f"  Stable Baseline: {stable_baseline_metrics}")
    print(f"  Canary Observed: {canary_observed_metrics}")

    # --- Automated Canary Analysis (ACA) based on thresholds (Flagger principles) ---
    failed_checks = 0
    analysis_details = []

    # 1. Error Rate Check: > 5% increase warrants investigation
    if canary_observed_metrics["error_rate"] > stable_baseline_metrics["error_rate"] * 1.05: 
        failed_checks += 1
        analysis_details.append(f"❌ Error rate increased from {stable_baseline_metrics['error_rate']:.2%} to {canary_observed_metrics['error_rate']:.2%}")

    # 2. Latency (p99) Check: > 15% increase is a regression
    if canary_observed_metrics["p99_latency_ms"] > stable_baseline_metrics["p99_latency_ms"] * 1.15: 
        failed_checks += 1
        analysis_details.append(f"❌ P99 Latency jumped from {stable_baseline_metrics['p99_latency_ms']}ms to {canary_observed_metrics['p99_latency_ms']:.2f}ms")

    # 3. Saturation (CPU) Check: > 20% increase suggests a leak
    if canary_observed_metrics["cpu_util_avg"] > stable_baseline_metrics["cpu_util_avg"] * 1.20: 
        failed_checks += 1
        analysis_details.append(f"❌ CPU utilization increased from {stable_baseline_metrics['cpu_util_avg']:.2%} to {canary_observed_metrics['cpu_util_avg']:.2%}")

    # 4. Business Metric (Checkout Success Rate) Check: > 1% drop is critical
    if canary_observed_metrics["checkout_success_rate"] < stable_baseline_metrics["checkout_success_rate"] * 0.99: 
        failed_checks += 1
        analysis_details.append(f"❌ Checkout success rate dropped from {stable_baseline_metrics['checkout_success_rate']:.2%} to {canary_observed_metrics['checkout_success_rate']:.2%}")

    # --- Final Decision ---
    if failed_checks == 0:
        print(f"  ✅ Canary analysis passed for {runbook_id}. No regressions detected.")
        return "SUCCESS"
    else:
        print(f"  ⚠️ Canary analysis WARNED for {runbook_id}. {failed_checks} regression(s) detected:")
        for detail in analysis_details:
            print(f"    - {detail}")
        return "FAILURE_METRIC_DROP" # Using existing status for simplicity

@activity_method
async def trigger_rollback_activity(runbook_id: str, reason: str, details: str) -> str:
    """
    Triggers an automated rollback, simulating Kubernetes rollback.
    """
    activity_info = activity_method.info()
    print(f"[Deployment Activity] {activity_info.activity_type} for {runbook_id}: Initiating rollback! Reason: {reason}")
    print(f"  Details: {details}")
    # Simulate Kubernetes rollback command
    await k8s_client.rollback_deployment(runbook_id, f"magellan-app-{runbook_id[:8]}")
    print(f"[Deployment Activity] {activity_info.activity_type} for {runbook_id}: Rollback (Kubernetes) completed.")
    return "ROLLED_BACK_COMPLETED"
