import React from "react";
import "./Toast.css"; // uses your existing toast styles

export default function ToastDownloadSuccess({ filename, fileUrl, folderPath, onClose }) {
    return (
        <div className="toast-box toast-success">
            <div className="toast-title">Download Completed</div>
            <div className="toast-sub">{filename}</div>

            <div className="toast-actions">
                <a className="toast-btn primary" href={fileUrl} target="_blank" rel="noreferrer">
                    Open Video
                </a>
                <button className="toast-btn secondary" onClick={() => {
                    navigator.clipboard.writeText(folderPath);
                    onClose();
                }}>
                    Show in Folder
                </button>
            </div>
        </div>
    );
}
