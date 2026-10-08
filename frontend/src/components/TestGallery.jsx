import React, { useState, useEffect, useRef } from 'react';
import { API_BASE_URL, DISEASE_INFO } from '../config';

const TABS = [
  { id: 'ALL', label: 'All Samples' },
  { id: 'Bacterialblight', label: 'Bacterial Blight' },
  { id: 'Blast', label: 'Rice Blast' },
  { id: 'Brownspot', label: 'Brown Spot' },
  { id: 'Tungro', label: 'Tungro' },
];

/**
 * Robust image fetcher with 4 fallback tiers:
 * 1. Same-origin relative path (via Vite dev proxy or production reverse proxy)
 * 2. Full configured url
 * 3. Direct 127.0.0.1 backend address
 * 4. In-memory Image -> Canvas blob extraction
 */
async function fetchSampleBlob(item) {
  const candidates = [
    `/api/samples/${item.className}/${item.filename}`,
    item.url,
    `http://127.0.0.1:8000/api/samples/${item.className}/${item.filename}`,
    `http://localhost:8000/api/samples/${item.className}/${item.filename}`,
  ];

  let lastErr = null;
  for (const targetUrl of candidates) {
    if (!targetUrl) continue;
    try {
      const res = await fetch(targetUrl);
      if (res.ok) {
        const blob = await res.blob();
        const ext = item.filename.toLowerCase().endsWith('.png') ? 'image/png' : 'image/jpeg';
        return new File([blob], item.filename, { type: ext });
      }
    } catch (err) {
      lastErr = err;
    }
  }

  // Fallback 4: Canvas blob conversion
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.onload = () => {
      try {
        const canvas = document.createElement('canvas');
        canvas.width = img.naturalWidth || 224;
        canvas.height = img.naturalHeight || 224;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0);
        const mime = item.filename.toLowerCase().endsWith('.png') ? 'image/png' : 'image/jpeg';
        canvas.toBlob((blob) => {
          if (blob) {
            resolve(new File([blob], item.filename, { type: mime }));
          } else {
            reject(lastErr || new Error('Failed to generate canvas blob'));
          }
        }, mime, 0.95);
      } catch (canvasErr) {
        reject(lastErr || canvasErr);
      }
    };
    img.onerror = () => reject(lastErr || new Error(`Could not load image: ${item.filename}`));
    img.src = item.url;
  });
}

