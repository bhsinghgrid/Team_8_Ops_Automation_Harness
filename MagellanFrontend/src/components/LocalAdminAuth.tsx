import React, { useState } from 'react';
import { Shield, Lock, User, Terminal, Eye, EyeOff, AlertCircle } from 'lucide-react';

interface LocalAdminAuthProps {
  onLoginSuccess: (username: string) => void;
}

export const LocalAdminAuth: React.FC<LocalAdminAuthProps> = ({ onLoginSuccess }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    // Simulated attractive login credentials check (standard for local ops harness)
    setTimeout(() => {
      if (username.trim().toLowerCase() === 'admin' && password === 'admin') {
        localStorage.setItem('magellan_auth_user', 'admin');
        onLoginSuccess('admin');
      } else {
        setError('Invalid operator credentials. Access Denied.');
      }
      setIsSubmitting(false);
    }, 800);
  };

  return (
    <div className="admin-auth-container">
      <style>{`
        .admin-auth-container {
          min-height: 100vh;
          width: 100vw;
          display: flex;
          align-items: center;
          justify-content: center;
          background: 
            radial-gradient(circle at top left, rgba(224, 169, 40, 0.12), transparent 45rem),
            radial-gradient(circle at bottom right, rgba(139, 58, 43, 0.12), transparent 45rem),
            linear-gradient(135deg, #120E0A 0%, #1A1511 100%);
          font-family: 'IBM Plex Sans', -apple-system, sans-serif;
          position: fixed;
          inset: 0;
          z-index: 9999;
          overflow-y: auto;
          padding: 1.5rem;
        }

        .auth-background-grid {
          position: absolute;
          inset: 0;
          pointer-events: none;
          background-image:
            linear-gradient(rgba(255, 255, 255, 0.02) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255, 255, 255, 0.02) 1px, transparent 1px);
          background-size: 40px 42px;
          mask-image: radial-gradient(circle at center, black 40%, transparent 90%);
        }

        .auth-glass-card {
          width: 100%;
          max-width: 440px;
          background: rgba(42, 33, 26, 0.45);
          backdrop-filter: blur(20px);
          border: 1px solid rgba(224, 169, 40, 0.15);
          border-radius: 20px;
          padding: 2.5rem;
          box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5), 0 0 40px rgba(224, 169, 40, 0.03);
          position: relative;
          z-index: 10;
          display: flex;
          flex-direction: column;
          gap: 1.75rem;
          animation: authCardEntrance 0.5s cubic-bezier(0.16, 1, 0.3, 1);
        }

        @keyframes authCardEntrance {
          from {
            opacity: 0;
            transform: translateY(15px) scale(0.98);
          }
          to {
            opacity: 1;
            transform: translateY(0) scale(1);
          }
        }

        .auth-logo-row {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 0.5rem;
          text-align: center;
        }

        .auth-badge {
          background: linear-gradient(135deg, #8B3A2B, #E0A928);
          color: white;
          font-family: 'JetBrains Mono', monospace;
          font-weight: 800;
          padding: 0.4rem 0.75rem;
          border-radius: 10px;
          font-size: 0.85rem;
          letter-spacing: 0.05em;
          box-shadow: 0 10px 20px rgba(139, 58, 43, 0.3);
        }

        .auth-heading {
          font-family: 'Fraunces', serif;
          font-size: 1.85rem;
          font-weight: 800;
          color: white;
          letter-spacing: -0.02em;
          margin-top: 0.5rem;
        }

        .auth-subheading {
          font-size: 0.82rem;
          color: rgba(255, 255, 255, 0.5);
          line-height: 1.4;
        }

        .auth-form {
          display: flex;
          flex-direction: column;
          gap: 1.25rem;
        }

        .auth-input-group {
          display: flex;
          flex-direction: column;
          gap: 0.35rem;
        }

        .auth-label {
          font-size: 0.68rem;
          font-weight: 800;
          color: rgba(255, 255, 255, 0.4);
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }

        .auth-input-wrapper {
          position: relative;
          display: flex;
          align-items: center;
        }

        .auth-input-icon {
          position: absolute;
          left: 0.85rem;
          color: rgba(255, 255, 255, 0.3);
        }

        .auth-input {
          width: 100%;
          background: rgba(0, 0, 0, 0.3);
          border: 1px solid rgba(255, 255, 255, 0.08);
          border-radius: 10px;
          padding: 0.75rem 1rem 0.75rem 2.5rem;
          color: white;
          font-size: 0.85rem;
          outline: none;
          transition: all 0.2s;
        }

        .auth-input:focus {
          border-color: #E0A928;
          box-shadow: 0 0 12px rgba(224, 169, 40, 0.15);
          background: rgba(0, 0, 0, 0.4);
        }

        .password-toggle-btn {
          position: absolute;
          right: 0.85rem;
          background: transparent;
          border: none;
          color: rgba(255, 255, 255, 0.3);
          cursor: pointer;
          display: flex;
          align-items: center;
          padding: 0;
        }

        .password-toggle-btn:hover {
          color: rgba(255, 255, 255, 0.6);
        }

        .auth-error-box {
          background: rgba(239, 68, 68, 0.1);
          border: 1px solid rgba(239, 68, 68, 0.25);
          border-radius: 8px;
          padding: 0.75rem;
          display: flex;
          align-items: center;
          gap: 0.5rem;
          color: #FC8181;
          font-size: 0.75rem;
          animation: shakeError 0.35s ease;
        }

        @keyframes shakeError {
          0%, 100% { transform: translateX(0); }
          25% { transform: translateX(-4px); }
          75% { transform: translateX(4px); }
        }

        .auth-submit-btn {
          background: linear-gradient(135deg, #8B3A2B 0%, #D47D34 100%);
          color: white;
          font-weight: 800;
          font-size: 0.85rem;
          border: none;
          padding: 0.85rem;
          border-radius: 10px;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 0.5rem;
          transition: all 0.2s;
          box-shadow: 0 6px 15px rgba(139, 58, 43, 0.2);
        }

        .auth-submit-btn:hover:not(:disabled) {
          transform: translateY(-1px);
          box-shadow: 0 8px 20px rgba(139, 58, 43, 0.3);
          background: linear-gradient(135deg, #9C4131 0%, #E28941 100%);
        }

        .auth-submit-btn:disabled {
          background: rgba(255, 255, 255, 0.08);
          color: rgba(255, 255, 255, 0.3);
          cursor: not-allowed;
          box-shadow: none;
        }

        .auth-footer {
          border-top: 1px solid rgba(255, 255, 255, 0.05);
          padding-top: 1rem;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 0.35rem;
          color: rgba(255, 255, 255, 0.35);
          font-size: 0.68rem;
          font-family: 'JetBrains Mono', monospace;
        }
      `}</style>
      <div className="auth-background-grid" />

      <div className="auth-glass-card">
        <div className="auth-logo-row">
          <span className="auth-badge">MGL</span>
          <h2 className="auth-heading">Operator Gateway</h2>
          <p className="auth-subheading">
            Authenticate to access Magellan's local self-healing search automation orchestrator.
          </p>
        </div>

        <form className="auth-form" onSubmit={handleLogin}>
          {/* Operator Username */}
          <div className="auth-input-group">
            <label className="auth-label">Operator ID</label>
            <div className="auth-input-wrapper">
              <User size={15} className="auth-input-icon" />
              <input
                type="text"
                className="auth-input"
                required
                placeholder="e.g. admin"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
              />
            </div>
          </div>

          {/* Secure Access PIN/Pass */}
          <div className="auth-input-group">
            <label className="auth-label">Access Passcode</label>
            <div className="auth-input-wrapper">
              <Lock size={15} className="auth-input-icon" />
              <input
                type={showPassword ? 'text' : 'password'}
                className="auth-input"
                required
                placeholder="••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              <button
                type="button"
                className="password-toggle-btn"
                onClick={() => setShowPassword(!showPassword)}
              >
                {showPassword ? <EyeOff size={15} /> : <Eye size={15} />}
              </button>
            </div>
          </div>

          {error && (
            <div className="auth-error-box">
              <AlertCircle size={15} className="shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <button
            type="submit"
            className="auth-submit-btn"
            disabled={isSubmitting || !username || !password}
          >
            {isSubmitting ? (
              <>
                <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" style={{ width: '16px', height: '16px' }}>
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                <span>Verifying Security Keys...</span>
              </>
            ) : (
              <>
                <Shield size={16} />
                <span>Initialize Operator Session</span>
              </>
            )}
          </button>
        </form>

        <div className="auth-footer">
          <Terminal size={11} />
          <span>Local Session Router: v1.2.4-stable</span>
        </div>
      </div>
    </div>
  );
};
