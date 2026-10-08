import React from 'react';
import { Award, Layers, Target, CheckCircle2 } from 'lucide-react';
import { MODEL_BENCHMARKS } from '../config';

export default function BenchmarkBanner() {
  return (
    <div className="benchmark-banner">
      <div className="benchmark-title">
        <Award size={18} />
        <span>Test-Set Performance</span>
      </div>

      <div className="benchmark-stats">
        <div className="benchmark-stat-item">
          <span className="benchmark-stat-label">Model Architecture</span>
          <span className="benchmark-stat-value">{MODEL_BENCHMARKS.architecture}</span>
        </div>

        <div className="benchmark-stat-item">
          <span className="benchmark-stat-label">Test Accuracy</span>
          <span className="benchmark-stat-value" style={{ color: 'var(--primary-800)' }}>
            {MODEL_BENCHMARKS.accuracy}
          </span>
        </div>

        <div className="benchmark-stat-item">
          <span className="benchmark-stat-label">Macro Precision</span>
          <span className="benchmark-stat-value">{MODEL_BENCHMARKS.macroPrecision}</span>
        </div>

        <div className="benchmark-stat-item">
          <span className="benchmark-stat-label">Macro Recall</span>
          <span className="benchmark-stat-value">{MODEL_BENCHMARKS.macroRecall}</span>
        </div>

        <div className="benchmark-stat-item">
          <span className="benchmark-stat-label">Macro F1</span>
          <span className="benchmark-stat-value">{MODEL_BENCHMARKS.macroF1}</span>
        </div>

        <div className="benchmark-stat-item">
          <span className="benchmark-stat-label">Correct Predictions</span>
          <span className="benchmark-stat-value">{MODEL_BENCHMARKS.correctPredictions}</span>
        </div>
      </div>
    </div>
  );
}