export default function TestGallery({
  onSelectSample,
  selectedFilename,
  isAnalyzing,
  onSamplesLoaded,
}) {
  const [classesData, setClassesData] = useState([]);
  const [activeTab, setActiveTab] = useState('ALL');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionError, setActionError] = useState(null);
  const [loadingSample, setLoadingSample] = useState(null);
  const scrollContainerRef = useRef(null);

  useEffect(() => {
    let mounted = true;
    const fetchSamples = async () => {
      try {
        setLoading(true);
        // Try relative endpoint first, then configured base URL
        let res;
        try {
          res = await fetch('/api/samples');
        } catch {
          res = await fetch(`${API_BASE_URL || 'http://127.0.0.1:8000'}/api/samples`);
        }
        if (!res.ok) throw new Error('Failed to retrieve test samples from server.');
        const data = await res.json();
        if (mounted) {
          const list = data.classes || [];
          setClassesData(list);
          setError(null);
          if (onSamplesLoaded) {
            onSamplesLoaded(list);
          }
        }
      } catch (err) {
        if (mounted) setError(err.message || 'Could not connect to sample service.');
      } finally {
        if (mounted) setLoading(false);
      }
    };
    fetchSamples();
    return () => { mounted = false; };
  }, [onSamplesLoaded]);

  // Compute flattened list of items based on activeTab
  const getDisplayItems = () => {
    const items = [];
    classesData.forEach((clsObj) => {
      if (activeTab === 'ALL' || activeTab === clsObj.name) {
        (clsObj.samples || []).forEach((filename) => {
          items.push({
            className: clsObj.name,
            displayName: DISEASE_INFO[clsObj.name]?.displayName || clsObj.name,
            filename,
            url: `/api/samples/${clsObj.name}/${filename}`,
          });
        });
      }
    });
    return items;
  };

  const handleScroll = (offset) => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollBy({ left: offset, behavior: 'smooth' });
    }
  };

  const handleChooseSample = async (item, autoAnalyze = false) => {
    if (isAnalyzing || loadingSample) return;
    setActionError(null);
    try {
      setLoadingSample(item.filename);
      const file = await fetchSampleBlob(item);

      onSelectSample(file, 'VERIFIED TEST SAMPLE', item.className, autoAnalyze);

      // Smooth scroll to Image Lab
      const labEl = document.getElementById('image-lab');
      if (labEl) {
        labEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    } catch (err) {
      console.error('Error loading sample:', err);
      setActionError(`Could not load sample "${item.filename}": ${err.message}`);
    } finally {
      setLoadingSample(null);
    }
  };

  const handleRandomSample = () => {
    const items = getDisplayItems();
    if (items.length === 0) return;
    const randomItem = items[Math.floor(Math.random() * items.length)];
    handleChooseSample(randomItem, false);
  };

  const displayItems = getDisplayItems();
  const totalCount = classesData.reduce((acc, c) => acc + (c.samples?.length || 0), 0);

  return (
    <section className="lv-gallery" id="test-gallery" aria-label="Verified test samples console">
      <div className="lv-gallery__head">
        <div className="lv-gallery__eyebrow">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
          </svg>
          VERIFIED TEST CONSOLE
        </div>
        <h2 className="lv-gallery__title">VERIFIED HELD-OUT TEST SAMPLES</h2>
        <p className="lv-gallery__sub">
          Directly sourced from local test dataset (<code>data/processed/test/</code>). Each image has an authenticated ground-truth disease class. Select or run real-time inference on any test specimen.
        </p>

        {/* Controls row: Tabs on left, Navigation & Random on right */}
        <div className="lv-gallery__controls-row">
          <div className="lv-gallery__tabs" role="tablist" aria-label="Sample disease filters">
            {TABS.map((tab) => {
              const count = tab.id === 'ALL'
                ? totalCount
                : (classesData.find((c) => c.name === tab.id)?.samples?.length || 0);
              return (
                <button
                  key={tab.id}
                  type="button"
                  role="tab"
                  aria-selected={activeTab === tab.id}
                  className={`lv-gallery__tab ${activeTab === tab.id ? 'active' : ''}`}
                  onClick={() => setActiveTab(tab.id)}
                >
                  {tab.label} {count > 0 ? `(${count})` : ''}
                </button>
              );
            })}
          </div>

          <div className="lv-gallery__nav-actions">
            <button
              type="button"
              className="btn btn-ghost btn-sm"
              onClick={handleRandomSample}
              disabled={isAnalyzing || loading || displayItems.length === 0}
              title="Pick a random sample from current filter"
              aria-label="Pick random verified sample"
            >
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <polyline points="16 3 21 3 21 8" />
                <line x1="4" y1="20" x2="21" y2="3" />
                <polyline points="21 16 21 21 16 21" />
                <line x1="15" y1="15" x2="21" y2="21" />
                <line x1="4" y1="4" x2="9" y2="9" />
              </svg>
              <span>Random Sample</span>
            </button>

            <button
              type="button"
              className="lv-gallery__arrow-btn"
              onClick={() => handleScroll(-460)}
              disabled={loading || displayItems.length === 0}
              aria-label="Scroll left in sample gallery"
              title="Scroll left"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <polyline points="15 18 9 12 15 6" />
              </svg>
            </button>

            <button
              type="button"
              className="lv-gallery__arrow-btn"
              onClick={() => handleScroll(460)}
              disabled={loading || displayItems.length === 0}
              aria-label="Scroll right in sample gallery"
              title="Scroll right"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <polyline points="9 18 15 12 9 6" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      <div className="lv-gallery__body">
        {actionError && (
          <div className="lv-error" style={{ margin: '14px 28px' }} role="alert">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            <span>{actionError}</span>
          </div>
        )}

        {loading ? (
          <div className="lv-gallery__loading">Loading verified samples from dataset…</div>
        ) : error ? (
          <div className="lv-error" style={{ margin: 20 }} role="alert">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            <span>{error}</span>
          </div>
        ) : (
          <div
            ref={scrollContainerRef}
            className="lv-gallery__track"
            role="list"
            aria-label="Verified test samples interactive carousel"
          >
            {displayItems.map((item) => {
              const isSelected = selectedFilename === item.filename;
              const isCurrentLoading = loadingSample === item.filename;
              return (
                <div
                  key={`${item.className}-${item.filename}`}
                  className={`lv-sample-card ${isSelected ? 'is-selected' : ''}`}
                  role="button"
                  tabIndex={0}
                  aria-label={`Sample ${item.displayName} file ${item.filename}`}
                  onClick={() => handleChooseSample(item, false)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      handleChooseSample(item, false);
                    }
                  }}
                >
                  <div className="lv-sample-card__img-box">
                    <img
                      className="lv-sample-card__img"
                      src={item.url}
                      alt={`${item.displayName} test sample`}
                      loading="lazy"
                    />
                    <span className="lv-sample-card__badge-top">TEST SAMPLE</span>
                    {isSelected && (
                      <span className="lv-sample-card__selected-pill">
                        <svg width="8" height="8" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                          <circle cx="12" cy="12" r="10" />
                        </svg>
                        SELECTED
                      </span>
                    )}
                  </div>

                  <div className="lv-sample-card__content">
                    <div className="lv-sample-card__title-row">
                      <span className="lv-sample-card__name">{item.displayName}</span>
                      <span className="lv-sample-card__gt">
                        GT: <strong>{item.className}</strong>
                      </span>
                      <span className="lv-sample-card__filename">{item.filename}</span>
                    </div>

                    <div className="lv-sample-card__actions" onClick={(e) => e.stopPropagation()}>
                      <button
                        type="button"
                        className="lv-card-btn lv-card-btn--use"
                        onClick={() => handleChooseSample(item, false)}
                        disabled={isAnalyzing || isCurrentLoading}
                        title="Load this sample into Image Lab"
                        aria-label={`Use ${item.displayName} sample`}
                      >
                        {isCurrentLoading ? 'Loading…' : 'Use Sample'}
                      </button>

                      <button
                        type="button"
                        className="lv-card-btn lv-card-btn--test"
                        onClick={() => handleChooseSample(item, true)}
                        disabled={isAnalyzing || isCurrentLoading}
                        title="Load and immediately analyze this sample"
                        aria-label={`Use and analyze ${item.displayName} sample`}
                      >
                        <svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                          <polygon points="5 3 19 12 5 21 5 3" />
                        </svg>
                        <span>Analyze</span>
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </section>
  );
}
