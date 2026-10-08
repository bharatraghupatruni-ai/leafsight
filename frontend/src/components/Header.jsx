import React from 'react';

function LeafIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"
      style={{ display: 'block', flexShrink: 0 }} aria-hidden="true">
      <path d="M2 22 12 12" />
      <path d="M12 12C12 6.5 7.5 2.5 2 3c.5 5.5 4.5 9 10 9z" fill="currentColor" fillOpacity="0.18" />
      <path d="M12 12C12 6.5 16.5 2.5 22 3c-.5 5.5-4.5 9-10 9z" fill="currentColor" fillOpacity="0.10" />
    </svg>
  );
}

function GithubIcon() {
  return (
    <svg viewBox="0 0 20 20" fill="currentColor" style={{ width: 16, height: 16 }} aria-hidden="true">
      <path fillRule="evenodd" clipRule="evenodd"
        d="M10 0C4.477 0 0 4.484 0 10.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483
        0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466
        -.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832
        .092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688
        -.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0110 4.844
        c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027
        .546 1.379.203 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688
        0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855
        0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0020 10.017C20 4.484 15.522 0 10 0z" />
    </svg>
  );
}

export default function Header({ backendStatus }) {
  const isOnline = backendStatus.status === 'ok' && backendStatus.model_loaded;
  const device   = (backendStatus.device || 'cpu').toUpperCase();

  return (
    <nav className="lv-nav" role="navigation" aria-label="Site navigation">
      <div className="lv-nav__inner">
        <div className="lv-brand">
          <span className="lv-brand__mark"><LeafIcon /></span>
          <span className="lv-brand__name">LEAFSIGHT</span>
          <span className="lv-brand__div" aria-hidden="true" />
          <span className="lv-brand__tagline">Intelligent Rice Disease Recognition</span>
        </div>

        <div className="lv-nav__right">
          <div
            className="lv-status"
            role="status"
            aria-label={isOnline ? `Model online on ${device}` : 'Backend offline'}
          >
            <span className={`lv-status__dot ${isOnline ? '' : 'offline'}`} />
            <span className="lv-status__text">{isOnline ? 'READY' : 'OFFLINE'}</span>
            {isOnline && (
              <span className="lv-status__detail">ViT-B/16 + GRU · {device}</span>
            )}
          </div>
          <a
            href="https://github.com/bharatraghupatruni-ai/leafsight"
            target="_blank" rel="noopener noreferrer"
            className="lv-gh-link" aria-label="View source on GitHub"
          >
            <GithubIcon />
            GitHub
          </a>
        </div>
      </div>
    </nav>
  );
}
