import React, { useState } from "react";
import { useDownload } from "../context/DownloadContext";
import "./HistoryPanel.css";

export default function HistoryPanel() {
  const { state, dispatch } = useDownload();
  const [filter, setFilter] = useState("all"); // all, video, torrent, audio

  const handleDelete = (id) => {
    dispatch({ type: "DELETE_HISTORY", id });
  };

  const handleClearAll = () => {
    if (window.confirm("Clear all history? This can't be undone! 🗑️")) {
      dispatch({ type: "CLEAR_HISTORY" });
    }
  };

  const handleOpenFile = async (filepath) => {
    try {
      const response = await fetch('http://localhost:8000/open-file', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: filepath })
      });
      const data = await response.json();
      if (data.error) {
        alert(`Couldn't open file: ${data.error}`);
      }
    } catch (error) {
      console.error('Failed to open file:', error);
      alert('Failed to open file');
    }
  };

  const handleShowInFolder = async (filepath) => {
    try {
      const response = await fetch('http://localhost:8000/show-in-folder', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: filepath })
      });
      const data = await response.json();
      if (data.error) {
        alert(`Couldn't open folder: ${data.error}`);
      }
    } catch (error) {
      console.error('Failed to show in folder:', error);
      alert('Failed to open folder');
    }
  };

  const getFileType = (entry) => {
    if (entry.filepath && entry.filepath.includes('Torrents')) return 'torrent';
    if (entry.mode === 'audio') return 'audio';
    return 'video';
  };

  const filteredHistory = state.history.filter(entry => {
    if (filter === 'all') return true;
    return getFileType(entry) === filter;
  });

  const formatDate = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (seconds < 60) return 'just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    if (days === 1) return 'yesterday';
    if (days < 7) return `${days}d ago`;

    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const getFileIcon = (type) => {
    switch (type) {
      case 'torrent': return '🧲';
      case 'audio': return '🎵';
      default: return '🎬';
    }
  };

  const getFileName = (entry) => {
    if (entry.filename && entry.filename !== 'Fetching metadata...') {
      return entry.filename;
    }
    if (entry.filepath) {
      const parts = entry.filepath.split(/[/\\]/);
      return parts[parts.length - 1];
    }
    return 'Unknown File';
  };

  return (
    <div className="history-panel-modern">
      {/* Header */}
      <div className="history-header-modern">
        <div className="header-title-section">
          <h2 className="history-title-modern">📜 Download History</h2>
          <p className="history-subtitle">Your downloaded vibes, all in one place</p>
        </div>

        {state.history.length > 0 && (
          <button onClick={handleClearAll} className="clear-all-btn-modern">
            <span>🗑️</span>
            Clear All
          </button>
        )}
      </div>

      {/* Filter Chips */}
      <div className="filter-chips-container">
        <button
          className={`filter-chip ${filter === 'all' ? 'active' : ''}`}
          onClick={() => setFilter('all')}
        >
          <span>✨</span> All
          <span className="chip-count">{state.history.length}</span>
        </button>
        <button
          className={`filter-chip ${filter === 'video' ? 'active' : ''}`}
          onClick={() => setFilter('video')}
        >
          <span>🎬</span> Videos
          <span className="chip-count">{state.history.filter(e => getFileType(e) === 'video').length}</span>
        </button>
        <button
          className={`filter-chip ${filter === 'audio' ? 'active' : ''}`}
          onClick={() => setFilter('audio')}
        >
          <span>🎵</span> Audio
          <span className="chip-count">{state.history.filter(e => getFileType(e) === 'audio').length}</span>
        </button>
        <button
          className={`filter-chip ${filter === 'torrent' ? 'active' : ''}`}
          onClick={() => setFilter('torrent')}
        >
          <span>🧲</span> Torrents
          <span className="chip-count">{state.history.filter(e => getFileType(e) === 'torrent').length}</span>
        </button>
      </div>

      {/* History Items */}
      <div className="history-list-modern">
        {filteredHistory.length === 0 ? (
          <div className="empty-state-modern">
            <div className="empty-icon">📭</div>
            <h3>No downloads yet</h3>
            <p>Your download history will appear here</p>
            <div className="empty-decoration">
              <span className="decoration-dot"></span>
              <span className="decoration-dot"></span>
              <span className="decoration-dot"></span>
            </div>
          </div>
        ) : (
          filteredHistory.map((entry) => {
            const fileType = getFileType(entry);
            const fileName = getFileName(entry);

            return (
              <div key={entry.id} className="history-item-modern">
                <div className="history-item-icon">
                  <span className="file-icon">{getFileIcon(fileType)}</span>
                  <div className="icon-glow"></div>
                </div>

                <div className="history-item-content">
                  <div className="history-item-header">
                    <h4 className="history-item-title">{fileName}</h4>
                    <span className="history-item-time">{formatDate(entry.timestamp)}</span>
                  </div>

                  <div className="history-item-meta">
                    <span className="meta-badge success">
                      <span className="badge-dot"></span>
                      Completed
                    </span>
                    <span className="meta-quality">{entry.quality || 'Best'}</span>
                  </div>
                </div>

                <div className="history-item-actions">
                  <button
                    className="action-btn primary-action"
                    onClick={() => handleOpenFile(entry.filepath || entry.filename)}
                    title="Open file"
                  >
                    <span>▶️</span>
                  </button>
                  <button
                    className="action-btn secondary-action"
                    onClick={() => handleShowInFolder(entry.filepath || entry.filename)}
                    title="Show in folder"
                  >
                    <span>📁</span>
                  </button>
                  <button
                    className="action-btn delete-action"
                    onClick={() => handleDelete(entry.id)}
                    title="Remove from history"
                  >
                    <span>❌</span>
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
