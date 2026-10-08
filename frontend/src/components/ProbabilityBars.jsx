import React from 'react';
import { BarChart3 } from 'lucide-react';
import { DISEASE_INFO } from '../config';

export default function ProbabilityBars({ probabilities, predictedClass }) {
  if (!probabilities) return null;

  const diseaseKeys = ["Bacterialblight", "Blast", "Brownspot", "Tungro"];

  return (
    <div className="card" style={{ marginTop: '24px' }}>
      <div className="card-header">
        <div className="card-title-group">
          <BarChart3 size={20} color="var(--primary-800)" />
          <div>
            <h3 className="card-title">Class Probabilities</h3>
            <p className="card-subtitle">Distribution across the 4 rice pathology classes</p>
          </div>
        </div>
      </div>

      <div className="probabilities-list">
        {diseaseKeys.map((key) => {
          const prob = probabilities[key] ?? 0;
          const percent = (prob * 100).toFixed(2);
          const isWinner = key === predictedClass;
          const label = DISEASE_INFO[key]?.displayName || key;

          return (
            <div key={key} className="prob-row">
              <div className="prob-label-row">
                <span className={`prob-class-name ${isWinner ? 'winner' : ''}`}>
                  {label} {isWinner && <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--primary-700)' }}>• Primary Match</span>}
                </span>
                <span className="prob-value">{percent}%</span>
              </div>

              <div className="prob-bar-track">
                <div
                  className={`prob-bar-fill ${isWinner ? 'winner' : ''}`}
                  style={{ width: `${Math.max(parseFloat(percent), 0.5)}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
