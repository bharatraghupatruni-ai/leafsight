import React from 'react';
import { Activity, ShieldAlert, RotateCcw, Stethoscope, CheckCircle2 } from 'lucide-react';
import { DISEASE_INFO } from '../config';

export default function ResultCard({ result, onReset }) {
  if (!result) return null;

  const diseaseKey = result.prediction;
  const info = DISEASE_INFO[diseaseKey] || {
    displayName: diseaseKey,
    pathogen: "Plant Pathogen",
    symptoms: "Characteristic foliar lesions on rice leaf tissue.",
    management: "Inspect field conditions and apply appropriate crop management protocols.",
    severity: "Identified"
  };

  const confidencePercent = (result.confidence * 100).toFixed(2);

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title-group">
          <Activity size={20} color="var(--primary-800)" />
          <div>
            <h2 className="card-title">Diagnostic Results</h2>
            <p className="card-subtitle">ViT-B/16 + GRU Classifier Prediction</p>
          </div>
        </div>

        <button
          type="button"
          className="btn btn-secondary"
          onClick={onReset}
          style={{ padding: '6px 12px', fontSize: '0.8rem' }}
        >
          <RotateCcw size={14} />
          <span>Reset</span>
        </button>
      </div>

      <div className="result-header-badge">
        <div>
          <span style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
            Predicted Disease
          </span>
          <div className="result-disease-name">{info.displayName}</div>
        </div>

        <div className="result-confidence-pill">
          {confidencePercent}%
          <span style={{ fontSize: '0.72rem', display: 'block', fontWeight: 500, color: 'var(--text-muted)' }}>
            confidence
          </span>
        </div>
      </div>

      <div className="disease-details-box">
        <div className="disease-detail-row">
          <strong>Causal Pathogen</strong>
          <p style={{ fontStyle: 'italic' }}>{info.pathogen}</p>
        </div>

        <div className="disease-detail-row">
          <strong>Symptoms</strong>
          <p>{info.symptoms}</p>
        </div>

        <div className="disease-detail-row">
          <strong>Recommended Management</strong>
          <p>{info.management}</p>
        </div>
      </div>
    </div>
  );
}
