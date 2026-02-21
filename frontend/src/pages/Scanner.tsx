import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type {
  IdentifiedInteraction,
  ContextWipeTestResult,
  TargetConfig,
  PresetCategory,
  PresetTestResult,
} from "../api/client";
import {
  scanIdentify,
  scanFull,
  scanTestWipe,
  saveTarget,
  getPresetCategories,
  runPresetTests,
} from "../api/client";

export function Scanner() {
  const [urlInput, setUrlInput] = useState("");
  const [seedsInput, setSeedsInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [identified, setIdentified] = useState<IdentifiedInteraction[]>([]);
  const [wipeResults, setWipeResults] = useState<ContextWipeTestResult[]>([]);
  const [savedIds, setSavedIds] = useState<Set<string>>(new Set());
  const [presetCategories, setPresetCategories] = useState<PresetCategory[]>([]);
  const [presetResults, setPresetResults] = useState<PresetTestResult[]>([]);
  const [presetCategoryFilter, setPresetCategoryFilter] = useState<Set<string>>(new Set());
  const [presetTarget, setPresetTarget] = useState<IdentifiedInteraction | null>(null);

  useEffect(() => {
    getPresetCategories()
      .then(setPresetCategories)
      .catch(() => {});
  }, []);

  const parseSeeds = (text: string) =>
    text
      .split(/\n/)
      .map((s) => s.trim())
      .filter(Boolean);

  const handleIdentify = async () => {
    const url = urlInput.trim();
    if (!url) {
      setError("Enter a URL");
      return;
    }
    setError(null);
    setLoading(true);
    setIdentified([]);
    setWipeResults([]);
    try {
      const list = await scanIdentify(url);
      setIdentified(list);
      if (list.length === 0) setError("No widgets identified on this URL.");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Identify failed");
    } finally {
      setLoading(false);
    }
  };

  const handleTestWipe = async (item: IdentifiedInteraction) => {
    setError(null);
    setLoading(true);
    try {
      const result = await scanTestWipe(item);
      setWipeResults((prev) => [result, ...prev]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Test wipe failed");
    } finally {
      setLoading(false);
    }
  };

  const handleFullScan = async () => {
    const seeds = parseSeeds(seedsInput);
    if (seeds.length === 0) {
      setError("Enter at least one seed URL (one per line).");
      return;
    }
    setError(null);
    setLoading(true);
    setIdentified([]);
    setWipeResults([]);
    try {
      const { results } = await scanFull(seeds);
      setWipeResults(results);
      if (results.length === 0) setError("Full scan found no widgets.");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Full scan failed");
    } finally {
      setLoading(false);
    }
  };

  const handleSaveTarget = async (config: TargetConfig) => {
    setError(null);
    setLoading(true);
    try {
      await saveTarget(config);
      setSavedIds((prev) => new Set(prev).add(config.name));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Save target failed");
    } finally {
      setLoading(false);
    }
  };

  const handleRunPresetTests = async (item: IdentifiedInteraction) => {
    setPresetTarget(item);
    setError(null);
    setLoading(true);
    setPresetResults([]);
    try {
      const categoryIds = presetCategoryFilter.size > 0 ? Array.from(presetCategoryFilter) : undefined;
      const { results } = await runPresetTests(item, categoryIds);
      setPresetResults(results);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Preset tests failed");
    } finally {
      setLoading(false);
    }
  };

  const togglePresetCategory = (id: string) => {
    setPresetCategoryFilter((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  return (
    <div className="scanner-page">
      <h1>Scanner</h1>
      <p className="subtitle">
        Discover AI chat widgets and test context override; save results as targets in the DB.
      </p>
      <nav>
        <Link to="/">Dashboard</Link>
        <Link to="/chat">Chat</Link>
      </nav>

      {error && <p className="error">{error}</p>}
      {loading && <p className="loading">Running scan…</p>}

      <section className="scan-inputs">
        <h2>Identify (single URL)</h2>
        <div className="input-row">
          <input
            type="url"
            placeholder="https://example.com"
            value={urlInput}
            onChange={(e) => setUrlInput(e.target.value)}
            className="url-input"
          />
          <button type="button" onClick={handleIdentify} disabled={loading}>
            Identify
          </button>
        </div>

        <h2>Full scan (seeds → scrape → identify → test wipe)</h2>
        <textarea
          placeholder={"One seed URL per line\nhttps://example.com\nhttps://example.org"}
          value={seedsInput}
          onChange={(e) => setSeedsInput(e.target.value)}
          rows={4}
          className="seeds-input"
        />
        <div className="input-row">
          <button type="button" onClick={handleFullScan} disabled={loading}>
            Run full scan
          </button>
        </div>
      </section>

      {identified.length > 0 && (
        <section className="scan-results identified">
          <h2>Identified widgets</h2>
          <ul>
            {identified.map((item, i) => (
              <li key={`${item.url}-${item.widget_type}-${i}`}>
                <span className="widget-type">{item.widget_type}</span>
                <span className="url">{item.url}</span>
                <span className="confidence">{(item.confidence * 100).toFixed(0)}%</span>
                <button
                  type="button"
                  onClick={() => handleTestWipe(item)}
                  disabled={loading}
                >
                  Test context wipe
                </button>
                <button
                  type="button"
                  onClick={() => handleRunPresetTests(item)}
                  disabled={loading}
                  className="preset-tests-btn"
                >
                  Run preset tests
                </button>
              </li>
            ))}
          </ul>
        </section>
      )}

      {presetCategories.length > 0 && identified.length > 0 && (
        <section className="scan-results preset-categories">
          <h2>Preset security test categories</h2>
          <p className="subtitle">Select categories to run (or leave all unchecked to run all). Then use &quot;Run preset tests&quot; on a widget above.</p>
          <ul className="preset-category-list">
            {presetCategories.map((c) => (
              <li key={c.id}>
                <label>
                  <input
                    type="checkbox"
                    checked={presetCategoryFilter.has(c.id)}
                    onChange={() => togglePresetCategory(c.id)}
                  />
                  <span className="preset-cat-name">{c.name}</span>
                </label>
                <span className="preset-cat-desc">{c.description}</span>
                <span className="preset-cat-count">{c.payload_count} payloads</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {presetResults.length > 0 && (
        <section className="scan-results preset-results">
          <h2>Preset test results</h2>
          {presetTarget && (
            <p className="preset-target">
              Target: {presetTarget.widget_type} @ {presetTarget.url}
            </p>
          )}
          <ul>
            {presetResults.map((r, i) => (
              <li key={`${r.category_id}-${i}`} className={r.error ? "preset-error" : ""}>
                <div className="preset-result-header">
                  <span className="preset-cat">{r.category_name}</span>
                </div>
                <div className="preset-payload">{r.payload}</div>
                {r.error ? (
                  <div className="preset-reply error">{r.error}</div>
                ) : (
                  <div className="preset-reply">{r.reply || "(no reply)"}</div>
                )}
              </li>
            ))}
          </ul>
        </section>
      )}

      {wipeResults.length > 0 && (
        <section className="scan-results wipe-results">
          <h2>Context wipe test results</h2>
          <ul>
            {wipeResults.map((res, i) => (
              <li key={`${res.identified.url}-${i}`} className={res.success ? "success" : "failed"}>
                <div className="result-header">
                  <span className="widget-type">{res.identified.widget_type}</span>
                  <span className="url">{res.identified.url}</span>
                  <span className="strategy">{res.strategy_used}</span>
                  <span className="success-badge">{res.success ? "Success" : "Failed"}</span>
                </div>
                <div className="result-actions">
                  <button
                    type="button"
                    onClick={() => handleSaveTarget(res.target_config)}
                    disabled={loading || savedIds.has(res.target_config.name)}
                  >
                    {savedIds.has(res.target_config.name) ? "Saved" : "Save as target"}
                  </button>
                </div>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
