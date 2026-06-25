import React, { useEffect, useState } from 'react';

export const Navigation: React.FC = () => {
  const [scrollProgress, setScrollProgress] = useState(0);
  const [activeSection, setActiveSection] = useState('main');
  const [visible, setVisible] = useState(true);
  const [lastScrollY, setLastScrollY] = useState(0);

  useEffect(() => {
    const handleScroll = () => {
      const currentScrollY = window.scrollY;
      
      // Auto hide navigation on scroll down, show on scroll up
      if (currentScrollY > lastScrollY && currentScrollY > 200) {
        setVisible(false);
      } else {
        setVisible(true);
      }
      setLastScrollY(currentScrollY);

      // Scroll progress indicator
      const totalHeight = document.documentElement.scrollHeight - window.innerHeight;
      if (totalHeight > 0) {
        const progress = (currentScrollY / totalHeight) * 100;
        setScrollProgress(progress);
      }

      // Track active section
      const sections = [
        'operating-model',
        'use-cases',
        'scenarios',
        'data-flow',
        'context',
        'user-flow',
        'sequence',
        'ui-screens',
        'roadmap',
        'components'
      ];

      let currentActive = 'main';
      for (const id of sections) {
        const el = document.getElementById(id);
        if (el) {
          const rect = el.getBoundingClientRect();
          // If the section top is near the top of the viewport
          if (rect.top <= 120 && rect.bottom > 120) {
            currentActive = id;
            break;
          }
        }
      }
      setActiveSection(currentActive);
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, [lastScrollY]);

  const navLinks = [
    { label: 'Operating Model', href: '#operating-model' },
    { label: 'Use Cases', href: '#use-cases' },
    { label: 'Scenarios', href: '#scenarios' },
    { label: 'Ops Console', href: '#ui-screens' },
    { label: 'Sequence', href: '#sequence' },
    { label: 'Roadmap', href: '#roadmap' },
    { label: 'Components', href: '#components' }
  ];

  const handleLinkClick = (e: React.MouseEvent<HTMLAnchorElement>, href: string) => {
    e.preventDefault();
    const targetId = href.slice(1);
    const targetEl = document.getElementById(targetId);
    if (targetEl) {
      targetEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  return (
    <nav style={{ transform: visible ? 'translateY(0)' : 'translateY(-100%)' }}>
      <div className="nav-inner">
        <div className="brand">
          <strong>Grid Dynamics</strong> &nbsp;|&nbsp; Magellan AI Search Ops Harness
        </div>
        <div className="nav-links">
          {navLinks.map((link) => {
            const id = link.href.slice(1);
            const isActive = activeSection === id;
            return (
              <a
                key={link.href}
                href={link.href}
                className={isActive ? 'active' : ''}
                aria-current={isActive ? 'true' : undefined}
                onClick={(e) => handleLinkClick(e, link.href)}
              >
                {link.label}
              </a>
            );
          })}
        </div>
      </div>
      <div
        className="scroll-progress"
        aria-hidden="true"
        style={{ width: `${scrollProgress}%` }}
      />
    </nav>
  );
};
