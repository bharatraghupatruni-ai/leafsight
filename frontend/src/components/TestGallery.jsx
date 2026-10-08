import React, { useState, useEffect } from 'react';
import { API_BASE_URL, DISEASE_INFO } from '../config';

const TABS = [
  { id: 'ALL', label: 'All Samples' },
  { id: 'Bacterialblight', label: 'Bacterial Blight' },
  { id: 'Blast', label: 'Rice Blast' },
  { id: 'Brownspot', label: 'Brown Spot' },
  { id: 'Tungro', label: 'Tungro' },
];

export default function TestGallery({
  onSelectSample,
  selectedFilename,
  isAnalyzing,
}) {
  const [classesData, setClassesData] = useState([]);
  const [activeTab, setActiveTab] = useState('ALL');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [loadingSample, setLoadingSample] = useState(null);

  useEffect(() => {
    let mounted = true;
    const fetchSamples = async () => {
      try {
        setLoading(true);
        const res = await fetch(`${API_BASE_URL}/api/samples`);
        if (!res.ok) throw new Error('Failed to retrieve test samples from server.');
        const data = await res.json();
        if (mounted) {
          setClassesData(data.classes || []);
          setError(null);
        }
      } catch (err) {
        if (mounted) setError(err.message || 'Could not connect to sample service.');
      } finally {
        if (mounted) setLoading(false);
      }
    };
    fetchSamples();
    return () => { mounted = false; };
  }, []);

  // Compute flattened list of items based on activeTab
  const getDisplayItems = () => {
    const items = [];
    classesData.forEach((clsObj) => {
      if (activeTab === 'ALL' || activeTab === clsObj.name) {
        clsObj.samples.forEach((filename) => {
          items.push({
            className: clsObj.name,
            displayName: DISEASE_INFO[clsObj.name]?.displayName || clsObj.name,
            filename,
            url: `${API_BASE_URL}/api/samples/${clsObj.name}/${filename}`,
          });
        });
      }
    });
    return items;
  };

  const handleChooseSample = async (item) => {
    if (isAnalyzing || loadingSample) return;
    try {
      setLoadingSample(item.filename);
      const res = await fetch(item.url);
      if (!res.ok) throw new Error(`Could not load test sample ${item.filename}`);
      const blob = await res.blob();
      const ext = item.filename.toLowerCase().endsWith('.png') ? 'image/png' : 'image/jpeg';
      const file = new File([blob], item.filename, { type: ext });

      onSelectSample(file, 'VERIFIED TEST SAMPLE', item.className);

      // Smooth scroll to Image Lab
      const labEl = document.getElementById('image-lab');
      if (labEl) {
        labEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    } catch (err) {
      console.error('Error loading sample:', err);
    } finally {
      setLoadingSample(null);
    }
  };

  const handleRandomSample = () => {
    const items = getDisplayItems();
    if (items.length === 0) return;
    const randomItem = items[Math.floor(Math.random() * items.length)];
    handleChooseSample(randomItem);
  };

  const displayItems = getDisplayItems();
  const totalCount = classesData.reduce((acc, c) => acc + (c.samples?.length || 0), 0);

  return (
    <section className="lv-gallery" id="test-gallery" aria-label="Verified test samples gallery">
      <div className="lv-gallery__head">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 12 }}>
          <div>
            <h2 className="lv-gallery__title">VERIFIED TEST SAMPLES</h2>
            <p className="lv-gallery__sub">
              Representative held-out evaluation samples from local dataset (data/processed/test/). Select any sample to run live inference.
            </p>
          </div>
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
        </div>

        {/* Tab Filters */}
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
      </div>

      <div className="lv-gallery__body">
        {loading ? (
          <div className="lv-gallery__loading">Loading verified samples from dataset…</div>
        ) : error ? (
          <div className="lv-error" role="alert">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            <span>{error}</span>
          </div>
        ) : (
          <div className="lv-gallery__grid" role="list" aria-label="Verified test samples list">
            {displayItems.map((item) => {
              const isSelected = selectedFilename === item.filename;
              const isCurrentLoading = loadingSample === item.filename;
              return (
                <div
                  key={`${item.className}-${item.filename}`}
                  className={`lv-thumb ${isSelected ? 'selected' : ''}`}
                  role="button"
                  tabIndex={0}
                  aria-label={`Select ${item.displayName} sample ${item.filename}`}
                  onClick={() => handleChooseSample(item)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      handleChooseSample(item);
                    }
                  }}
                >
                  <div className="lv-thumb__img-wrap">
                    <img
                      className="lv-thumb__img"
                      src={item.url}
                      alt={`${item.displayName} test sample`}
                      loading="lazy"
                    />
                  </div>
                  <div className="lv-thumb__meta">
                    <span className="lv-thumb__cls">{item.displayName}</span>
                    <span className="lv-thumb__tag">
                      {isCurrentLoading ? 'LOADING…' : 'TEST SAMPLE'}
                    </span>
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
