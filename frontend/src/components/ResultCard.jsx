import React, { useEffect, useState } from 'react';
import { DISEASE_INFO } from '../config';
import ProbabilityBars from './ProbabilityBars';

export default function ResultCard({
  result,
  imageSource,
  groundTruth,
  onReset,
  isAnalyzing,
}) {
  const [barWidth, setBarWidth] = useState(0);

  const confidence = result?.confidence ?? 0;
  const confPct = (confidence * 100).toFixed(2);
  const isVerifiedSample = imageSource === 'VERIFIED TEST SAMPLE';

  useEffect(() => {
    if (result) {
      setBarWidth(0);
      const t = setTimeout(() => setBarWidth(confidence * 100), 120);
      return () => clearTimeout(t);
    } else {
      setBarWidth(0);
    }
  }, [confidence]);

  const isMatch = Boolean(
    result &&
    groundTruth &&
    result.prediction.toLowerCase().trim() === groundTruth.toLowerCase().trim()
  );

  return (
    <div className="lv-diagnosis" id="diagnosis-panel">
      <div className="lv-section-head">
        <h2 className="lv-section-head__title">DIAGNOSIS</h2>
        <span className="label">
          {result ? 'EVALUATION COMPLETE' : (isAnalyzing ? 'PROCESSING' : 'STANDBY')}
        </span>
      </div>

      {!result ? (
        <div className="lv-diag-empty" id="empty-result-state">
          <div className="lv-diag-empty__icon" aria-hidden="true">
            {isAnalyzing ? (
              <span className="btn__spin" style={{ width: 20, height: 20, borderColor: 'var(--c-accent)', borderTopColor: 'transparent' }} />
            ) : (
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="11" cy="11" r="8" />
                <line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
            )}
          </div>
          <h3 className="lv-diag-empty__h">
            {isAnalyzing ? 'ANALYZING LEAF…' : 'WAITING FOR IMAGE'}
          </h3>
          <p className="lv-diag-empty__p">
            {isAnalyzing
              ? 'Evaluating 196 patch tokens across 12 ViT layers and sequence GRU classifier.'
              : 'Upload a leaf image or select any verified test sample to run disease recognition.'}
          </p>
        </div>
      ) : (
        <div className="lv-pred" id="prediction-card">
          {/* Top: disease name + confidence */}
          <div className="lv-pred__top">
            <div className="lv-pred__left">
              <p className="lv-pred__eyebrow">PREDICTED DISEASE</p>
              <h3 className="lv-pred__name">
                {DISEASE_INFO[result.prediction]?.displayName ?? result.prediction}
              </h3>
            </div>
            <div className="lv-pred__right">
              <div className="lv-pred__conf-val">{confPct}%</div>
              <div className="lv-pred__conf-lbl">CONFIDENCE</div>
            </div>
          </div>

          {/* Thin confidence bar */}
          <div className="lv-conf-bar" role="progressbar" aria-valuenow={barWidth} aria-valuemin={0} aria-valuemax={100} aria-label="Confidence percentage">
            <div className="lv-conf-bar__fill" style={{ width: `${barWidth}%` }} />
          </div>

          {/* Verification section: Ground Truth vs Prediction for Verified Samples */}
          {isVerifiedSample && groundTruth && (
            <div className="lv-verif" aria-label="Ground truth verification">
              <div className="lv-verif__item">
                <span className="lv-verif__lbl">SOURCE</span>
                <span className="lv-verif__val">TEST DATASET</span>
              </div>
              <div className="lv-verif__item">
                <span className="lv-verif__lbl">GROUND TRUTH</span>
                <span className="lv-verif__val" style={{ color: 'var(--c-accent)' }}>{groundTruth}</span>
              </div>
              <div className="lv-verif__item">
                <span className="lv-verif__lbl">MODEL PREDICTION</span>
                <span className="lv-verif__val">{result.prediction}</span>
              </div>
              <div className="lv-verif__item">
                <span className="lv-verif__lbl">STATUS</span>
                <span className={`lv-verif__status ${isMatch ? 'correct' : 'wrong'}`}>
                  {isMatch ? '✓ CORRECT MATCH' : '▲ MISCLASSIFIED'}
                </span>
              </div>
            </div>
          )}

          {/* External image verification state */}
          {!isVerifiedSample && (
            <>
              <div className="lv-verif" aria-label="External image verification">
                <div className="lv-verif__item">
                  <span className="lv-verif__lbl">SOURCE</span>
                  <span className="lv-verif__val">EXTERNAL IMAGE</span>
                </div>
                <div className="lv-verif__item">
                  <span className="lv-verif__lbl">MODEL PREDICTION</span>
                  <span className="lv-verif__val">{result.prediction}</span>
                </div>
                <div className="lv-verif__item">
                  <span className="lv-verif__lbl">STATUS</span>
                  <span className="lv-verif__status" style={{ background: 'var(--c-surface-2)', color: 'var(--c-text-2)' }}>
                    UNVERIFIED GROUND TRUTH
                  </span>
                </div>
              </div>

              {/* Informational domain note */}
              <div className="lv-ext-note" role="note">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <circle cx="12" cy="12" r="10" />
                  <line x1="12" y1="8" x2="12" y2="12" />
                  <line x1="12" y1="16" x2="12.01" y2="16" />
                </svg>
                <span>
                  Predictions on external images may differ from held-out test-set results because image quality, background, lighting, camera angle, and disease stage can vary from the training distribution.
                </span>
              </div>
            </>
          )}

          {/* Class probabilities list */}
          <ProbabilityBars
            probabilities={result.probabilities}
            predictedClass={result.prediction}
          />

          {/* Footer actions */}
          <div className="lv-pred__footer">
            <button
              type="button"
              className="btn btn-ghost btn-sm"
              onClick={onReset}
              id="reset-analysis-btn"
              aria-label="Clear and analyze new image"
            >
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
                <polyline points="1 4 1 10 7 10" />
                <path d="M3.51 15a9 9 0 1 0 .49-3.45" />
              </svg>
              <span>New Analysis</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
