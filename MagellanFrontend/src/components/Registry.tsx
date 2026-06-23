import React from 'react';
import { 
  Sliders, 
  Settings, 
  ShieldAlert, 
  Clock, 
  Sparkles 
} from 'lucide-react';

interface RegistryProps {
  skills: {
    catalogEnrichment: boolean;
    semanticIndex: boolean;
    autocompleteTuning: boolean;
    mxpGovernance: boolean;
    multimodalQa: boolean;
  };
  setSkills: React.Dispatch<React.SetStateAction<{
    catalogEnrichment: boolean;
    semanticIndex: boolean;
    autocompleteTuning: boolean;
    mxpGovernance: boolean;
    multimodalQa: boolean;
  }>>;
  ndcgFloor: string;
  setNdcgFloor: (val: string) => void;
  latencyCeiling: string;
  setLatencyCeiling: (val: string) => void;
  canaryTraffic: string;
  setCanaryTraffic: (val: string) => void;
}

export const Registry: React.FC<RegistryProps> = ({
  skills,
  setSkills,
  ndcgFloor,
  setNdcgFloor,
  latencyCeiling,
  setLatencyCeiling,
  canaryTraffic,
  setCanaryTraffic
}) => {
  const toggleSkill = (key: keyof typeof skills) => {
    setSkills(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const skillList = [
    {
      key: 'catalogEnrichment',
      label: 'catalog-enrichment-qa',
      desc: 'Catalog Optimization Agent triages missing attributes & taxonomy gaps',
      type: 'Catalog QA Agent',
      behavior: 'Propose bounded taxonomy patches, then validate with offline evals.',
      temporal: 'Event-triggered when exit clusters cross threshold.',
      approval: 'Auto unless quality or latency guardrail fails.',
    },
    {
      key: 'semanticIndex',
      label: 'semantic-index-refresh',
      desc: 'Vector Search Agent computes seasonal embedding drift and scopes refreshes',
      type: 'Vector Refresh',
      behavior: 'Detect drift, refresh embeddings, and compare shadow-query relevance.',
      temporal: 'Daily schedule with anomaly-triggered fast path.',
      approval: 'Auto for refresh; human approval for model family change.',
    },
    {
      key: 'autocompleteTuning',
      label: 'autocomplete-tuning',
      desc: 'Smart Autocomplete Agent aggregates slang synonyms and failed prefixes',
      type: 'Autocomplete Tuning',
      behavior: 'Create typo and synonym candidates with rewrite-scope checks.',
      temporal: 'Hourly failed-prefix replay.',
      approval: 'Conditional when protected terms or broad rewrites appear.',
    },
    {
      key: 'mxpGovernance',
      label: 'mxp-rule-governance',
      desc: 'Merchandising Rules Agent checks boosted clearances against conversions',
      type: 'Rule Governance',
      behavior: 'Recommend rule changes, retain rollback snapshots, and require sign-off.',
      temporal: '6-hour scan plus anomaly-triggered workflow.',
      approval: 'Human approval required for production merchandising mutation.',
    },
    {
      key: 'multimodalQa',
      label: 'multimodal-input-qa',
      desc: 'Multimodal Search Agent monitors image-to-text embedding regressions',
      type: 'Multimodal QA',
      behavior: 'Compare visual-text retrieval against golden query-image pairs.',
      temporal: 'Nightly regression suite.',
      approval: 'Auto for alerting; human approval for release changes.',
    },
  ] as const;

  return (
    <div className="registry-grid">
      
      {/* Runbook Skills Table */}
      <div className="card">
        <div className="card-header">
          <h3>
            <Sliders size={18} style={{ color: 'var(--primary)' }} />
            <span>Active Runbook Automation Skills</span>
          </h3>
          <span className="ui-badge" style={{ background: 'var(--success-glow)', color: 'var(--success)' }}>
            {Object.values(skills).filter(Boolean).length} Active Agent Loops
          </span>
        </div>
        <p className="policy-description" style={{ marginBottom: '1.25rem' }}>
          Enable or disable automated agents. Disabled agents will not triage signals or queue active runbooks in the incident board.
        </p>

        <div className="registry-table">
          {skillList.map((skill) => (
            <div key={skill.key} className="registry-row">
              <div className="registry-row-info">
                <strong>{skill.label}</strong>
                <span>{skill.desc}</span>
              </div>
              <div className="registry-row-meta">
                <span>Agent Type: <strong>{skill.type}</strong></span>
                <span>Behavior: <strong>{skill.behavior}</strong></span>
                <span>Temporal: <strong>{skill.temporal}</strong></span>
                <span>Approval: <strong>{skill.approval}</strong></span>
              </div>
              <div>
                <button 
                  type="button" 
                  className={`switch ${skills[skill.key] ? 'active' : ''}`}
                  onClick={() => toggleSkill(skill.key)}
                  aria-label={`Toggle ${skill.label}`}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Global Release Policies */}
      <div className="card">
        <div className="card-header">
          <h3>
            <Settings size={18} style={{ color: 'var(--primary)' }} />
            <span>Global Release Policies</span>
          </h3>
        </div>
        <p className="policy-description" style={{ marginBottom: '1rem' }}>
          Policies govern the Temporal gates. Evaluated NDCG below the floor triggers manual approvals. Latency spikes above ceiling halt canaries.
        </p>

        <div className="policy-inputs">
          <div className="policy-field">
            <label htmlFor="ndcg-input">
              <Sparkles size={12} style={{ marginRight: '0.25rem' }} />
              Auto-approve NDCG floor
            </label>
            <input 
              id="ndcg-input"
              type="text" 
              value={ndcgFloor}
              onChange={(e) => setNdcgFloor(e.target.value)}
              placeholder="0.84"
            />
          </div>

          <div className="policy-field">
            <label htmlFor="latency-input">
              <Clock size={12} style={{ marginRight: '0.25rem' }} />
              P95 latency ceiling
            </label>
            <input 
              id="latency-input"
              type="text" 
              value={latencyCeiling}
              onChange={(e) => setLatencyCeiling(e.target.value)}
              placeholder="150ms"
            />
          </div>

          <div className="policy-field">
            <label htmlFor="canary-input">
              <ShieldAlert size={12} style={{ marginRight: '0.25rem' }} />
              Initial canary traffic
            </label>
            <input 
              id="canary-input"
              type="text" 
              value={canaryTraffic}
              onChange={(e) => setCanaryTraffic(e.target.value)}
              placeholder="5%"
            />
          </div>
        </div>
      </div>

    </div>
  );
};
