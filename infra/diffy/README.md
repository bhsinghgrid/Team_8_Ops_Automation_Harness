# Diffy Shadow Testing

This folder shows the real Diffy-style shadow-testing topology.

Diffy sits outside the application code as a proxy wrapper:

- `web-app-production-a` is the primary baseline
- `web-app-production-b` is the secondary baseline used to measure noise
- `web-app-candidate-next` is the V-next candidate
- `diffy-proxy` multicasts requests to all three services

The app code here is deliberately tiny:

- the primary and secondary return the same JSON shape
- they differ only in `generated_at`, which Diffy treats as harmless noise
- the candidate intentionally changes `balance_usd` to `balance`, which Diffy flags as a regression

## Run It

From the repo root:

```bash
docker compose -f infra/diffy/docker-compose.yml up --build
```

Then send traffic to the proxy:

```bash
curl http://localhost:8880/api/v1/user/10923
```

Open the Diffy dashboard:

```text
http://localhost:8888
```

The admin console is available at:

```text
http://localhost:8881/admin
```

## Link It To The Agents

If you export or save the Diffy shadow payload to JSON, you can feed it straight into the agent pipeline:

```bash
python3 main.py --shadow-input /path/to/diffy-shadow.json
```

The bridge understands either of these shapes:

- top-level `primary`, `secondary`, `candidate`
- nested `shadowTest.primary`, `shadowTest.secondary`, `shadowTest.candidate`

In the current pipeline, Diffy runs as a post-agent validation step, after the fix plan is generated.

## What This Demonstrates

- The application services do not contain shadow-testing logic.
- Diffy wraps the services and compares responses externally.
- The secondary service is used to identify noisy fields like timestamps.
- The candidate service is checked against the primary after noise suppression.

## How To Adapt It

Replace the demo service image/build with your own service containers, keeping the same three-way topology:

- primary
- secondary
- candidate

If your app needs state changes, point the candidate at an isolated shadow database or write-disabled environment.
