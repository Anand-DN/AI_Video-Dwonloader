import React, { useState } from "react";
import { useDownload } from "../context/DownloadContext";

export default function SettingsPanel({ onClose }) {
  const { state, dispatch } = useDownload();
  const [max, setMax] = useState(state.settings.maxConcurrent || 2);
  const [def, setDef] = useState(state.settings.defaultMode || "video");

  const save = () => {
    dispatch({
      type: "SET_SETTINGS",
      settings: { maxConcurrent: Number(max), defaultMode: def },
    });
    onClose();
  };

  return (
    <div className="settings-panel">
      <div style={{ marginBottom: "2rem" }}>
        <h2
          style={{
            fontSize: "1.75rem",
            marginBottom: "0.5rem",
            background: "var(--accent-gradient)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
          }}
        >
          ⚙️ Settings
        </h2>
        <p style={{ color: "var(--text-tertiary)", fontSize: "0.95rem" }}>
          Configure your download preferences
        </p>
      </div>

      <div className="input-group">
        <label className="input-label">Maximum Concurrent Downloads</label>
        <input
          type="number"
          min="1"
          max="5"
          value={max}
          onChange={(e) => setMax(e.target.value)}
          className="input"
        />
        <p
          style={{
            fontSize: "0.85rem",
            color: "var(--text-tertiary)",
            marginTop: "6px",
          }}
        >
          Recommended: 2-3 for optimal performance
        </p>
      </div>

      <div className="input-group">
        <label className="input-label">Default Download Mode</label>
        <select
          value={def}
          onChange={(e) => setDef(e.target.value)}
          className="select"
        >
          <option value="video">🎥 Video</option>
          <option value="audio">🎵 Audio Only</option>
        </select>
      </div>

      <div style={{ display: "flex", gap: "12px", marginTop: "2rem" }}>
        <button onClick={save} className="btn btn-primary" style={{ flex: 1 }}>
          💾 Save Changes
        </button>
        <button onClick={onClose} className="btn btn-secondary">
          ✕ Cancel
        </button>
      </div>
    </div>
  );
}
