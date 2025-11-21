import React from "react";
import { useTheme } from "../context/ThemeContext";

export default function Header({ onSettingsClick }) {
  const { theme, toggle } = useTheme();

  return (
    <header className="header">
      <div className="header-content">
        <div className="logo-section">
          <div className="logo">⚛️</div>
          <h1 className="app-title">Video Downloader</h1>
        </div>

        <div className="header-actions">
          <button
            onClick={toggle}
            className="btn btn-icon"
            title={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
          >
            {theme === "dark" ? "☀️" : "🌙"}
          </button>
          <button
            onClick={onSettingsClick}
            className="btn btn-icon"
            title="Settings"
          >
            ⚙️
          </button>
        </div>
      </div>
    </header>
  );
}
