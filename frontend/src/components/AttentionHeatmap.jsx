import React, { useState } from 'react';
import { Eye, Layers, Split, Image as ImageIcon, Info } from 'lucide-react';

export default function AttentionHeatmap({ originalUrl, heatmapBase64, description }) {
  const [viewMode, setViewMode] = useState('side-by-side'); // 'side-by-side' | 'heatmap' | 'original'

  if (!heatmapBase64 && !originalUrl) return null;

  return (
    <div className="card attention-card">
      <div className="card-header">
        <div className="card-title-group">
          <Eye size={20} color="var(--primary-800)" />
          <div>
            <h3 className="card-title">Model Attention</h3>
            <p className="card-subtitle">ViT Layer Attention Rollout Map</p>
          </div>
        </div>
      </div>

      <div className="attention-desc-box">
        <p>
          {description ||
            'This visualization highlights image regions that received stronger attention during the prediction.'}
        </p>
      </div>

      <div className="visual-tabs">
        <button
          type="button"
          className={`visual-tab-btn ${viewMode === 'side-by-side' ? 'active' : ''}`}
          onClick={() => setViewMode('side-by-side')}
        >
          <Split size={14} style={{ display: 'inline', marginRight: 4, verticalAlign: 'middle' }} />
          Side-by-Side
        </button>
        <button
          type="button"
          className={`visual-tab-btn ${viewMode === 'heatmap' ? 'active' : ''}`}
          onClick={() => setViewMode('heatmap')}
        >
          <Layers size={14} style={{ display: 'inline', marginRight: 4, verticalAlign: 'middle' }} />
          Attention Map
        </button>
        <button
          type="button"
          className={`visual-tab-btn ${viewMode === 'original' ? 'active' : ''}`}
          onClick={() => setViewMode('original')}
        >
          <ImageIcon size={14} style={{ display: 'inline', marginRight: 4, verticalAlign: 'middle' }} />
          Original Leaf
        </button>
      </div>

      <div className={`visual-display-grid ${viewMode === 'side-by-side' ? 'side-by-side' : ''}`}>
        {(viewMode === 'side-by-side' || viewMode === 'original') && originalUrl && (
          <div className="visual-frame">
            <div className="visual-frame-header">
              <span>Original Leaf Image</span>
              <span>224×224</span>
            </div>
            <img src={originalUrl} alt="Original Rice Leaf" className="visual-frame-img" />
          </div>
        )}

        {(viewMode === 'side-by-side' || viewMode === 'heatmap') && heatmapBase64 && (
          <div className="visual-frame">
            <div className="visual-frame-header">
              <span>Attention Visualization (Rollout Overlay)</span>
              <span>Jet Colormap</span>
            </div>
            <img src={heatmapBase64} alt="Attention Rollout Overlay" className="visual-frame-img" />
          </div>
        )}
      </div>
    </div>
  );
}
