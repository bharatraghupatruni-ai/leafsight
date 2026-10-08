import React, { useRef, useState } from 'react';

export default function ImageUploader({
  selectedFile,
  previewUrl,
  imageMeta,
  imageSource,
  groundTruth,
  onFileSelect,
  onClear,
  onAnalyze,
  isAnalyzing,
}) {
  const fileInputRef = useRef(null);
  const [isDragOver, setIsDragOver] = useState(false);

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) {
      onFileSelect(file, 'EXTERNAL IMAGE', null);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => setIsDragOver(false);

  const handleClickZone = () => {
    if (!selectedFile && !isAnalyzing) {
      fileInputRef.current?.click();
    }
  };

  const handleKeyZone = (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleClickZone();
    }
  };

  const isVerifiedSample = imageSource === 'VERIFIED TEST SAMPLE';
  const canAnalyze = !!selectedFile && !isAnalyzing;

  return (
    <div className="lv-lab" id="image-lab">
      <div className="lv-section-head">
        <h2 className="lv-section-head__title">IMAGE LAB</h2>
        <span className="label">
          {selectedFile ? (isVerifiedSample ? 'VERIFIED SAMPLE' : 'EXTERNAL INPUT') : 'INPUT WORKSPACE'}
        </span>
      </div>

      {/* Drop / Preview Zone */}
      <div
        className={`lv-dropzone ${selectedFile ? 'has-image' : ''} ${isDragOver ? 'drag-over' : ''}`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={handleClickZone}
        onKeyDown={handleKeyZone}
        role={selectedFile ? undefined : 'button'}
        tabIndex={selectedFile ? -1 : 0}
        aria-label={selectedFile ? 'Loaded rice leaf image' : 'Upload rice leaf image'}
      >
        {!selectedFile ? (
          <>
            <div className="lv-dropzone__grid" aria-hidden="true" />
            <div className="lv-dropzone__empty">
              <div className="lv-dropzone__icon" aria-hidden="true">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                  <polyline points="17 8 12 3 7 8" />
                  <line x1="12" y1="3" x2="12" y2="15" />
                </svg>
              </div>
              <p className="lv-dropzone__title">Drop rice leaf image here</p>
              <p className="lv-dropzone__hint">or click to browse from device, or pick a verified sample below</p>
              <div className="lv-dropzone__fmts" aria-label="Supported image formats">
                {['PNG', 'JPG', 'JPEG', 'WEBP'].map((fmt) => (
                  <span key={fmt} className="lv-dropzone__fmt">{fmt}</span>
                ))}
              </div>
            </div>
          </>
        ) : (
          <div className="lv-img-preview">
            <img
              className="lv-img-preview__img"
              src={previewUrl}
              alt={selectedFile.name || 'Rice leaf preview'}
            />

            {/* Bottom metadata strip */}
            <div className="lv-img-preview__overlay" aria-hidden="true">
              <div className="lv-img-preview__meta">
                <span className="lv-img-preview__fname">{selectedFile.name}</span>
                <span className="lv-img-preview__dims">
                  {imageMeta.width > 0 ? `${imageMeta.width} × ${imageMeta.height}` : 'IMAGE'}
                  {imageMeta.size ? ` · ${imageMeta.size}` : ''}
                </span>
              </div>
              <div className="lv-img-preview__source">
                <span className="lv-img-preview__src-label">SOURCE</span>
                <span className={`lv-img-preview__src-val ${isVerifiedSample ? 'is-verified' : ''}`}>
                  {imageSource || 'EXTERNAL IMAGE'}
                </span>
              </div>
            </div>

            {/* Clear button */}
            {!isAnalyzing && (
              <button
                type="button"
                className="lv-img-preview__clear"
                onClick={(e) => {
                  e.stopPropagation();
                  onClear();
                }}
                aria-label="Remove image"
                title="Remove image"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            )}

            {/* Real-time scanning animation overlay while analyzing */}
            {isAnalyzing && (
              <div className="lv-scan" aria-live="polite" aria-label="Analyzing image with ViT-B/16 and GRU">
                <div className="lv-scan__grid" aria-hidden="true" />
                <div className="lv-scan__line" aria-hidden="true" />
                <div className="lv-scan__content">
                  <p className="lv-scan__title">ANALYZING IMAGE</p>
                  <div className="lv-scan__steps">
                    <span className="lv-scan__step">ViT-B/16 PATCH EXTRACTION</span>
                    <span className="lv-scan__step">196 TOKEN ATTENTION ROLLOUT</span>
                    <span className="lv-scan__step">GRU SEQUENCE CLASSIFICATION</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/png,image/jpeg,image/webp,image/bmp"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) {
            onFileSelect(file, 'EXTERNAL IMAGE', null);
          }
        }}
        style={{ display: 'none' }}
        aria-label="Choose image file"
      />

      {/* Ground Truth badge if verified sample */}
      {selectedFile && isVerifiedSample && groundTruth && (
        <div className="lv-gt-badge" aria-label="Verified sample details">
          <div className="lv-gt-badge__item">
            <span className="lv-gt-badge__label">DATASET SOURCE</span>
            <span className="lv-gt-badge__val">data/processed/test/</span>
          </div>
          <div className="lv-gt-badge__item">
            <span className="lv-gt-badge__label">GROUND TRUTH</span>
            <span className="lv-gt-badge__val" style={{ color: 'var(--c-accent)' }}>{groundTruth}</span>
          </div>
          <div className="lv-gt-badge__item">
            <span className="lv-gt-badge__label">SAMPLE STATUS</span>
            <span className="lv-gt-badge__val">HELD-OUT TEST SAMPLE</span>
          </div>
        </div>
      )}

      {/* Action buttons */}
      <div className="lv-action-bar">
        <button
          id="analyze-btn"
          type="button"
          className="btn btn-primary"
          onClick={onAnalyze}
          disabled={!canAnalyze}
          aria-label={isAnalyzing ? 'Analyzing image…' : 'Analyze Leaf'}
          aria-busy={isAnalyzing}
        >
          {isAnalyzing ? (
            <>
              <span className="btn__spin" aria-hidden="true" />
              <span>Analyzing…</span>
            </>
          ) : (
            <>
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <circle cx="11" cy="11" r="8" />
                <line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
              <span>Analyze Leaf</span>
            </>
          )}
        </button>

        {selectedFile && !isAnalyzing && (
          <button
            type="button"
            className="btn btn-ghost"
            onClick={onClear}
            aria-label="Reset and upload another image"
            title="Reset"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
              <polyline points="1 4 1 10 7 10" />
              <path d="M3.51 15a9 9 0 1 0 .49-3.45" />
            </svg>
            <span>Reset</span>
          </button>
        )}
      </div>
    </div>
  );
}
