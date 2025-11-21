# backend/torrent_downloader.py
import libtorrent as lt
import time
import threading
from pathlib import Path
from typing import Callable, Optional

class TorrentDownloader:
    def __init__(self, download_dir: str):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.session = lt.session()
        self.session.listen_on(6881, 6891)
        self.handles = {}  # torrent_id -> handle
        self.cancel_events = {}  # torrent_id -> threading.Event
        
    def add_torrent(self, torrent_id: str, magnet_link: str, progress_callback: Callable):
        """Add a torrent download"""
        params = {
            'save_path': str(self.download_dir),
            'storage_mode': lt.storage_mode_t.storage_mode_sparse,
        }
        
        handle = lt.add_magnet_uri(self.session, magnet_link, params)
        self.handles[torrent_id] = handle
        self.cancel_events[torrent_id] = threading.Event()
        
        # Start monitoring thread
        thread = threading.Thread(
            target=self._monitor_progress,
            args=(torrent_id, handle, progress_callback),
            daemon=True
        )
        thread.start()
        
        return {"status": "started", "id": torrent_id}
    
    def _monitor_progress(self, torrent_id: str, handle, progress_callback: Callable):
        """Monitor torrent download progress"""
        print(f"Starting torrent monitor for {torrent_id}")
        
        # Wait for metadata
        while not handle.has_metadata():
            if self.cancel_events.get(torrent_id, threading.Event()).is_set():
                progress_callback({"status": "cancelled"})
                return
            time.sleep(0.1)
        
        torrent_info = handle.get_torrent_info()
        progress_callback({
            "status": "metadata",
            "name": torrent_info.name(),
            "total_size": torrent_info.total_size(),
            "num_files": torrent_info.num_files()
        })
        
        # Monitor download progress
        last_downloaded = 0
        last_time = time.time()
        
        while not handle.is_seed():
            if self.cancel_events.get(torrent_id, threading.Event()).is_set():
                self.session.remove_torrent(handle)
                progress_callback({"status": "cancelled"})
                return
            
            status = handle.status()
            current_time = time.time()
            time_diff = current_time - last_time
            
            # Calculate ETA
            downloaded_bytes = status.total_download
            bytes_diff = downloaded_bytes - last_downloaded
            total_size = torrent_info.total_size()
            remaining_bytes = total_size - downloaded_bytes
            
            # Calculate average speed and ETA
            if time_diff > 0 and status.download_rate > 0:
                eta_seconds = remaining_bytes / status.download_rate
            else:
                eta_seconds = 0
            
            progress_callback({
                "status": "downloading",
                "progress": status.progress * 100,
                "download_rate": status.download_rate,
                "upload_rate": status.upload_rate,
                "num_peers": status.num_peers,
                "num_seeds": status.num_seeds,
                "total_download": status.total_download,
                "total_upload": status.total_upload,
                "eta": int(eta_seconds) if eta_seconds > 0 else 0,  # ETA in seconds
            })
            
            last_downloaded = downloaded_bytes
            last_time = current_time
            
            time.sleep(1)
        
        # Download complete
        progress_callback({
            "status": "finished",
            "save_path": str(self.download_dir / torrent_info.name())
        })
        
        print(f"Torrent {torrent_id} completed")
    
    def cancel_torrent(self, torrent_id: str):
        """Cancel a torrent download"""
        if torrent_id in self.cancel_events:
            self.cancel_events[torrent_id].set()
            
        if torrent_id in self.handles:
            handle = self.handles[torrent_id]
            self.session.remove_torrent(handle)
            del self.handles[torrent_id]
            
        return {"status": "cancelled"}
    
    def get_status(self, torrent_id: str):
        """Get current status of a torrent"""
        if torrent_id not in self.handles:
            return {"error": "Torrent not found"}
        
        handle = self.handles[torrent_id]
        status = handle.status()
        
        return {
            "progress": status.progress * 100,
            "download_rate": status.download_rate,
            "upload_rate": status.upload_rate,
            "num_peers": status.num_peers,
            "state": str(status.state)
        }

# Global torrent downloader instance
torrent_manager = None

def get_torrent_manager(download_dir: str):
    global torrent_manager
    if torrent_manager is None:
        torrent_manager = TorrentDownloader(download_dir)
    return torrent_manager
