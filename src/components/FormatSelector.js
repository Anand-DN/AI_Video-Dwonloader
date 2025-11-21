import React from "react";

export default function FormatSelector({ selected, onSelect }) {
    const videoOptions = ["8k", "4k", "2k", "1080p", "720p"];
    const audioOptions = ["mp3", "webm", "aac"];

    return (
        <div className="format-box">
            <div className="section">
                <div className="label">Video</div>
                <div className="chips">
                    {videoOptions.map(opt => (
                        <button key={opt} className={`chip ${selected === opt ? "active" : ""}`} onClick={() => onSelect(opt)}>{opt}</button>
                    ))}
                </div>
            </div>

            <div className="section">
                <div className="label">Audio Only</div>
                <div className="chips">
                    {audioOptions.map(opt => (
                        <button key={opt} className={`chip ${selected === opt ? "active" : ""}`} onClick={() => onSelect(opt)}>{opt}</button>
                    ))}
                </div>
            </div>
        </div>
    );
}
