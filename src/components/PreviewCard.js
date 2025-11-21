import React from "react";

export default function PreviewCard({ thumb, title, onFetch, url }) {
  return (
    <div className="preview-card">
      <div className="preview-left">
        <div className="thumb-wrap">
          <img src={thumb} alt="thumb" className="thumb-img" />
        </div>
      </div>

      <div className="preview-right">
        <div className="preview-title">{title || "Preview"}</div>
        <div className="preview-url">{url || "Enter a video URL and click Fetch"}</div>
        <div style={{marginTop:12}}>
          <button className="primary" onClick={onFetch}>Fetch Preview</button>
        </div>
      </div>
    </div>
  );
}
