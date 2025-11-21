import React, { useEffect, useRef } from "react";
import toast from "react-hot-toast";
import { useDownload } from "../context/DownloadContext";
import { fileUrl, wsUrl } from "../utils/api";

export default function DownloadCard({ item }) {
  const { dispatch } = useDownload();
  const wsRef = useRef(null);

  useEffect(() => {
    // if running, ensure websocket is connected
    if (item.status === "running" && !wsRef.current) {
      const ws = new WebSocket(wsUrl(item.id));
      wsRef.current = ws;
      ws.onmessage = (ev) => {
        const d = JSON.parse(ev.data);
        if (d.status === "downloading") {
          const pct = d.total_bytes ? Math.round((d.downloaded_bytes / d.total_bytes) * 100) : item.progress || 0;
          dispatch({ type: "UPDATE_ITEM", id: item.id, updates: { progress: pct, speed: d.speed, eta: d.eta } });
        } else if (d.status === "finished_file") {
          dispatch({ type: "UPDATE_ITEM", id: item.id, updates: { status: "finished", filename: d.filename, progress: 100 } });
          toast.success(`Finished: ${d.filename}`);
          // push to server history (optional on frontend)
          dispatch({ type: "PUSH_HISTORY", entry: { id: item.id, url: item.url, filename: d.filename, date: new Date().toLocaleString() } });
        } else if (d.status === "finished") {
          // final
          dispatch({ type: "UPDATE_ITEM", id: item.id, updates: { status: "finished" } });
        } else if (d.status === "error") {
          dispatch({ type: "UPDATE_ITEM", id: item.id, updates: { status: "error" } });
          toast.error(`Error: ${d.error || "download failed"}`);
        }
      };
      ws.onopen = () => { };
      ws.onerror = () => {
        toast.error("WebSocket error for download");
      };
    }
    // cleanup when card unmounts
    return () => {
      try { wsRef.current?.close(); } catch { }
    };
    // eslint-disable-next-line
  }, [item.status]);

  const start = async () => {
    // send API request to start
    dispatch({ type: "UPDATE_ITEM", id: item.id, updates: { status: "starting" } });
    try {
      const res = await fetch(`${process.env.REACT_APP_BACKEND || "http://127.0.0.1:8000"}/download`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: item.url, id: item.id, mode: item.mode.startsWith("mp") ? "audio" : "video" })
      });
      const j = await res.json();
      if (j.error) { throw new Error(j.error); }
      dispatch({ type: "UPDATE_ITEM", id: item.id, updates: { status: "running" } });
      toast.success("Download started");
    } catch (e) {
      dispatch({ type: "UPDATE_ITEM", id: item.id, updates: { status: "error" } });
      toast.error("Failed to start download");
    }
  };

  const remove = () => {
    dispatch({ type: "REMOVE_ITEM", id: item.id });
  };

  return (
    <div className="download-card">
      <img className="dc-thumb" src={item.thumb} alt="thumb" />
      <div className="dc-body">
        <div className="dc-row">
          <div className="dc-title">{item.title || item.url}</div>
          <div className="dc-actions">
            {item.status !== "running" && item.status !== "finished" && <button className="mini" onClick={start}>Start</button>}
            <button className="mini danger" onClick={remove}>Remove</button>
          </div>
        </div>

        <div className="dc-progress">
          <div className="dc-progress-bar">
            <div className="dc-progress-fill" style={{ width: `${item.progress || 0}%` }} />
          </div>
          <div className="dc-meta">
            <span>{item.progress || 0}%</span>
            <span className="muted">{item.status}</span>
          </div>
        </div>

        <div className="dc-footer">
          {item.filename ? <a className="file-link" href={fileUrl(item.filename)} target="_blank" rel="noreferrer">⬇ {item.filename}</a> : <span className="muted">No file yet</span>}
          <div className="small-muted">{item.mode} • {item.speed ? `${(item.speed / 1024).toFixed(1)} KB/s` : ""} • ETA: {item.eta ?? "--"}</div>
        </div>
      </div>
    </div>
  );
}
