import React from 'react';

export const Hero: React.FC = () => {
  const handleScrollToConsole = (e: React.MouseEvent<HTMLAnchorElement>) => {
    e.preventDefault();
    const consoleEl = document.getElementById('ui-screens');
    if (consoleEl) {
      consoleEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  const handleScrollToModel = (e: React.MouseEvent<HTMLAnchorElement>) => {
    e.preventDefault();
    const modelEl = document.getElementById('operating-model');
    if (modelEl) {
      modelEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  return (
    <section className="hero" aria-labelledby="page-title">
      <div className="hero-visual" aria-hidden="true">
        <div className="ops-stage ops-link">
          <div className="ops-card ops-search">
            <h4>AI Search Ops Signal</h4>
            <div className="ops-query">
              <span className="lens">Q</span>
              <span>zero-result cluster: waterproof trail shoes</span>
            </div>
          </div>
          <div className="ops-node">
            <strong>OPS</strong>
            <span>Harness</span>
          </div>
          <div className="ops-card ops-pipeline">
            <h4>Runbook Pipeline</h4>
            <div className="ops-pipeline-row">
              <span className="ops-label">Catalog</span>
              <div className="ops-bar">
                <span style={{ '--w': '92%' } as React.CSSProperties}></span>
              </div>
              <span className="ops-score">gap</span>
            </div>
            <div className="ops-pipeline-row">
              <span className="ops-label">Index</span>
              <div className="ops-bar">
                <span style={{ '--w': '88%' } as React.CSSProperties}></span>
              </div>
              <span className="ops-score">stale</span>
            </div>
            <div className="ops-pipeline-row">
              <span className="ops-label">MXP</span>
              <div className="ops-bar">
                <span style={{ '--w': '76%' } as React.CSSProperties}></span>
              </div>
              <span className="ops-score">review</span>
            </div>
            <div className="ops-pipeline-row">
              <span className="ops-label">Canary</span>
              <div className="ops-bar">
                <span style={{ '--w': '64%' } as React.CSSProperties}></span>
              </div>
              <span className="ops-score">pass</span>
            </div>
          </div>
          <div className="ops-card ops-metric">
            <strong>18</strong>
            <span>Open ops tasks triaged into eval-ready runbooks</span>
          </div>
        </div>
      </div>
      <div className="hero-content">
        <div className="hero-text">
          <div className="eyebrow">
            Ops Automation · Grid Dynamics AI Search · Ecommerce Relevance
          </div>
          <h1 id="page-title">
            AI Search<br />
            <em>Ops Automation</em><br />
            Harness
          </h1>
          <p className="subtitle">
            <strong>Magellan</strong> is a control plane around Grid Dynamics AI Search: it detects catalog, autocomplete, semantic index, personalization, and merchandising issues, then turns them into evaluated runbooks, approvals, canaries, and rollback-ready releases.
          </p>
          <div className="hero-actions">
            <a className="hero-action primary" href="#operating-model" onClick={handleScrollToModel}>
              Read Operating Model <span aria-hidden="true">→</span>
            </a>
            <a className="hero-action" href="#ui-screens" onClick={handleScrollToConsole}>
              View Ops Console <span aria-hidden="true">↓</span>
            </a>
          </div>
          <div className="hero-tags">
            <span className="hero-tag">Ops: Catalog QA</span>
            <span className="hero-tag">Ops: Semantic Index Refresh</span>
            <span className="hero-tag">Ops: Autocomplete Tuning</span>
            <span className="hero-tag">Ops: MXP Rule Governance</span>
            <span className="hero-tag">Ops: Canary &amp; Rollback</span>
          </div>
          <div className="hero-proofline" aria-label="Core operating guarantees">
            <span>Runbooks-as-workflows</span>
            <span>Human approval gates</span>
            <span>Signed release evidence</span>
          </div>
        </div>
      </div>
    </section>
  );
};
