import React from 'react';

export default function Footer() {
  return (
    <footer className="app-footer">
      <p>
        <strong>LEAFSIGHT</strong> — Intelligent Rice Leaf Disease Recognition System • ViT-B/16 + GRU Classifier
      </p>
      <p style={{ marginTop: 4, fontSize: '0.75rem', color: 'var(--text-muted)' }}>
        Empowering precision agriculture with deep learning attention mechanisms.
      </p>
    </footer>
  );
}
