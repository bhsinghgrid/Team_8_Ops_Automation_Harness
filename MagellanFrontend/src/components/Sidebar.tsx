import React from 'react';
import { 
  BarChart3, 
  Layers, 
  Sliders, 
  SearchCode, 
  History, 
  Terminal,
  Beaker,
  Factory
} from 'lucide-react';

interface SidebarProps {
  currentTab: string;
  setCurrentTab: (tab: string) => void;
  openIncidentsCount: number;
  backendStatus?: 'loading' | 'connected' | 'offline';
  temporalConnected?: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({ 
  currentTab, 
  setCurrentTab, 
  openIncidentsCount,
  backendStatus = 'offline',
  temporalConnected = false
}) => {
  const menuItems = [
    { id: 'overview', label: 'Overview', icon: BarChart3 },
    { id: 'factory', label: 'Ops Factory', icon: Factory },
    { id: 'queue', label: 'Ops Runbooks', icon: Layers, badge: openIncidentsCount },
    { id: 'registry', label: 'Runbook Registry', icon: Sliders },
    { id: 'clusters', label: 'Query Clusters', icon: SearchCode },
    { id: 'audit', label: 'Audit Trail', icon: History },
    { id: 'live-test', label: 'Live Test', icon: Beaker },
    { id: 'shadow-reports', label: 'Shadow Reports', icon: Terminal }
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <span className="logo-badge">MGL</span>
        <span className="logo-text">Magellan Ops</span>
      </div>
      
      <nav className="sidebar-nav">
        <ul className="sidebar-menu">
          {menuItems.map((item) => {
            const IconComponent = item.icon;
            const isActive = currentTab === item.id;
            return (
              <li 
                key={item.id} 
                className={`menu-item ${isActive ? 'active' : ''}`}
              >
                <button type="button" onClick={() => setCurrentTab(item.id)}>
                  <IconComponent size={18} />
                  <span>{item.label}</span>
                  {item.badge !== undefined && item.badge > 0 && (
                    <span className="menu-item-badge">{item.badge}</span>
                  )}
                </button>
              </li>
            );
          })}
        </ul>
      </nav>
      
      <div className="sidebar-footer" style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', alignItems: 'flex-start' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.72rem' }}>
          <span style={{ width: '7px', height: '7px', borderRadius: '50%', background: backendStatus === 'connected' ? '#10B981' : '#EF4444', boxShadow: backendStatus === 'connected' ? '0 0 6px #10B981' : '0 0 6px #EF4444' }} />
          <span style={{ color: 'rgba(255,255,255,0.6)' }}>API Source: <strong>{backendStatus === 'connected' ? 'ONLINE' : 'OFFLINE'}</strong></span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.72rem' }}>
          <span style={{ width: '7px', height: '7px', borderRadius: '50%', background: temporalConnected ? '#10B981' : '#EF4444', boxShadow: temporalConnected ? '0 0 6px #10B981' : '0 0 6px #EF4444' }} />
          <span style={{ color: 'rgba(255,255,255,0.6)' }}>Temporal: <strong>{temporalConnected ? 'CONNECTED' : 'DISCONNECTED'}</strong></span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', borderTop: '1px solid rgba(255,255,255,0.08)', width: '100%', paddingTop: '0.4rem', marginTop: '0.2rem', color: 'rgba(255,255,255,0.4)' }}>
          <Terminal size={12} />
          <span style={{ fontSize: '0.65rem' }}>Harness: <strong>v1.2.4-stable</strong></span>
        </div>
      </div>
    </aside>
  );
};
