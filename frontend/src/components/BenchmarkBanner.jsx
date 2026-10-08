import React from 'react';
import { MODEL_BENCHMARKS } from '../config';

const METRICS = [
  { value: MODEL_BENCHMARKS.accuracy, label: 'TEST ACCURACY', accent: true },
  { value: MODEL_BENCHMARKS.macroF1, label: 'MACRO F1', accent: false },
  { value: MODEL_BENCHMARKS.correctPredictions, label: 'CORRECT (720 / 721)', accent: false },
  { value: '721 SAMPLES', label: 'HELD-OUT TEST SET', accent: false },
];

export default function BenchmarkBanner() {
  return (
    <section className="lv-perf" aria-label="Model performance benchmarks">
      <div className="lv-perf__intro">
        <p className="lv-perf__title">MODEL PERFORMANCE</p>
        <p className="lv-perf__arch">{MODEL_BENCHMARKS.architecture}</p>
      </div>

      <div className="lv-perf__metrics" role="list">
        {METRICS.map(({ value, label, accent }) => (
          <div
            key={label}
            className="lv-perf__stat"
            role="listitem"
            aria-label={`${label}: ${value}`}
          >
            <span className={`lv-perf__val ${accent ? 'accent' : ''}`}>{value}</span>
            <span className="lv-perf__lbl">{label}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
