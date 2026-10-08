import React from 'react';

export default function Footer() {
  return (
    <footer className="lv-footer" role="contentinfo">
      <div className="lv-footer__inner">
        <div className="lv-footer__l">
          <strong>LEAFSIGHT VISION LAB</strong> — Intelligent Rice Leaf Disease Recognition System · Held-out Test Set Accuracy: 99.86% (720/721 correct) · Macro F1: 99.85%
        </div>
        <div className="lv-footer__r">
          ViT-B/16 (196 Tokens) · GRU Sequence Classifier · PyTorch 2.6
        </div>
      </div>
    </footer>
  );
}
