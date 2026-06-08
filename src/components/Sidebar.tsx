import React from 'react';
import { 
  BarChart3, 
  Layers, 
  Sliders, 
  SearchCode, 
  History, 
  Terminal,
  Database
} from 'lucide-react';

interface SidebarProps {
  currentTab: string;
  setCurrentTab: (tab: string) => void;
  openIncidentsCount: number;
}

export const Sidebar: React.FC<SidebarProps> = ({ 
  currentTab, 
  setCurrentTab, 
  openIncidentsCount 
}) => {
  const menuItems = [
    { id: 'overview', label: 'Overview', icon: BarChart3 },
    { id: 'queue', label: 'Ops Runbooks', icon: Layers, badge: openIncidentsCount },
    { id: 'registry', label: 'Runbook Registry', icon: Sliders },
    { id: 'clusters', label: 'Query Clusters', icon: SearchCode },
    { id: 'backend', label: 'Backend Details', icon: Database },
    { id: 'audit', label: 'Audit Trail', icon: History }
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
      
      <div className="sidebar-footer">
        <Terminal size={14} />
        <span>Harness: <strong>v1.2.4-stable</strong></span>
      </div>
    </aside>
  );
};
