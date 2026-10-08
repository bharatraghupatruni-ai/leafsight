import React, { useRef, useState } from 'react';
import { UploadCloud, Image as ImageIcon, X, Sparkles, AlertTriangle } from 'lucide-react';

export default function ImageUploader({
  selectedFile,
  previewUrl,
  imageMeta,
  onFileSelect,
  onClear,
  onAnalyze,
  isAnalyzing,
  onSelectSample
}) {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      onFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      onFileSelect(e.target.files[0]);
    }
  };

  const triggerFileInput = () => {
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
      fileInputRef.current.click();
    }
  };

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title-group">
          <ImageIcon size={20} color="var(--primary-800)" />
          <div>
            <h2 className="card-title">Leaf Image Input</h2>
            <p className="card-subtitle">Upload or select a rice leaf image for disease diagnosis</p>
          </div>
        </div>
      </div>

      <input
        ref={fileInputRef}
        type="file"
        accept="image/png, image/jpeg, image/jpg, image/webp"
        style={{ display: 'none' }}
        onChange={handleFileChange}
      />

      {!previewUrl ? (
        <div
          className={`dropzone ${isDragging ? 'active' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={triggerFileInput}
        >
          <div className="dropzone-icon-circle">
            <UploadCloud size={28} />
          </div>
          <p className="dropzone-main-text">Upload a rice leaf image</p>
          <p className="dropzone-sub-text">Drag & drop or click to browse (PNG, JPG, JPEG)</p>
        </div>
      ) : (
        <div>
          <div className="preview-wrapper">
            <img src={previewUrl} alt="Selected rice leaf preview" className="preview-image" />
            <button
              type="button"
              className="preview-clear-btn"
              onClick={onClear}
              title="Remove image"
              disabled={isAnalyzing}
            >
              <X size={18} />
            </button>
            <div className="preview-overlay-info">
              <span>{selectedFile?.name || 'Uploaded Leaf Image'}</span>
              <span>
                {imageMeta.width && imageMeta.height ? `${imageMeta.width}×${imageMeta.height} px` : ''}
                {imageMeta.size ? ` • ${imageMeta.size}` : ''}
              </span>
            </div>
          </div>
        </div>
      )}

      <div style={{ marginTop: '20px' }}>
        <button
          type="button"
          className="btn btn-primary"
          onClick={onAnalyze}
          disabled={!selectedFile || isAnalyzing}
        >
          {isAnalyzing ? (
            <>
              <span className="loading-spinner" />
              <span>Analyzing leaf...</span>
            </>
          ) : (
            <>
              <Sparkles size={18} />
              <span>Analyze Leaf</span>
            </>
          )}
        </button>
      </div>

      {onSelectSample && (
        <div className="sample-presets">
          <p className="sample-presets-title">Quick Test Samples</p>
          <div className="sample-buttons-grid">
            <button
              type="button"
              className="sample-btn"
              onClick={() => onSelectSample('Bacterialblight')}
              disabled={isAnalyzing}
            >
              Bacterial Blight Sample
            </button>
            <button
              type="button"
              className="sample-btn"
              onClick={() => onSelectSample('Blast')}
              disabled={isAnalyzing}
            >
              Rice Blast Sample
            </button>
            <button
              type="button"
              className="sample-btn"
              onClick={() => onSelectSample('Brownspot')}
              disabled={isAnalyzing}
            >
              Brown Spot Sample
            </button>
            <button
              type="button"
              className="sample-btn"
              onClick={() => onSelectSample('Tungro')}
              disabled={isAnalyzing}
            >
              Rice Tungro Sample
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
