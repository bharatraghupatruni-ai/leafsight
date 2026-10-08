import React, { useEffect, useState } from 'react';
import { DISEASE_INFO } from '../config';

const CLASS_ORDER = ['Bacterialblight', 'Blast', 'Brownspot', 'Tungro'];

export default function ProbabilityBars({ probabilities, predictedClass }) {
  const [animated, setAnimated] = useState(false);

  useEffect(() => {
    setAnimated(false);
    const t = setTimeout(() => setAnimated(true), 100);
    return () => clearTimeout(t);
  }, [probabilities]);

  if (!probabilities) return null;

  // Sorted entries descending by probability
  const entries = CLASS_ORDER.map((cls) => ({
    cls,
    displayName: DISEASE_INFO[cls]?.displayName ?? cls,
    prob: probabilities[cls] ?? 0,
    isWinner: cls.toLowerCase() === (predictedClass || '').toLowerCase(),
  })).sort((a, b) => b.prob - a.prob);

  return (
    <div className="lv-probs" id="probability-bars" aria-label="Class softmax probabilities">
      <div className="lv-probs__head">
        <span className="label">SOFTMAX OUTPUT</span>
        <span className="label" style={{ fontWeight: 400, textTransform: 'none' }}>
          Calibrated Distribution
        </span>
      </div>

      <div className="lv-probs__list" role="list">
        {entries.map(({ cls, displayName, prob, isWinner }) => {
          const pct = (prob * 100).toFixed(2);
          const barW = animated ? prob * 100 : 0;
          return (
            <div
              key={cls}
              className="lv-prob-row"
              role="listitem"
              aria-label={`${displayName}: ${pct}%`}
            >
              <div className="lv-prob-row__info">
                <span className={`lv-prob-row__name ${isWinner ? 'winner' : ''}`}>
                  {displayName}
                </span>
                <span className={`lv-prob-row__pct ${isWinner ? 'winner' : ''}`}>
                  {pct}%
                </span>
              </div>
              <div className="lv-prob-row__track" role="presentation">
                <div
                  className={`lv-prob-row__fill ${isWinner ? 'winner' : ''}`}
                  style={{ width: `${barW}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
