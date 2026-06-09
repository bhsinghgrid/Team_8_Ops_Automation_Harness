# Canary Release Controller — Integration Guide

This guide details how to integrate the **Canary Release Controller (Phase 4: Governed Release Ops)** into a Magellan project built up to **Phase 3 (Evaluation + Shadow Factory)**.

---

## 1. Architectural Relationship

The Canary Release Controller sits at the orchestration tier of the release phase. It manages progressive traffic routing and utilizes the Phase 3 **Feedback Agent** as its validation engine at each rollout tier.

```
          [ Upstream Fix Applied ]
                     │
                     ▼
       ┌───────────────────────────┐
       │ CanaryReleaseController   │ ◄── [ CLI Entrypoint / Orchestrator ]
       └─────┬───────────────┬─────┘
             │ 5%            │ 100%
             ▼               ▼
       ┌───────────────────────────┐
       │  Phase 3 Feedback Agent   │ ◄── [ Runs verification & evaluations ]
       └───────────────────────────┘
```

---

## 2. Integration Checklist

### Step 1: Environment Variables Configuration
Configure the following variables in your staging and production environments (`.env` or system environment):

```bash
# Disable mock mode to allow live OCS API and database connections
OCS_MOCK_MODE=False

# Live OCS URL Configurations
OCS_SEARCH_URL=http://localhost:8534
OCS_INDEXER_URL=http://localhost:8535
OCS_CONFIG_URL=http://localhost:8536
OCS_SUGGEST_URL=http://localhost:8536/suggest

# PostgreSQL connection string for production audit log
DB_CONNECTION_STRING=postgresql://postgres:postgres@localhost:5432/ocs_audit

# Canary-Specific Configurations
CANARY_SOAK_TIME=300       # Seconds to wait at each tier before evaluation (e.g. 5 minutes)
CANARY_MAX_HOLDS=3         # Number of consecutive HOLD decisions before escalating
CANARY_ROUTING_HEADER=X-OCS-Canary-Weight
```

### Step 2: Database Schema Provisioning
The `OCSDatabase` connection helper in `feedback_agent/db.py` automatically initializes tables on startup. When running in a live PostgreSQL environment, the script automatically creates the `canary_releases` table:

```sql
CREATE TABLE IF NOT EXISTS canary_releases (
    id SERIAL PRIMARY KEY,
    incident_id VARCHAR(255),
    query TEXT,
    current_tier INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'PENDING',
    tiers_completed TEXT DEFAULT '[]',
    hold_count INTEGER DEFAULT 0,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    final_decision VARCHAR(50)
);
```

*Note: The database connector automatically translates SQL parameter placeholders (`?` used in SQLite $\rightarrow$ `%s` used in PostgreSQL) depending on the active connection type.*

### Step 3: Triggering the Rollout Loop
Run the Canary Release Controller CLI from your deployment pipeline or orchestration system (e.g., Temporal Workflow activity, Jenkins, or GitHub Actions):

```bash
python3 -m feedback_agent.canary.run_canary --input input.json --output-dir canary_output
```

#### CLI Parameters:
* `--input`: Path to the `input.json` containing the fix plan applied by the upstream agents.
* `--output-dir`: Directory where per-tier feedback logs and the final rollout execution summary are stored.

---

## 3. Handling Rollout Lifecycle States

The controller writes its final summary to `canary_output/canary_release_result.json`. Your outer orchestration loop should read this file and handle the following status outcomes:

| Output Status | Meaning | Action Needed |
| :--- | :--- | :--- |
| **`COMPLETED`** | 100% traffic successfully routed to the candidate config. | Close the incident ticket. |
| **`ROLLED_BACK`** | A regression was caught. OCS configurations were automatically reverted, and the query was logged as `REGRESSED`. | Flag the patch for developer revision. |
| **`HELD`** | Progression paused (max holds reached or warning threshold hit). | Alert the search operations team for manual verification. |

---

## 4. Verification & Testing

To verify the integration locally, you can use Mock Mode:

```bash
# Run in Mock Mode (default)
python3 -m feedback_agent.canary.run_canary --input input.json --output-dir canary_output
```

This will run all 4 tiers (`5%`, `25%`, `50%`, `100%`) instantly (soak time is overridden to `0` seconds in mock mode), writing the evaluation records to SQLite and outputs to the `canary_output/` folder.
