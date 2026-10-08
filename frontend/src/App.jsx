import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import BenchmarkBanner from './components/BenchmarkBanner';
import ImageUploader from './components/ImageUploader';
import ResultCard from './components/ResultCard';
import ProbabilityBars from './components/ProbabilityBars';
import AttentionHeatmap from './components/AttentionHeatmap';
import Footer from './components/Footer';
import { API_BASE_URL } from './config';
import { AlertCircle, FileSearch, ShieldCheck } from 'lucide-react';
import './styles/App.css';

export default function App() {
  const [backendStatus, setBackendStatus] = useState({ status: 'checking', model_loaded: false, device: 'cpu' });
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [imageMeta, setImageMeta] = useState({ width: 0, height: 0, size: '' });
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [diagnosticResult, setDiagnosticResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');

  // Check backend health on mount
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/health`);
        if (res.ok) {
          const data = await res.json();
          setBackendStatus(data);
        } else {
          setBackendStatus({ status: 'error', model_loaded: false, device: 'unknown' });
        }
      } catch (err) {
        setBackendStatus({ status: 'offline', model_loaded: false, device: 'unknown' });
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  const handleFileSelect = (file) => {
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      setErrorMessage('Please upload a valid image file (PNG, JPG, JPEG, WEBP).');
      return;
    }

    setErrorMessage('');
    setSelectedFile(file);

    const objectUrl = URL.createObjectURL(file);
    setPreviewUrl(objectUrl);

    // Measure dimensions
    const img = new Image();
    img.onload = () => {
      setImageMeta({
        width: img.naturalWidth,
        height: img.naturalHeight,
        size: formatFileSize(file.size)
      });
    };
    img.src = objectUrl;

    // Reset previous results
    setDiagnosticResult(null);
  };

  const handleClear = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    setImageMeta({ width: 0, height: 0, size: '' });
    setDiagnosticResult(null);
    setErrorMessage('');
  };

  const handleSelectSample = async (sampleKey) => {
    try {
      setErrorMessage('');
      const sampleUrl = `/samples/${sampleKey}.jpg`;
      const response = await fetch(sampleUrl);
      if (!response.ok) throw new Error('Sample image not found');
      const blob = await response.blob();
      const file = new File([blob], `${sampleKey}_sample.jpg`, { type: 'image/jpeg' });
      handleFileSelect(file);
    } catch (err) {
      setErrorMessage(`Failed to load sample image for ${sampleKey}. You can upload an image directly.`);
    }
  };

  const handleAnalyze = async () => {
    if (!selectedFile) return;

    setIsAnalyzing(true);
    setErrorMessage('');

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      // Call explain endpoint which provides prediction + attention rollout visualization
      const response = await fetch(`${API_BASE_URL}/api/explain`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail || 'Analysis request failed on the server.');
      }

      const data = await response.json();
      setDiagnosticResult(data);
    } catch (err) {
      setErrorMessage(
        err.message || 'Unable to analyze image. Please ensure the backend server is running and try again.'
      );
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="app-container">
      <Header backendStatus={backendStatus} />

      <main className="main-content">
        <BenchmarkBanner />

        <div className="dashboard-grid">
          {/* Left Column: Image Input & Settings */}
          <div>
            <ImageUploader
              selectedFile={selectedFile}
              previewUrl={previewUrl}
              imageMeta={imageMeta}
              onFileSelect={handleFileSelect}
              onClear={handleClear}
              onAnalyze={handleAnalyze}
              isAnalyzing={isAnalyzing}
              onSelectSample={handleSelectSample}
            />

            {errorMessage && (
              <div className="error-banner">
                <AlertCircle size={18} style={{ flexShrink: 0, marginTop: 2 }} />
                <div>
                  <strong>Analysis Error:</strong> {errorMessage}
                </div>
              </div>
            )}
          </div>

          {/* Right Column: Diagnostic & Explainability Results */}
          <div>
            {diagnosticResult ? (
              <>
                <ResultCard result={diagnosticResult} onReset={handleClear} />
                <ProbabilityBars
                  probabilities={diagnosticResult.probabilities}
                  predictedClass={diagnosticResult.prediction}
                />
                <AttentionHeatmap
                  originalUrl={previewUrl}
                  heatmapBase64={diagnosticResult.heatmap_base64}
                  description={diagnosticResult.description}
                />
              </>
            ) : (
              <div className="card" style={{ textAlign: 'center', padding: '48px 24px' }}>
                <div
                  style={{
                    width: 56,
                    height: 56,
                    borderRadius: '50%',
                    background: 'var(--bg-surface-subtle)',
                    color: 'var(--text-muted)',
                    display: 'inline-flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    marginBottom: 16
                  }}
                >
                  <FileSearch size={28} />
                </div>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: 8 }}>
                  Ready for Disease Analysis
                </h3>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', maxWidth: 420, margin: '0 auto' }}>
                  Upload a rice leaf image or choose one of the test samples to view real-time disease classification,
                  calibrated class probabilities, and ViT attention rollout visualization.
                </p>
              </div>
            )}
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
