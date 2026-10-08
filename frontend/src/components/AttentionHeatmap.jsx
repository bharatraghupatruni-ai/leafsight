import React, { useState } from 'react';

const MODES = [
  { id: 'overlay',  label: 'OVERLAY' },
  { id: 'heatmap',  label: 'ATTENTION MAP' },
  { id: 'original', label: 'ORIGINAL' },
];

export default function AttentionHeatmap({
  originalUrl,
  heatmapBase64,
  pureHeatmapBase64,
  description,
}) {
  const [activeMode, setActiveMode] = useState('overlay');

  if (!heatmapBase64) return null;

  const overlaySrc = heatmapBase64.startsWith('data:')
    ? heatmapBase64
    : `data:image/png;base64,${heatmapBase64}`;

  const pureHeatmapSrc = pureHeatmapBase64
    ? (pureHeatmapBase64.startsWith('data:') ? pureHeatmapBase64 : `data:image/png;base64,${pureHeatmapBase64}`)
    : overlaySrc;

  let currentSrc = overlaySrc;
  let currentLabel = 'ATTENTION OVERLAY';
  if (activeMode === 'original') {
    currentSrc = originalUrl;
    currentLabel = 'ORIGINAL INPUT';
  } else if (activeMode === 'heatmap') {
    currentSrc = pureHeatmapSrc;
    currentLabel = 'ATTENTION HEATMAP';
  }

  return (
    <section className="lv-attn" id="attention-viewer" aria-label="ViT Attention Visualization">
      <div className="lv-attn__head">
        <h3 className="lv-attn__title">WHAT THE MODEL ATTENDS TO</h3>
        <p className="lv-attn__desc">
          {description ||
            'Attention visualization showing image regions that received stronger attention during the ViT prediction.'}
        </p>
      </div>

      {/* Segmented controls */}
      <div className="lv-attn__tabs" role="tablist" aria-label="Attention view modes">
        {MODES.map(({ id, label }) => (
          <button
            key={id}
            type="button"
            role="tab"
            aria-selected={activeMode === id}
            className={`lv-attn__tab ${activeMode === id ? 'active' : ''}`}
            onClick={() => setActiveMode(id)}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Image display */}
      <div className="lv-attn__view">
        <div className="lv-attn__img-box">
          <img
            key={activeMode}
            className="lv-attn__img"
            src={currentSrc}
            alt={`${currentLabel} of rice leaf`}
          />
          <span className="lv-attn__badge tl" aria-hidden="true">{currentLabel}</span>
          <span className="lv-attn__badge br" aria-hidden="true">
            ViT-B/16 · 224 × 224 · 14 × 14 PATCH GRID
          </span>
        </div>

        {/* Colormap Legend */}
        {activeMode !== 'original' && (
          <div className="lv-attn__legend" aria-label="Heatmap salience colormap">
            <span style={{ fontWeight: 600 }}>LOW SALIENCE</span>
            <div className="lv-attn__legend-bar" aria-hidden="true" />
            <span style={{ fontWeight: 600 }}>HIGH SALIENCE</span>
          </div>
        )}

        <p style={{ marginTop: 10, fontSize: 11, color: 'var(--c-text-3)', lineHeight: 1.5 }}>
          Visual representation of ViT self-attention rollout across 12 transformer layers (196 patch tokens). Indicates relative feature salience, not proof of biological causation.
        </p>
      </div>
    </section>
  );
}
