import React from 'react';
import { Leaf, Cpu, CheckCircle2, AlertCircle } from 'lucide-react';

export default function Header({ backendStatus }) {
  const isOnline = backendStatus.status === 'ok' && backendStatus.model_loaded;
  const deviceName = (backendStatus.device || 'cpu').toUpperCase();

  return (
    <header className="app-header">
      <div className="header-inner">
        <div className="brand-section">
          <div className="brand-icon">
            <Leaf size={22} strokeWidth={2.4} />
          </div>
          <div className="brand-text">
            <h1>LEAFSIGHT</h1>
            <p>Intelligent Rice Disease Recognition</p>
          </div>
        </div>

        <div className="header-badges">
          <div className="status-badge" title={`Backend status on ${deviceName}`}>
            <span className={`status-dot ${isOnline ? '' : 'offline'}`} />
            {isOnline ? (
              <span>Model Active ({deviceName})</span>
            ) : (
              <span>Connecting to Backend...</span>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
