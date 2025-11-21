import React, { useEffect } from "react";
import { useDownload } from "../context/DownloadContext";
import DownloadCard from "./DownloadCard";

export default function DownloadQueue() {
  const { state } = useDownload();

  return (
    <div className="queue-card">
      <h3>Download Queue</h3>
      {state.queue.length === 0 && <p className="muted">Queue is empty — add downloads</p>}
      <div className="queue-list">
        {state.queue.map((item) => (
          <DownloadCard key={item.id} item={item} />
        ))}
      </div>
    </div>
  );
}
