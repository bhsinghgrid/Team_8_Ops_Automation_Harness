import React from 'react';

export const EvidenceAndStats: React.FC = () => {
  return (
    <>
      <section className="credibility-section sysco-evidence" id="credibility-discipline">
        <div className="container">
          <div className="editors-note">
            <div className="editors-label">Validation status</div>
            <div className="editors-body">
              <span className="drop">C</span>
              <strong>Concept architecture.</strong> Prototype, demo, pilot, and production status are not claimed unless explicitly marked. Metrics are illustrative unless tagged <strong>Observed in pilot</strong>; UI screens are demo surfaces until tied to approved workflows.
            </div>
          </div>
          <div className="arch-panel shared">
            <div className="arch-panel-label">Evidence Boundary</div>
            <h2 className="arch-panel-title">Magellan AI Search Ops Harness</h2>
            <p className="arch-panel-desc">
              <strong>Primary evaluator: Lead for Ecommerce Search Platforms.</strong> First workflow: automate operational tasks around Grid Dynamics AI Search without replacing the search solution itself. <strong>90-day proof:</strong> detect one retail query-cluster issue, generate the runbook, evaluate the change, canary it, and execute a rollback drill with signed evidence.
            </p>
            <table className="detail-table">
              <caption className="visually-hidden">
                Evidence boundaries and governance definitions for the Magellan AI Search Ops Harness concept.
              </caption>
              <thead>
                <tr>
                  <th scope="col">Boundary</th>
                  <th scope="col">Definition</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td className="label-cell">Source solution</td>
                  <td>
                    Built as an ops layer around{' '}
                    <a href="https://www.griddynamics.com/solutions/ai-search" target="_blank" rel="noreferrer">
                      Grid Dynamics AI Search and Selection
                    </a>
                    : semantic search, catalog optimization, multimodal engagement, smart autocomplete, personalization, JIT recommendations, AI-assisted selection, UGC feedback, and MXP merchandising controls.
                  </td>
                </tr>
                <tr>
                  <td className="label-cell">Write-capable</td>
                  <td>
                    Catalog enrichment tickets, synonym and autocomplete candidates, semantic index refresh jobs, MXP rule proposals, experiment configs, dashboard annotations, canary flags, rollback triggers.
                  </td>
                </tr>
                <tr>
                  <td className="label-cell">Human approval</td>
                  <td>
                    Production rule changes, broad traffic ramp, model or index swap, metric override, and high-impact merchandising changes.
                  </td>
                </tr>
                <tr>
                  <td className="label-cell">Auto-close</td>
                  <td>
                    Catalog completeness checks, query-cluster drift detection, zero-result triage, offline eval runs, shadow tests, and canary health checks.
                  </td>
                </tr>
                <tr>
                  <td className="label-cell">Evidence</td>
                  <td>
                    AI Search capability touched, dataset snapshot, query cluster, eval score, business metric, approver, canary cohort, and rollback reason.
                  </td>
                </tr>
                <tr>
                  <td className="label-cell">Stack discipline</td>
                  <td>
                    Magellan does not replace the search engine, MXP, recommender, or model provider. It wraps them with runbook automation, governance, observability, and reversible release control.
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <div className="container">
        <div className="stats-bar reveal visible">
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-number">7%+</div>
              <div className="stat-label">Conversion Rate Uplift</div>
              <span className="stat-note">GD AI Search proof point</span>
            </div>
            <div className="stat-card">
              <div className="stat-number">12%</div>
              <div className="stat-label">Click-Through Increase</div>
              <span className="stat-note">GD AI Search proof point</span>
            </div>
            <div className="stat-card">
              <div className="stat-number">~30%</div>
              <div className="stat-label">Revenue-per-Visitor</div>
              <span className="stat-note">GD AI Search proof point</span>
            </div>
            <div className="stat-card">
              <div className="stat-number">15x</div>
              <div className="stat-label">Return on Investment</div>
              <span className="stat-note">GD AI Search proof point</span>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export const OperatingModel: React.FC = () => {
  return (
    <section id="operating-model" className="operating-model">
      <div className="container">
        <div className="model-grid">
          <div className="model-summary reveal visible">
            <div className="section-label">00 — Operating Model</div>
            <h2>An ops layer for AI Search after go-live.</h2>
            <p className="lead">
              Grid Dynamics AI Search provides the product discovery capabilities. Magellan automates the operational work around those capabilities: detect issues, diagnose root cause, propose a safe change, run evals, and release only through guarded workflows.
            </p>
            <div className="model-points">
              <div className="model-point">
                <span className="icon-chip" style={{ '--accent': 'var(--orange)' } as React.CSSProperties}>EV</span>
                <div>
                  <strong>Every anomaly becomes an ops task</strong>
                  <p>Zero-result clusters, stale catalog attributes, weak autocomplete suggestions, and rule conflicts become structured work items, not ad hoc tickets.</p>
                </div>
              </div>
              <div className="model-point">
                <span className="icon-chip" style={{ '--accent': 'var(--teal)' } as React.CSSProperties}>QA</span>
                <div>
                  <strong>Runbooks generate candidate fixes</strong>
                  <p>The harness proposes catalog enrichment, synonym packs, index refreshes, personalization guardrails, and MXP rule changes with evidence attached.</p>
                </div>
              </div>
              <div className="model-point">
                <span className="icon-chip" style={{ '--accent': 'var(--emerald)' } as React.CSSProperties}>AB</span>
                <div>
                  <strong>Every release is measured and reversible</strong>
                  <p>Temporal workflows drive evals, shadow tests, canaries, approvals, rollback conditions, and versioned audit trails.</p>
                </div>
              </div>
            </div>
          </div>

          <div className="model-board reveal reveal-delay-1 visible">
            <div className="model-stage" data-step="01" style={{ '--accent': 'var(--orange)' } as React.CSSProperties}>
              <div className="stage-name">Capture Ops Signals</div>
              <div className="stage-detail">
                <h3>Watch the AI Search operating surface.</h3>
                <p>Catalog deltas, query logs, zero-result sessions, voice/image search failures, reviews, UGC signals, inventory shifts, and MXP overrides enter one ops ledger.</p>
                <ul>
                  <li>Catalog delta</li>
                  <li>Query logs</li>
                  <li>UGC</li>
                  <li>MXP edits</li>
                </ul>
              </div>
            </div>
            <div className="model-stage" data-step="02" style={{ '--accent': 'var(--teal)' } as React.CSSProperties}>
              <div className="stage-name">Diagnose Capability</div>
              <div className="stage-detail">
                <h3>Map symptoms to the responsible AI Search capability.</h3>
                <p>The harness classifies whether the issue belongs to semantic retrieval, catalog optimization, multimodal search, smart autocomplete, personalization, JIT recommendations, product selection, UGC feedback, or merchandising rules.</p>
                <ul>
                  <li>Semantic</li>
                  <li>Catalog</li>
                  <li>Autocomplete</li>
                  <li>MXP</li>
                </ul>
              </div>
            </div>
            <div className="model-stage" data-step="03" style={{ '--accent': 'var(--indigo)' } as React.CSSProperties}>
              <div className="stage-name">Propose Runbook</div>
              <div className="stage-detail">
                <h3>Generate a fix with tests, owner, and rollback plan.</h3>
                <p>Candidate runbooks include catalog fixes, synonym updates, autocomplete terms, re-embedding jobs, rule changes, benchmark sets, and rollout criteria.</p>
                <ul>
                  <li>Eval set</li>
                  <li>Owner</li>
                  <li>Canary</li>
                  <li>Rollback</li>
                </ul>
              </div>
            </div>
            <div className="model-stage" data-step="04" style={{ '--accent': 'var(--emerald)' } as React.CSSProperties}>
              <div className="stage-name">Release Safely</div>
              <div className="stage-detail">
                <h3>Apply ops changes only when evidence and guardrails agree.</h3>
                <p>Temporal coordinates shadow tests, canary traffic, operator review, automatic promotion, and rollback when search quality, latency, or business metrics degrade.</p>
                <ul>
                  <li>Shadow</li>
                  <li>5% canary</li>
                  <li>Approval</li>
                  <li>Audit</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export const UseCases: React.FC = () => {
  const cases = [
    { code: 'SE', label: 'Semantic Index Refresh Ops', text: 'Detect stale embeddings after catalog changes, scope the affected query clusters, schedule re-indexing, and attach before/after relevance evidence.', accent: 'var(--orange)' },
    { code: 'PR', label: 'Catalog Enrichment QA', text: 'Find missing attributes, weak titles, taxonomy gaps, and image/text inconsistencies before they degrade semantic search and product selection.', accent: 'var(--teal)' },
    { code: 'AR', label: 'Smart Autocomplete Tuning', text: 'Cluster typos, slang, trending terms, and zero-result prefixes into reviewed synonym and suggestion packs for autocomplete releases.', accent: 'var(--indigo)' },
    { code: 'QM', label: 'Personalization Guardrails', text: 'Monitor budgets, brand preferences, session behavior, and repeat-visit patterns so personalization improves relevance without overfitting or biasing inventory.', accent: 'var(--emerald)' },
    { code: 'IF', label: 'JIT Recommendation Ops', text: 'Evaluate result summaries, feature callouts, comparison prompts, and intent-refinement suggestions before they influence purchase decisions.', accent: 'var(--indigo)' },
    { code: 'ZM', label: 'MXP Rule Governance', text: 'Version, test, approve, and rollback synonyms, acronyms, boosts, suppressions, campaigns, and merchandising rules from the MXP control surface.', accent: 'var(--orange)' }
  ];

  return (
    <section id="use-cases">
      <div className="container">
        <div className="reveal visible">
          <div className="section-label">01 — Ops Use Cases</div>
          <h2>Ops Tasks Around<br />Grid Dynamics AI Search</h2>
          <p className="lead">
            AI Search capabilities create operational surface area after launch. Magellan automates the repetitive work a search platform team must keep doing: detect drift, prepare fixes, evaluate changes, route approvals, and release safely.
          </p>
        </div>

        <div className="usecase-grid">
          {cases.map((c, i) => (
            <div key={i} className="usecase-card reveal visible" style={{ '--card-accent': c.accent } as React.CSSProperties}>
              <div className="usecase-icon" style={{ background: `color-mix(in srgb, ${c.accent} 14%, white)`, color: c.accent }}>
                {c.code}
              </div>
              <h4>{c.label}</h4>
              <p>{c.text}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export const Scenarios: React.FC = () => {
  return (
    <section id="scenarios" style={{ background: 'var(--white)' }}>
      <div className="container">
        <div className="reveal visible">
          <div className="section-label">02 — Ops Scenarios</div>
          <h2>From Search Signal to<br />Approved Ops Change</h2>
          <p className="lead">
            Every scenario follows the same harness pattern: capture an operational signal, diagnose the affected AI Search capability, generate a runbook, and release the fix through measured controls.
          </p>
        </div>

        {/* Overview Flow */}
        <div className="scenario-flow reveal visible">
          <div className="flow-step">
            <div className="flow-dot" style={{ background: 'var(--orange)' }}>1</div>
            <h4 style={{ color: 'var(--orange)' }}>Signal</h4>
            <p>Catalog deltas, failed queries, low CTR, stale suggestions, rule conflicts</p>
          </div>
          <div className="flow-step">
            <div className="flow-dot" style={{ background: 'var(--teal)' }}>2</div>
            <h4 style={{ color: 'var(--teal)' }}>Diagnosis</h4>
            <p>Map symptoms to semantic search, catalog QA, autocomplete, personalization, or MXP</p>
          </div>
          <div className="flow-step">
            <div className="flow-dot" style={{ background: 'var(--emerald)' }}>3</div>
            <h4 style={{ color: 'var(--emerald)' }}>Runbook</h4>
            <p>Generate proposed fix, eval set, owner, approval gate, and rollback plan</p>
          </div>
          <div className="flow-step">
            <div className="flow-dot" style={{ background: 'var(--indigo)' }}>4</div>
            <h4 style={{ color: 'var(--indigo)' }}>Release</h4>
            <p>Shadow test, canary, monitor, promote, annotate, or rollback</p>
          </div>
        </div>

        {/* Scenario A */}
        <div className="scenario-detail reveal visible">
          <div className="scenario-detail-header">
            <span className="scenario-badge" style={{ background: 'var(--orange-dim)', color: 'var(--orange)' }}>Scenario A</span>
            <h3 style={{ margin: 0, fontSize: '1.15rem' }}>Catalog Update Breaks Semantic Retrieval</h3>
          </div>
          <div className="scenario-detail-body">
            <div className="scenario-col">
              <div className="scenario-col-label" style={{ color: 'var(--orange)' }}>Signal</div>
              <p>New seasonal trail shoes ship with missing waterproof and terrain attributes.</p>
            </div>
            <div className="scenario-col">
              <div className="scenario-col-label" style={{ color: 'var(--teal)' }}>Harness Work</div>
              <p>Detect catalog completeness gap → cluster impacted queries → propose enrichment patch → scope embedding refresh.</p>
            </div>
            <div className="scenario-col">
              <div className="scenario-col-label" style={{ color: 'var(--emerald)' }}>Runbook</div>
              <p>Catalog fix ticket, targeted re-embedding job, benchmark query set, and rollback target.</p>
            </div>
            <div className="scenario-col">
              <div className="scenario-col-label" style={{ color: 'var(--indigo)' }}>Release</div>
              <p>Shadow eval passes, 5% canary starts, conversion and zero-result metrics monitored.</p>
            </div>
          </div>
        </div>

        {/* Scenario B */}
        <div className="scenario-detail reveal visible">
          <div className="scenario-detail-header">
            <span className="scenario-badge" style={{ background: 'var(--teal-dim)', color: 'var(--teal)' }}>Scenario B</span>
            <h3 style={{ margin: 0, fontSize: '1.15rem' }}>Autocomplete Misses a Demand Trend</h3>
          </div>
          <div className="scenario-detail-body">
            <div className="scenario-col">
              <div className="scenario-col-label" style={{ color: 'var(--orange)' }}>Signal</div>
              <p>Mobile searches for "hybrid work backpack" and related prefixes show rising exits.</p>
            </div>
            <div className="scenario-col">
              <div className="scenario-col-label" style={{ color: 'var(--teal)' }}>Harness Work</div>
              <p>Cluster failed prefixes → mine catalog and query logs → generate synonym/autocomplete candidates → estimate business impact.</p>
            </div>
            <div className="scenario-col">
              <div className="scenario-col-label" style={{ color: 'var(--emerald)' }}>Runbook</div>
              <p>Suggestion pack, typo/slang mapping, MXP synonym proposal, and CTR guardrail.</p>
            </div>
            <div className="scenario-col">
              <div className="scenario-col-label" style={{ color: 'var(--indigo)' }}>Release</div>
              <p>Merchandising owner approves, suggestions canary on mobile, exits and CTR tracked.</p>
            </div>
          </div>
        </div>

        {/* Scenario C */}
        <div className="scenario-detail reveal visible">
          <div className="scenario-detail-header">
            <span className="scenario-badge" style={{ background: 'var(--emerald-dim)', color: 'var(--emerald)' }}>Scenario C</span>
            <h3 style={{ margin: 0, fontSize: '1.15rem' }}>Merchandising Rule Conflict</h3>
          </div>
          <div className="scenario-detail-body">
            <div className="scenario-col">
              <div className="scenario-col-label" style={{ color: 'var(--orange)' }}>Trigger</div>
              <p>A campaign boost promotes low-stock products and suppresses higher-converting substitutes.</p>
            </div>
            <div className="scenario-col">
              <div className="scenario-col-label" style={{ color: 'var(--teal)' }}>Harness Work</div>
              <p>Compare MXP rule diffs, inventory, conversion, and query cluster performance; isolate the conflicting boost rule.</p>
            </div>
            <div className="scenario-col">
              <div className="scenario-col-label" style={{ color: 'var(--emerald)' }}>Runbook</div>
              <p>Rollback candidate, substitute boost proposal, business impact note, and approval request.</p>
            </div>
            <div className="scenario-col">
              <div className="scenario-col-label" style={{ color: 'var(--indigo)' }}>Release</div>
              <p>Traffic ramp pauses, owner approves rollback, dashboard annotation records the incident and fix.</p>
            </div>
          </div>
        </div>

        <div className="feedback-loop reveal visible">
          <span className="icon">FB</span>
          Ops feedback updates runbook thresholds, query-cluster watchlists, and approval routing after each release.
        </div>
      </div>
    </section>
  );
};

export const DataFlow: React.FC = () => {
  return (
    <section id="data-flow">
      <div className="container">
        <div className="reveal visible">
          <div className="section-label">03 — Data Flow Diagram</div>
          <h2>How Ops Work Moves Through<br />the Harness Pipeline</h2>
          <p className="lead">
            Five layers turn AI Search telemetry into governed operational work: signal capture, diagnosis, runbook generation, controlled release, and feedback into future thresholds.
          </p>
        </div>

        <div className="dataflow-layers">
          <div className="df-layer reveal visible" style={{ '--accent': 'var(--orange)' } as React.CSSProperties}>
            <div className="df-layer-name"><span className="icon">IN</span> Ingestion</div>
            <div className="df-layer-content">AI Search events, catalog deltas, query logs, voice/image search attempts, UGC and reviews, inventory changes, MXP rule diffs</div>
          </div>
          <div className="df-arrow reveal visible">↓</div>
          <div className="df-layer reveal visible" style={{ '--accent': 'var(--teal)' } as React.CSSProperties}>
            <div className="df-layer-name"><span className="icon">DG</span> Diagnosis</div>
            <div className="df-layer-content">Query-cluster analysis, catalog completeness scoring, autocomplete failure grouping, personalization guardrail checks, rule conflict detection</div>
          </div>
          <div className="df-arrow reveal visible">↓</div>
          <div className="df-layer reveal visible" style={{ '--accent': 'var(--indigo)' } as React.CSSProperties}>
            <div className="df-layer-name"><span className="icon">RB</span> Runbook</div>
            <div className="df-layer-content">LLM/RLM-assisted root-cause summary, candidate catalog fix, synonym pack, re-index plan, MXP rule proposal, eval suite, owner routing</div>
          </div>
          <div className="df-arrow reveal visible">↓</div>
          <div className="df-layer reveal visible" style={{ '--accent': 'var(--emerald)' } as React.CSSProperties}>
            <div className="df-layer-name"><span className="icon">RL</span> Release</div>
            <div className="df-layer-content">Grid Dynamics AI Search adapters for semantic search, catalog optimization, smart autocomplete, personalization, JIT recommendations, and MXP rules</div>
          </div>
          <div className="df-arrow reveal visible">↓</div>
          <div className="df-layer reveal visible" style={{ '--accent': 'var(--navy)' } as React.CSSProperties}>
            <div className="df-layer-name"><span className="icon">FB</span> Feedback</div>
            <div className="df-layer-content">Canary telemetry, CTR, conversion, zero-result rate, latency, inventory impact, approval history → threshold tuning and watchlist updates</div>
          </div>
        </div>

        <div className="feedback-loop reveal visible">
          <span className="icon">FB</span>
          Feedback loop closes the circle: each release updates watchlists, thresholds, eval coverage, and approval policies for the next ops cycle.
        </div>
      </div>
    </section>
  );
};

export const ContextEngineering: React.FC = () => {
  return (
    <section id="context" className="dark-section">
      <div className="container">
        <div className="reveal visible">
          <div className="section-label" style={{ color: 'var(--orange)' }}>04 — Context Engineering</div>
          <h2>Runbook Context,<br />Approvals &amp; Evidence</h2>
          <p className="lead">
            How the harness assembles enough context to diagnose an AI Search ops issue, generate a safe runbook, and route the change through approvals.
          </p>
        </div>

        {/* Turn 1 Context Window */}
        <h3 style={{ color: 'var(--orange)', marginTop: '3rem' }} className="reveal visible">Turn 1 — Initial Context Assembly</h3>
        <div className="context-blocks reveal visible">
          <div className="ctx-block" style={{ '--accent': 'var(--orange)' } as React.CSSProperties}>
            <div className="ctx-label" style={{ color: 'var(--orange)' }}>Runbook Policy</div>
            <div className="ctx-content" style={{ color: 'var(--gray-400)' }}>Allowed actions, approval rules, rollback requirements, and protected AI Search surfaces</div>
          </div>
          <div className="ctx-block" style={{ '--accent': 'var(--teal)' } as React.CSSProperties}>
            <div className="ctx-label" style={{ color: 'var(--teal)' }}>Ops Signal</div>
            <div className="ctx-content" style={{ color: 'var(--gray-400)' }}>Failed query cluster, catalog delta, autocomplete miss, multimodal failure, or MXP rule conflict</div>
          </div>
          <div className="ctx-block" style={{ '--accent': 'var(--indigo)' } as React.CSSProperties}>
            <div className="ctx-label" style={{ color: 'var(--indigo)' }}>Capability Map</div>
            <div className="ctx-content" style={{ color: 'var(--gray-400)' }}>Semantic search, catalog optimization, smart autocomplete, personalization, JIT recommendations, MXP rules</div>
          </div>
          <div className="ctx-block" style={{ '--accent': 'var(--emerald)' } as React.CSSProperties}>
            <div className="ctx-label" style={{ color: 'var(--emerald)' }}>Evidence Pack</div>
            <div className="ctx-content" style={{ color: 'var(--gray-400)' }}>Catalog rows, product embeddings, query logs, inventory state, reviews, baseline metrics, owner history</div>
          </div>
          <div className="ctx-block" style={{ '--accent': 'var(--navy-mid)' } as React.CSSProperties}>
            <div className="ctx-label" style={{ color: 'var(--gray-300)' }}>Tool Calls</div>
            <div className="ctx-content" style={{ color: 'var(--gray-400)' }}>catalog QA → gaps, eval factory → scores, MXP adapter → rule diff, Temporal → workflow state</div>
          </div>
        </div>

        {/* Temporal + RLMs */}
        <div className="two-panel reveal visible">
          <div className="panel" style={{ background: 'rgba(242,237,225,0.04)', borderColor: 'rgba(242,237,225,0.08)' }}>
            <h4 style={{ color: 'var(--teal)' }}><span className="icon-chip" style={{ '--accent': 'var(--teal)' } as React.CSSProperties}>TL</span> Temporal — Automated Approvals</h4>
            <ol>
              <li style={{ color: 'var(--gray-400)' }}>Runbook triggered by catalog, query, autocomplete, or MXP signal</li>
              <li style={{ color: 'var(--gray-400)' }}>Automated validation: relevance, zero-result, latency, inventory, and business checks</li>
              <li style={{ color: 'var(--gray-400)' }}>Shadow test before canary traffic</li>
              <li style={{ color: 'var(--gray-400)' }}>Approval gate: auto-approve only for low-risk, metric-clean changes</li>
              <li style={{ color: 'var(--gray-400)' }}>Progressive rollout: 5% → 25% → 50% → 100%</li>
              <li style={{ color: 'var(--gray-400)' }}>Rollback activity if degradation detected</li>
            </ol>
          </div>
          <div className="panel" style={{ background: 'rgba(242,237,225,0.04)', borderColor: 'rgba(242,237,225,0.08)' }}>
            <h4 style={{ color: 'var(--indigo)' }}><span className="icon-chip" style={{ '--accent': 'var(--indigo)' } as React.CSSProperties}>AI</span> RLMs (with CodeAct Execution)</h4>
            <ol>
              <li style={{ color: 'var(--gray-400)' }}>Decompose ops incidents into affected capability, data gap, metric impact, and owner path</li>
              <li style={{ color: 'var(--gray-400)' }}>Each sub-task gets a focused evidence window</li>
              <li style={{ color: 'var(--gray-400)' }}>CodeAct executes eval scripts, statistical analysis, catalog diffs, and rule diffs</li>
              <li style={{ color: 'var(--gray-400)' }}>Results folded back into parent context</li>
              <li style={{ color: 'var(--gray-400)' }}>Handles multi-signal incidents across catalog, semantic retrieval, autocomplete, and merchandising controls</li>
            </ol>
          </div>
        </div>

        {/* Follow-up Context */}
        <div className="callout reveal visible" style={{ background: 'rgba(139,58,43,0.08)', marginTop: '3rem' }}>
          <div className="callout-label">Example — RLM Decomposition</div>
          <p style={{ color: 'var(--gray-300)' }}><strong style={{ color: 'var(--white)' }}>Incident:</strong> "waterproof trail shoe queries are failing after the spring catalog refresh"</p>
          <p style={{ color: 'var(--gray-400)', marginTop: '0.5rem' }}>RLM decomposes: <span style={{ color: 'var(--teal)' }}>[catalog delta]</span> → <span style={{ color: 'var(--orange)' }}>[attribute gaps]</span> → <span style={{ color: 'var(--emerald)' }}>[semantic index freshness]</span> → <span style={{ color: 'var(--indigo)' }}>[MXP rule conflicts]</span> → runbook + eval + canary</p>
        </div>
      </div>
    </section>
  );
};

export const UserFlow: React.FC = () => {
  return (
    <section id="user-flow">
      <div className="container">
        <div className="reveal visible">
          <div className="section-label">05 — Ops Flow Diagram</div>
          <h2>End-to-End Journey from<br />Incident to Controlled Release</h2>
          <p className="lead">
            Six stages trace the operator path through Magellan: detect an AI Search issue, diagnose it, generate a runbook, evaluate it, release it, and learn from the outcome.
          </p>
        </div>

        <div className="userflow-steps">
          <div className="uf-step reveal visible" style={{ '--step-color': 'var(--orange)' } as React.CSSProperties}>
            <div className="uf-icon" style={{ background: 'var(--orange-dim)', color: 'var(--orange)', width: 36, height: 36, borderRadius: 8, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', marginBottom: '0.5rem' }}>SG</div>
            <h5 style={{ color: 'var(--orange)' }}>Signal</h5>
            <p>Catalog, query, autocomplete, or rule anomaly arrives</p>
          </div>
          <div className="uf-step reveal visible" style={{ '--step-color': 'var(--teal)' } as React.CSSProperties}>
            <div className="uf-icon" style={{ background: 'var(--teal-dim)', color: 'var(--teal)', width: 36, height: 36, borderRadius: 8, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', marginBottom: '0.5rem' }}>DG</div>
            <h5 style={{ color: 'var(--teal)' }}>Diagnose</h5>
            <p>Affected AI Search capability and root cause identified</p>
          </div>
          <div className="uf-step reveal visible" style={{ '--step-color': 'var(--indigo)' } as React.CSSProperties}>
            <div className="uf-icon" style={{ background: 'var(--indigo-dim)', color: 'var(--indigo)', width: 36, height: 36, borderRadius: 8, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', marginBottom: '0.5rem' }}>RB</div>
            <h5 style={{ color: 'var(--indigo)' }}>Runbook</h5>
            <p>Candidate fix, owner, eval set, and rollback plan created</p>
          </div>
          <div className="uf-step reveal visible" style={{ '--step-color': 'var(--emerald)' } as React.CSSProperties}>
            <div className="uf-icon" style={{ background: 'var(--emerald-dim)', color: 'var(--emerald)', width: 36, height: 36, borderRadius: 8, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', marginBottom: '0.5rem' }}>EV</div>
            <h5 style={{ color: 'var(--emerald)' }}>Evaluate</h5>
            <p>Offline, shadow, latency, and business guardrails run</p>
          </div>
          <div className="uf-step reveal visible" style={{ '--step-color': 'var(--navy)' } as React.CSSProperties}>
            <div className="uf-icon" style={{ background: 'rgba(27,42,74,0.1)', color: 'var(--navy)', width: 36, height: 36, borderRadius: 8, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', marginBottom: '0.5rem' }}>RL</div>
            <h5 style={{ color: 'var(--navy)' }}>Release</h5>
            <p>Approval, canary, dashboard annotation, or rollback</p>
          </div>
          <div className="uf-step reveal visible" style={{ '--step-color': 'var(--orange)' } as React.CSSProperties}>
            <div className="uf-icon" style={{ background: 'var(--orange-dim)', color: 'var(--orange)', width: 36, height: 36, borderRadius: 8, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', marginBottom: '0.5rem' }}>FB</div>
            <h5 style={{ color: 'var(--orange)' }}>Learn</h5>
            <p>Thresholds, watchlists, and runbook templates updated</p>
          </div>
        </div>

        {/* Swimlanes */}
        <div className="swimlane reveal visible" style={{ marginTop: '3rem' }}>
          <div className="swimlane-header" style={{ background: 'var(--teal)' }}>Operator Flow</div>
          <div className="swimlane-body">
            <div className="swimlane-cell">
              <h5>Configure Runbooks</h5>
              <p>Select enabled ops automations</p>
            </div>
            <div className="swimlane-cell">
              <h5>Set Thresholds</h5>
              <p>Define quality gates for auto-approval</p>
            </div>
            <div className="swimlane-cell">
              <h5>Review Evidence</h5>
              <p>Inspect evals, owners, and risk</p>
            </div>
            <div className="swimlane-cell">
              <h5>Approve / Roll Back</h5>
              <p>Control release and recovery actions</p>
            </div>
          </div>
        </div>

        <div className="swimlane reveal visible">
          <div className="swimlane-header" style={{ background: 'var(--indigo)' }}>Analytics Flow</div>
          <div className="swimlane-body">
            <div className="swimlane-cell">
              <h5>Query Clusters</h5>
              <p>Trends, exits, zero-result queries</p>
            </div>
            <div className="swimlane-cell">
              <h5>Ops Metrics</h5>
              <p>Runbook volume, eval pass rate, SLA</p>
            </div>
            <div className="swimlane-cell">
              <h5>Canary Results</h5>
              <p>Change outcomes and statistical confidence</p>
            </div>
            <div className="swimlane-cell">
              <h5>Business Impact</h5>
              <p>Conversion, inventory, revenue per search</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export const SequenceInteractions: React.FC = () => {
  return (
    <section id="sequence" style={{ background: 'var(--white)' }}>
      <div className="container">
        <div className="seq-intro reveal visible">
          <div>
            <div className="section-label">06 — Sequence Diagram</div>
            <h2>Component Interactions for<br />an AI Search Ops Runbook</h2>
            <p className="lead">
              The ops path separates live search serving from automated remediation, so Grid Dynamics AI Search stays stable while Magellan prepares, tests, and releases controlled changes.
            </p>
          </div>
          <div className="seq-legend" aria-label="Sequence legend">
            <span>Solid = ops workflow</span>
            <span>Dashed = telemetry feedback</span>
            <span>Gates = promotion checks</span>
          </div>
        </div>

        {/* Diagram 1 */}
        <div className="seq-diagram reveal visible">
          <div className="seq-titlebar">
            <h3>Runbook Creation Path</h3>
            <span>Target: evidence before change</span>
          </div>
          <div className="seq-scroll">
            <div className="seq-canvas" style={{ '--cols': 6 } as React.CSSProperties}>
              <div className="seq-lifelines">
                <div></div>
                <div className="seq-lane" style={{ '--accent': 'var(--orange)' } as React.CSSProperties}>
                  <strong>AI Search</strong>
                  <span>Live solution</span>
                </div>
                <div className="seq-lane" style={{ '--accent': 'var(--teal)' } as React.CSSProperties}>
                  <strong>Ops Ledger</strong>
                  <span>Signals + diffs</span>
                </div>
                <div className="seq-lane" style={{ '--accent': 'var(--indigo)' } as React.CSSProperties}>
                  <strong>Diagnosis Engine</strong>
                  <span>Capability mapping</span>
                </div>
                <div className="seq-lane" style={{ '--accent': 'var(--navy)' } as React.CSSProperties}>
                  <strong>Runbook Factory</strong>
                  <span>Fix proposal</span>
                </div>
                <div className="seq-lane" style={{ '--accent': 'var(--emerald)' } as React.CSSProperties}>
                  <strong>Eval Factory</strong>
                  <span>Offline + shadow</span>
                </div>
                <div className="seq-lane" style={{ '--accent': 'var(--cyan)' } as React.CSSProperties}>
                  <strong>Temporal</strong>
                  <span>Approval + release</span>
                </div>
              </div>

              {/* Rows */}
              <div className="seq-row">
                <div className="seq-index">1</div>
                <div className="seq-arrow" style={{ '--start': 1, '--end': 2, '--accent': 'var(--orange)' } as React.CSSProperties}>
                  <span>emit ops signal</span>
                </div>
                <div className="seq-note" style={{ '--col': 2 } as React.CSSProperties}>Zero-result cluster, catalog delta, rule diff, or canary metric</div>
              </div>
              <div className="seq-row">
                <div className="seq-index">2</div>
                <div className="seq-arrow" style={{ '--start': 2, '--end': 3, '--accent': 'var(--teal)' } as React.CSSProperties}>
                  <span>classify issue</span>
                </div>
                <div className="seq-note" style={{ '--col': 3 } as React.CSSProperties}>Maps symptom to semantic search, catalog, autocomplete, personalization, or MXP</div>
              </div>
              <div className="seq-row">
                <div className="seq-index">3</div>
                <div className="seq-arrow" style={{ '--start': 3, '--end': 4, '--accent': 'var(--indigo)' } as React.CSSProperties}>
                  <span>generate runbook</span>
                </div>
                <div className="seq-note" style={{ '--col': 4 } as React.CSSProperties}>Candidate fix, evidence pack, owner, eval set, rollback plan</div>
              </div>
              <div className="seq-row">
                <div className="seq-index">4</div>
                <div className="seq-arrow reverse" style={{ '--start': 3, '--end': 4, '--accent': 'var(--navy)' } as React.CSSProperties}>
                  <span>root cause</span>
                </div>
                <div className="seq-note" style={{ '--col': 3 } as React.CSSProperties}>Attribute gap, stale index, weak suggestion, or rule conflict</div>
              </div>
              <div className="seq-row">
                <div className="seq-index">5</div>
                <div className="seq-arrow" style={{ '--start': 4, '--end': 5, '--accent': 'var(--emerald)' } as React.CSSProperties}>
                  <span>evaluate proposal</span>
                </div>
                <div className="seq-note" style={{ '--col': 5 } as React.CSSProperties}>Offline benchmark, shadow replay, latency, inventory, business guardrails</div>
              </div>
              <div className="seq-row">
                <div className="seq-index">6</div>
                <div className="seq-arrow reverse" style={{ '--start': 4, '--end': 5, '--accent': 'var(--emerald)' } as React.CSSProperties}>
                  <span>eval report</span>
                </div>
                <div className="seq-note" style={{ '--col': 4 } as React.CSSProperties}>Pass/fail, metric deltas, sample size, risk flags</div>
              </div>
              <div className="seq-row">
                <div className="seq-index">7</div>
                <div className="seq-arrow" style={{ '--start': 5, '--end': 6, '--accent': 'var(--teal)' } as React.CSSProperties}>
                  <span>start approval</span>
                </div>
                <div className="seq-note" style={{ '--col': 6 } as React.CSSProperties}>Route to search lead, merchandiser, or auto-approval policy</div>
              </div>
              <div className="seq-row">
                <div className="seq-index">8</div>
                <div className="seq-arrow async" style={{ '--start': 1, '--end': 6, '--accent': 'var(--cyan)' } as React.CSSProperties}>
                  <span>release telemetry</span>
                </div>
                <div className="seq-note" style={{ '--col': 6 } as React.CSSProperties}>Canary data updates runbook status without blocking live search</div>
              </div>
            </div>
          </div>
          <div className="seq-gates">
            <div className="seq-gate">
              <strong>No Inline Mutation</strong>
              <p>Magellan prepares fixes outside the live request path.</p>
            </div>
            <div className="seq-gate">
              <strong>Evidence Required</strong>
              <p>Each runbook carries source signal, root cause, eval report, and rollback plan.</p>
            </div>
            <div className="seq-gate">
              <strong>Policy Guard</strong>
              <p>Inventory, merchandising, latency, and business rules gate release.</p>
            </div>
            <div className="seq-gate">
              <strong>Ops Feedback</strong>
              <p>Release telemetry updates thresholds and future watchlists.</p>
            </div>
          </div>
        </div>

        {/* Diagram 2 */}
        <div className="seq-diagram reveal visible" style={{ marginTop: '2rem' }}>
          <div className="seq-titlebar">
            <h3>Controlled Release Loop</h3>
            <span>Shadow + canary + rollback</span>
          </div>
          <div className="seq-scroll">
            <div className="seq-canvas" style={{ '--cols': 6 } as React.CSSProperties}>
              <div className="seq-lifelines">
                <div></div>
                <div className="seq-lane" style={{ '--accent': 'var(--cyan)' } as React.CSSProperties}>
                  <strong>Runbook</strong>
                  <span>Approved candidate</span>
                </div>
                <div className="seq-lane" style={{ '--accent': 'var(--orange)' } as React.CSSProperties}>
                  <strong>AI Search Adapter</strong>
                  <span>Catalog/MXP/index</span>
                </div>
                <div className="seq-lane" style={{ '--accent': 'var(--teal)' } as React.CSSProperties}>
                  <strong>Temporal</strong>
                  <span>Workflow control</span>
                </div>
                <div className="seq-lane" style={{ '--accent': 'var(--indigo)' } as React.CSSProperties}>
                  <strong>Observability</strong>
                  <span>Ops + business metrics</span>
                </div>
                <div className="seq-lane" style={{ '--accent': 'var(--navy)' } as React.CSSProperties}>
                  <strong>Audit Ledger</strong>
                  <span>Evidence history</span>
                </div>
                <div className="seq-lane" style={{ '--accent': 'var(--emerald)' } as React.CSSProperties}>
                  <strong>Traffic Router</strong>
                  <span>Shadow + canary</span>
                </div>
              </div>

              {/* Rows */}
              <div className="seq-row">
                <div className="seq-index">1</div>
                <div className="seq-arrow" style={{ '--start': 1, '--end': 2, '--accent': 'var(--cyan)' } as React.CSSProperties}>
                  <span>apply candidate</span>
                </div>
                <div className="seq-note" style={{ '--col': 2 } as React.CSSProperties}>Catalog patch, synonym pack, index refresh, or MXP rule change</div>
              </div>
              <div className="seq-row">
                <div className="seq-index">2</div>
                <div className="seq-arrow" style={{ '--start': 1, '--end': 3, '--accent': 'var(--orange)' } as React.CSSProperties}>
                  <span>start workflow</span>
                </div>
                <div className="seq-note" style={{ '--col': 3 } as React.CSSProperties}>Approval state, release window, rollback activity</div>
              </div>
              <div className="seq-row">
                <div className="seq-index">3</div>
                <div className="seq-arrow" style={{ '--start': 3, '--end': 6, '--accent': 'var(--teal)' } as React.CSSProperties}>
                  <span>shadow replay</span>
                </div>
                <div className="seq-note" style={{ '--col': 6 } as React.CSSProperties}>Mirrored traffic validates behavior before real users see it</div>
              </div>
              <div className="seq-row">
                <div className="seq-index">4</div>
                <div className="seq-arrow" style={{ '--start': 6, '--end': 4, '--accent': 'var(--indigo)' } as React.CSSProperties}>
                  <span>collect telemetry</span>
                </div>
                <div className="seq-note" style={{ '--col': 4 } as React.CSSProperties}>CTR, conversion, zero-result rate, latency, inventory impact</div>
              </div>
              <div className="seq-row">
                <div className="seq-index">5</div>
                <div className="seq-arrow reverse" style={{ '--start': 1, '--end': 5, '--accent': 'var(--navy)' } as React.CSSProperties}>
                  <span>write audit</span>
                </div>
                <div className="seq-note" style={{ '--col': 1 } as React.CSSProperties}>Source signal, evidence, approver, rollout state, rollback plan</div>
              </div>
              <div className="seq-row">
                <div className="seq-index">6</div>
                <div className="seq-arrow" style={{ '--start': 3, '--end': 6, '--accent': 'var(--emerald)' } as React.CSSProperties}>
                  <span>canary 5% → 25% → 100%</span>
                </div>
                <div className="seq-note" style={{ '--col': 6 } as React.CSSProperties}>Promotion only when live metrics beat baseline</div>
              </div>
              <div className="seq-row">
                <div className="seq-index">7</div>
                <div className="seq-arrow reverse async" style={{ '--start': 2, '--end': 6, '--accent': 'var(--rose)' } as React.CSSProperties}>
                  <span>rollback signal</span>
                </div>
                <div className="seq-note" style={{ '--col': 3 } as React.CSSProperties}>Automatic rollback on search quality, latency, inventory, or conversion regression</div>
              </div>
            </div>
          </div>
          <div className="seq-gates">
            <div className="seq-gate">
              <strong>Auto-Approve</strong>
              <p>Allowed only for low-risk ops changes with clean evals and enough sample size.</p>
            </div>
            <div className="seq-gate">
              <strong>Manual Review</strong>
              <p>Required for ambiguous clusters, brand-sensitive rules, or high business impact.</p>
            </div>
            <div className="seq-gate">
              <strong>Shadow First</strong>
              <p>High-risk catalog, autocomplete, and MXP changes run on mirrored traffic before canary.</p>
            </div>
            <div className="seq-gate">
              <strong>Audit Trail</strong>
              <p>Every released runbook links to signal, evidence, approver, and rollback plan.</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export const Roadmap: React.FC = () => {
  return (
    <section id="roadmap" style={{ background: 'var(--white)' }}>
      <div className="container">
        <div className="reveal visible">
          <div className="section-label">08 — Implementation Roadmap</div>
          <h2>Build Plan for<br />AI Search Ops Automation</h2>
          <p className="lead">
            A credible harness starts by instrumenting the existing AI Search solution, then adds runbook generation, eval coverage, and controlled release workflows around the highest-volume ops tasks.
          </p>
        </div>

        <div className="roadmap-grid">
          <div className="roadmap-card reveal visible" style={{ '--accent': 'var(--orange)' } as React.CSSProperties}>
            <div className="phase">Phase 1</div>
            <h3>AI Search Ops Signals</h3>
            <p>Instrument the operational events needed to understand catalog, semantic search, autocomplete, personalization, and MXP health.</p>
            <ul>
              <li>Canonical ops event schema</li>
              <li>Catalog and rule diff capture</li>
              <li>Zero-result cluster ledger</li>
            </ul>
          </div>
          <div className="roadmap-card reveal visible" style={{ '--accent': 'var(--teal)' } as React.CSSProperties}>
            <div className="phase">Phase 2</div>
            <h3>Runbook Automation MVP</h3>
            <p>Generate reviewed fixes for the first three ops loops: catalog enrichment, autocomplete tuning, and semantic index refresh.</p>
            <ul>
              <li>Root-cause summaries</li>
              <li>Fix proposal templates</li>
              <li>Owner and approval routing</li>
            </ul>
          </div>
          <div className="roadmap-card reveal visible" style={{ '--accent': 'var(--indigo)' } as React.CSSProperties}>
            <div className="phase">Phase 3</div>
            <h3>Evaluation + Shadow Factory</h3>
            <p>Measure runbook proposals before release, using offline benchmarks, shadow traffic, latency checks, and business guardrails.</p>
            <ul>
              <li>Query-cluster eval suite</li>
              <li>Latency and cost checks</li>
              <li>Merchandising regression alerts</li>
            </ul>
          </div>
          <div className="roadmap-card reveal visible" style={{ '--accent': 'var(--emerald)' } as React.CSSProperties}>
            <div className="phase">Phase 4</div>
            <h3>Governed Release Ops</h3>
            <p>Use Temporal to coordinate approvals, canaries, dashboard annotations, rollback drills, and audit history for AI Search ops changes.</p>
            <ul>
              <li>5/25/50/100 rollout ladder</li>
              <li>Human override queue</li>
              <li>Versioned runbook registry</li>
            </ul>
          </div>
        </div>

        <div className="governance-band reveal visible">
          <div className="governance-item">
            <strong>Guardrail</strong>
            <p>No catalog, autocomplete, index, personalization, or MXP change can bypass relevance, latency, inventory, and business impact thresholds.</p>
          </div>
          <div className="governance-item">
            <strong>Observability</strong>
            <p>Every decision records source signal, affected AI Search capability, candidate fix, eval score, approver, and rollout state.</p>
          </div>
          <div className="governance-item">
            <strong>Control</strong>
            <p>Search leads and merchandisers retain approve, reject, pin, boost, suppress, and rollback controls when automation confidence is low.</p>
          </div>
        </div>
      </div>
    </section>
  );
};

export const ComponentsModel: React.FC = () => {
  return (
    <section id="components" style={{ background: 'var(--white)' }}>
      <div className="container">
        <div className="reveal visible">
          <div className="section-label">09 — Recommended Components</div>
          <h2>Solution Surface &amp;<br />Ops Building Blocks</h2>
          <p className="lead">
            The harness is composed of three layers: the Grid Dynamics AI Search capability surface, ops automation runbooks, and infrastructure for orchestration, evidence, and release control.
          </p>
        </div>

        {/* Grid Dynamics AI Search Surface */}
        <div className="comp-section reveal visible">
          <div className="comp-section-title" style={{ color: 'var(--orange)' }}>Grid Dynamics AI Search Surface</div>
          <div className="comp-grid">
            <div className="comp-card" data-role="Retrieval" style={{ '--accent': 'var(--orange)' } as React.CSSProperties}>
              <h4>Semantic Vector Search</h4>
              <p>Understands imprecise queries and product meaning through semantic retrieval over catalog and engagement signals.</p>
            </div>
            <div className="comp-card" data-role="Catalog" style={{ '--accent': 'var(--teal)' } as React.CSSProperties}>
              <h4>Catalog Optimization</h4>
              <p>Improves product data, titles, descriptions, attributes, and categorization for better discovery.</p>
            </div>
            <div className="comp-card" data-role="Multimodal" style={{ '--accent': 'var(--indigo)' } as React.CSSProperties}>
              <h4>Multimodal Search</h4>
              <p>Supports text, voice, and image-based search flows that need separate QA and failure tracking.</p>
            </div>
            <div className="comp-card" data-role="Autocomplete" style={{ '--accent': 'var(--emerald)' } as React.CSSProperties}>
              <h4>Smart Autocomplete</h4>
              <p>Uses catalog insights, query patterns, and customer behavior to predict intent in real time.</p>
            </div>
            <div className="comp-card" data-role="Personalization" style={{ '--accent': 'var(--navy)' } as React.CSSProperties}>
              <h4>Personalized Results</h4>
              <p>Uses customer history and session data to align results and recommendations with shopper preferences.</p>
            </div>
            <div className="comp-card" data-role="Merchandising" style={{ '--accent': 'var(--orange)' } as React.CSSProperties}>
              <h4>MXP Merchandising Rules</h4>
              <p>Maintains business control through synonyms, boosts, suppressions, campaigns, and targeted promotions.</p>
            </div>
          </div>
        </div>

        {/* Ops Automation Runbooks */}
        <div className="comp-section reveal visible">
          <div className="comp-section-title" style={{ color: 'var(--teal)' }}>Ops Automation Runbooks</div>
          <div className="comp-grid">
            <div className="comp-card" data-role="Catalog QA" style={{ '--accent': 'var(--orange)' } as React.CSSProperties}>
              <h4>Catalog QA Agent</h4>
              <p>Detects missing attributes, weak descriptions, taxonomy gaps, and media mismatches that degrade discovery.</p>
            </div>
            <div className="comp-card" data-role="Indexing" style={{ '--accent': 'var(--teal)' } as React.CSSProperties}>
              <h4>Semantic Index Refresh</h4>
              <p>Scopes re-embedding and re-indexing work after catalog changes, seasonal shifts, or retrieval drift.</p>
            </div>
            <div className="comp-card" data-role="Autocomplete" style={{ '--accent': 'var(--indigo)' } as React.CSSProperties}>
              <h4>Autocomplete Tuning</h4>
              <p>Generates reviewed suggestion and synonym packs from failed prefixes, typos, slang, and trending terms.</p>
            </div>
            <div className="comp-card" data-role="Rules" style={{ '--accent': 'var(--emerald)' } as React.CSSProperties}>
              <h4>MXP Rule Governance</h4>
              <p>Versions, tests, approves, and rolls back synonyms, boosts, suppressions, and campaign rules.</p>
            </div>
            <div className="comp-card" data-role="Guardrails" style={{ '--accent': 'var(--navy)' } as React.CSSProperties}>
              <h4>Personalization Guardrails</h4>
              <p>Monitors session, budget, brand, inventory, and preference effects before personalization changes expand.</p>
            </div>
            <div className="comp-card" data-role="UGC" style={{ '--accent': 'var(--orange)' } as React.CSSProperties}>
              <h4>UGC Signal Miner</h4>
              <p>Extracts review and social chatter signals that can become catalog improvements or recommendation tests.</p>
            </div>
          </div>
        </div>

        {/* Infrastructure */}
        <div className="comp-section reveal visible">
          <div className="comp-section-title" style={{ color: 'var(--indigo)' }}>Infrastructure</div>
          <div className="comp-grid">
            <div className="comp-card" data-role="Orchestration" style={{ '--accent': 'var(--orange)' } as React.CSSProperties}>
              <h4>Temporal</h4>
              <p>Durable workflow engine for runbook execution, approvals, canaries, dashboard annotation, and rollback.</p>
            </div>
            <div className="comp-card" data-role="Quality" style={{ '--accent': 'var(--teal)' } as React.CSSProperties}>
              <h4>Eval Factory</h4>
              <p>Automated evaluations for query clusters, autocomplete packs, catalog fixes, MXP rules, and business guardrails.</p>
            </div>
            <div className="comp-card" data-role="Management" style={{ '--accent': 'var(--indigo)' } as React.CSSProperties}>
              <h4>Runbook Registry</h4>
              <p>Central catalog of ops automations with ownership, allowed actions, approval requirements, and versioning.</p>
            </div>
            <div className="comp-card" data-role="Data" style={{ '--accent': 'var(--emerald)' } as React.CSSProperties}>
              <h4>Signal Store</h4>
              <p>Real-time and batch storage for query clusters, catalog deltas, rule diffs, canary metrics, and release evidence.</p>
            </div>
            <div className="comp-card" data-role="Storage" style={{ '--accent': 'var(--navy)' } as React.CSSProperties}>
              <h4>AI Search Adapters</h4>
              <p>Connectors for semantic index refresh, autocomplete configuration, catalog enrichment, personalization guardrails, and MXP rules.</p>
            </div>
            <div className="comp-card" data-role="Messaging" style={{ '--accent': 'var(--orange)' } as React.CSSProperties}>
              <h4>Kafka / Event Bus</h4>
              <p>Real-time event streaming for AI Search telemetry, clickstream, runbook events, approvals, and release outcomes.</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
