import React, { useState, useEffect, useCallback, useRef } from 'react';
import Header from './components/Header';
import BenchmarkBanner from './components/BenchmarkBanner';
import ImageUploader from './components/ImageUploader';
import ResultCard from './components/ResultCard';
import AttentionHeatmap from './components/AttentionHeatmap';
import TestGallery from './components/TestGallery';
import Footer from './components/Footer';
import { API_BASE_URL } from './config';

export default function App() {
  const [backendStatus, setBackendStatus] = useState({
    status: 'checking',
    model_loaded: false,
    device: 'cpu',
  });
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [imageMeta, setImageMeta] = useState({ width: 0, height: 0, size: '' });
  const [imageSource, setImageSource] = useState(null);
  const [groundTruth, setGroundTruth] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [diagnosticResult, setDiagnosticResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');
  const [loadedClasses, setLoadedClasses] = useState([]);

  // Ref to hold current file to avoid race condition in async inference
  const activeFileRef = useRef(null);

  // Health poll
  useEffect(() => {
    let mounted = true;
    const check = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/health`);
        if (res.ok) {
          const data = await res.json();
          if (mounted) setBackendStatus(data);
        } else {
          if (mounted) setBackendStatus({ status: 'error', model_loaded: false, device: 'unknown' });
        }
      } catch {
        if (mounted) setBackendStatus({ status: 'offline', model_loaded: false, device: 'unknown' });
      }
    };
    check();
    const id = setInterval(check, 15000);
    return () => {
      mounted = false;
      clearInterval(id);
    };
  }, []);

  const formatSize = (bytes) => {
    if (!bytes) return '';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  const runAnalysis = async (fileToAnalyze) => {
    const file = fileToAnalyze || activeFileRef.current || selectedFile;
    if (!file) return;

    setIsAnalyzing(true);
    setErrorMessage('');
    try {
      const fd = new FormData();
      fd.append('file', file);

      const res = await fetch(`${API_BASE_URL}/api/explain`, {
        method: 'POST',
        body: fd,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail || 'Inference and explainability failed on server.');
      }

      const data = await res.json();
      setDiagnosticResult(data);
    } catch (err) {
      setErrorMessage(err.message || 'Unable to analyze image. Verify the backend server is running.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleFileSelect = (file, source = 'EXTERNAL IMAGE', gt = null, autoAnalyze = false) => {
    if (!file) return;
    if (!file.type.startsWith('image/')) {
      setErrorMessage('Please upload a valid image file (PNG, JPG, JPEG, WEBP).');
      return;
    }
    setErrorMessage('');
    setSelectedFile(file);
    activeFileRef.current = file;
    setImageSource(source);
    setGroundTruth(gt);
    setDiagnosticResult(null);

    if (previewUrl && previewUrl.startsWith('blob:')) {
      URL.revokeObjectURL(previewUrl);
    }
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);

    const img = new Image();
    img.onload = () => {
      setImageMeta({
        width: img.naturalWidth,
        height: img.naturalHeight,
        size: formatSize(file.size),
      });
    };
    img.src = url;

    if (autoAnalyze) {
      runAnalysis(file);
    }
  };

  const handleClear = () => {
    if (previewUrl && previewUrl.startsWith('blob:')) {
      URL.revokeObjectURL(previewUrl);
    }
    setSelectedFile(null);
    activeFileRef.current = null;
    setPreviewUrl(null);
    setImageMeta({ width: 0, height: 0, size: '' });
    setImageSource(null);
    setGroundTruth(null);
    setDiagnosticResult(null);
    setErrorMessage('');
  };

  const handleAnalyze = () => {
    runAnalysis(selectedFile);
  };

  // Next sample workflow for live demonstrations
  const handleNextSample = useCallback(async () => {
    if (loadedClasses.length === 0 || !selectedFile) return;

    // Find all samples for the current groundTruth class (or all if unspecified)
    let candidateList = [];
    if (groundTruth) {
      const clsObj = loadedClasses.find((c) => c.name === groundTruth);
      if (clsObj && clsObj.samples) {
        candidateList = clsObj.samples.map((fname) => ({
          className: clsObj.name,
          filename: fname,
        }));
      }
    }

    if (candidateList.length === 0) {
      loadedClasses.forEach((clsObj) => {
        (clsObj.samples || []).forEach((fname) => {
          candidateList.push({ className: clsObj.name, filename: fname });
        });
      });
    }

    if (candidateList.length === 0) return;

    // Find current index
    const currIdx = candidateList.findIndex((item) => item.filename === selectedFile.name);
    const nextIdx = (currIdx + 1) % candidateList.length;
    const nextItem = candidateList[nextIdx];

    try {
      const res = await fetch(`${API_BASE_URL}/api/samples/${nextItem.className}/${nextItem.filename}`);
      if (!res.ok) throw new Error('Could not fetch next sample');
      const blob = await res.blob();
      const ext = nextItem.filename.toLowerCase().endsWith('.png') ? 'image/png' : 'image/jpeg';
      const file = new File([blob], nextItem.filename, { type: ext });

      handleFileSelect(file, 'VERIFIED TEST SAMPLE', nextItem.className, true);

      const labEl = document.getElementById('image-lab');
      if (labEl) {
        labEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    } catch (err) {
      console.error('Failed to load next sample:', err);
    }
  }, [loadedClasses, selectedFile, groundTruth]);

  return (
    <div className="lv-shell">
      <Header backendStatus={backendStatus} />

      <main className="lv-main">
        {/* Hero */}
        <section className="lv-hero" aria-labelledby="hero-title">
          <p className="lv-hero__kicker">VISION TRANSFORMER + GRU · BIO-COMPUTING LAB</p>
          <h1 className="lv-hero__h1" id="hero-title">
            See what the model <em>sees.</em>
          </h1>
          <p className="lv-hero__p">
            Upload a rice leaf image to identify its disease across four categories,
            inspect calibrated prediction confidence, and visualize the exact image regions
            receiving stronger ViT self-attention rollout.
          </p>
        </section>

        {/* Model Performance Strip */}
        <BenchmarkBanner />

        {/* Two-Column Core Workspace */}
        <div className="lv-workspace">
          {/* Left: Image Lab */}
          <div>
            <ImageUploader
              selectedFile={selectedFile}
              previewUrl={previewUrl}
              imageMeta={imageMeta}
              imageSource={imageSource}
              groundTruth={groundTruth}
              onFileSelect={handleFileSelect}
              onClear={handleClear}
              onAnalyze={handleAnalyze}
              isAnalyzing={isAnalyzing}
            />

            {errorMessage && (
              <div className="lv-error" role="alert">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <circle cx="12" cy="12" r="10" />
                  <line x1="12" y1="8" x2="12" y2="12" />
                  <line x1="12" y1="16" x2="12.01" y2="16" />
                </svg>
                <span><strong>Error: </strong>{errorMessage}</span>
              </div>
            )}
          </div>

          {/* Right: Diagnosis Panel */}
          <div>
            <ResultCard
              result={diagnosticResult}
              imageSource={imageSource}
              groundTruth={groundTruth}
              onReset={handleClear}
              isAnalyzing={isAnalyzing}
              onNextSample={handleNextSample}
            />
          </div>
        </div>

        {/* Attention Visualization Section */}
        {diagnosticResult?.heatmap_base64 && (
          <AttentionHeatmap
            originalUrl={previewUrl}
            heatmapBase64={diagnosticResult.heatmap_base64}
            pureHeatmapBase64={diagnosticResult.pure_heatmap_base64}
            description={diagnosticResult.description}
          />
        )}

        {/* Verified Test Sample Gallery Console */}
        <TestGallery
          onSelectSample={handleFileSelect}
          selectedFilename={selectedFile?.name}
          isAnalyzing={isAnalyzing}
          onSamplesLoaded={setLoadedClasses}
        />
      </main>

      <Footer />
    </div>
  );
}
