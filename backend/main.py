# backend/main.py
import asyncio
import json
import os
import subprocess
import platform
import threading
from pathlib import Path
from typing import Dict, Optional, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from downloader import run_download_in_thread, get_thumbnail_for_url
from db import create_tables, add_history_entry, list_history, delete_history
from torrent_downloader import get_torrent_manager

app = FastAPI(title="Video Downloader Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure downloads directory
DEFAULT_DL_DIR = Path.home() / "Downloads"
DEFAULT_DL_DIR.mkdir(parents=True, exist_ok=True)

# Torrent download directory
TORRENT_DL_DIR = Path.home() / "Downloads" / "Torrents"
TORRENT_DL_DIR.mkdir(parents=True, exist_ok=True)

# Create database tables
create_tables()

# WebSocket Manager
class WSManager:
    def __init__(self):
        self.connections: Dict[str, WebSocket] = {}
    
    def add_connection(self, id: str, websocket: WebSocket):
        self.connections[id] = websocket
    
    def remove_connection(self, id: str):
        self.connections.pop(id, None)
    
    async def send(self, id: str, message: dict):
        ws = self.connections.get(id)
        if ws:
            try:
                await ws.send_json(message)
            except Exception as e:
                print(f"WebSocket send error: {e}")

ws_manager = WSManager()

# Job Manager
class JobManager:
    def __init__(self):
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
    
    def register(self, id: str, thread: threading.Thread, cancel_event: threading.Event):
        with self._lock:
            self._jobs[id] = {"thread": thread, "cancel_event": cancel_event}
    
    def get_cancel_event(self, id: str) -> Optional[threading.Event]:
        with self._lock:
            item = self._jobs.get(id)
            return item["cancel_event"] if item else None
    
    def unregister(self, id: str):
        with self._lock:
            self._jobs.pop(id, None)
    
    def is_running(self, id: str) -> bool:
        with self._lock:
            return id in self._jobs

job_manager = JobManager()

@app.get("/formats")
async def get_formats(url: str = Query(...)):
    """Get available formats for a video URL"""
    try:
        from yt_dlp import YoutubeDL
        
        ydl_opts = {
            'quiet': False,
            'no_warnings': False,
            'nocheckcertificate': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
                'Sec-Fetch-Mode': 'navigate',
            },
            'extractor_retries': 3,
            'socket_timeout': 30,
        }
        
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            formats = info.get('formats', [])
            title = info.get('title', 'Unknown')
            thumbnail = info.get('thumbnail', '')
            duration = info.get('duration', 0)
            
            print(f"\n=== Found {len(formats)} total formats for: {title} ===")
            
            def get_quality_label(height):
                if height >= 4320:
                    return "8K"
                elif height >= 2160:
                    return "4K"
                elif height >= 1440:
                    return "2K"
                elif height >= 1080:
                    return "1080p"
                elif height >= 720:
                    return "720p"
                elif height >= 480:
                    return "480p"
                elif height >= 360:
                    return "360p"
                elif height >= 240:
                    return "240p"
                elif height >= 144:
                    return "144p"
                else:
                    return f"{height}p"
            
            # First pass: Look for combined video+audio formats
            combined_formats = {}
            
            # Second pass: Look for video-only formats (usually higher quality)
            video_only_formats = {}
            
            for f in formats:
                format_id = f.get('format_id')
                ext = f.get('ext', 'mp4')
                height = f.get('height')
                vcodec = f.get('vcodec', 'none')
                acodec = f.get('acodec', 'none')
                filesize = f.get('filesize') or f.get('filesize_approx', 0)
                
                if not height or height == 0:
                    continue
                
                quality_label = get_quality_label(height)
                
                # Combined video+audio
                if vcodec != 'none' and acodec != 'none':
                    print(f"✓ Combined: {quality_label} ({height}p) - ID: {format_id}")
                    if quality_label not in combined_formats:
                        combined_formats[quality_label] = {
                            'format_id': format_id,
                            'quality': quality_label,
                            'resolution': f"{height}p",
                            'ext': ext,
                            'filesize': filesize,
                            'height': height,
                        }
                
                # Video-only (needs audio to be merged)
                elif vcodec != 'none' and acodec == 'none':
                    print(f"✓ Video-only: {quality_label} ({height}p) - ID: {format_id}")
                    if quality_label not in video_only_formats:
                        video_only_formats[quality_label] = {
                            'format_id': f"{format_id}+bestaudio",
                            'quality': quality_label,
                            'resolution': f"{height}p",
                            'ext': 'mp4',
                            'filesize': filesize,
                            'height': height,
                        }
            
            # Merge both dictionaries
            all_video_formats = {}
            all_video_formats.update(video_only_formats)
            
            for quality, fmt in combined_formats.items():
                if quality not in all_video_formats:
                    all_video_formats[quality] = fmt
            
            video_formats = sorted(all_video_formats.values(), key=lambda x: x['height'], reverse=True)
            
            print(f"\n=== Final video formats: {[f['quality'] for f in video_formats]} ===")
            
            # Audio formats
            audio_formats = []
            best_audio = None
            
            for f in formats:
                format_id = f.get('format_id')
                ext = f.get('ext', '').lower()
                vcodec = f.get('vcodec', 'none')
                acodec = f.get('acodec', 'none')
                abr = f.get('abr', 0)
                filesize = f.get('filesize') or f.get('filesize_approx', 0)
                
                if acodec != 'none' and vcodec == 'none':
                    if not best_audio or abr > best_audio.get('abr', 0):
                        best_audio = {
                            'format_id': format_id,
                            'quality': 'Best Quality',
                            'ext': ext if ext in ['webm', 'opus', 'm4a'] else 'webm',
                            'filesize': filesize,
                            'abr': abr,
                        }
            
            if best_audio:
                audio_formats.append(best_audio)
            
            if not audio_formats:
                audio_formats = [
                    {'format_id': 'bestaudio', 'quality': 'Best Quality', 'ext': 'webm', 'filesize': 0},
                ]
            
            if not video_formats:
                print("WARNING: No video formats found, using fallback")
                video_formats = [
                    {'format_id': 'bestvideo+bestaudio/best', 'quality': 'Best Available', 'resolution': 'Auto', 'ext': 'mp4', 'filesize': 0},
                ]
            
            return {
                'title': title,
                'thumbnail': thumbnail,
                'duration': duration,
                'video_formats': video_formats,
                'audio_formats': audio_formats,
            }
            
    except Exception as e:
        error_msg = str(e)
        print(f"Error fetching formats: {error_msg}")
        
        if "bot" in error_msg.lower() or "captcha" in error_msg.lower() or "verify" in error_msg.lower():
            return JSONResponse({
                'error': 'verification_required',
                'message': 'The video platform requires human verification.'
            }, status_code=429)
        
        return JSONResponse({
            'error': 'fetch_failed',
            'message': f'Failed to fetch video information: {error_msg}'
        }, status_code=500)

@app.post("/download")
async def start_download(payload: dict):
    url = payload.get("url")
    if not url:
        return JSONResponse({"error": "url required"}, status_code=400)
    
    client_id = payload.get("id") or str(abs(hash(url)))[:12]
    mode = payload.get("mode", "video")
    format_id = payload.get("format_id", "best")
    
    if job_manager.is_running(client_id):
        return JSONResponse({"error": "job already running"}, status_code=400)
    
    cancel_event = threading.Event()
    
    loop = asyncio.get_event_loop()
    
    def progress_sender(msg: dict):
        try:
            future = asyncio.run_coroutine_threadsafe(
                ws_manager.send(client_id, msg),
                loop
            )
            future.result(timeout=1.0)
        except Exception as e:
            print(f"Progress sender error: {e}")
    
    thread = run_download_in_thread(url, str(DEFAULT_DL_DIR), mode, format_id, progress_sender, cancel_event)
    job_manager.register(client_id, thread, cancel_event)
    
    def watcher():
        thread.join()
        try:
            add_history_entry({
                "id": client_id,
                "url": url,
                "filename": None,
                "mode": mode,
                "status": "finished",
            })
        except Exception:
            pass
        finally:
            job_manager.unregister(client_id)
    
    threading.Thread(target=watcher, daemon=True).start()
    return {"id": client_id, "status": "started"}

@app.post("/cancel")
async def cancel_download(payload: dict):
    id = payload.get("id")
    if not id:
        return JSONResponse({"error": "id required"}, status_code=400)
    
    cancel_event = job_manager.get_cancel_event(id)
    if cancel_event:
        cancel_event.set()
        return {"id": id, "status": "cancelling"}
    return JSONResponse({"error": "not found"}, status_code=404)

@app.post("/open-file")
async def open_file(payload: dict):
    """Open a file with the default application"""
    file_path = payload.get("path")
    if not file_path:
        return JSONResponse({"error": "File path required"}, status_code=400)
    
    file_path = Path(file_path)
    
    if not file_path.is_absolute():
        file_path = DEFAULT_DL_DIR / file_path
    
    print(f"Trying to open file: {file_path}")
    
    if not file_path.exists():
        print(f"File not found: {file_path}")
        return JSONResponse({"error": f"File not found: {file_path}"}, status_code=404)
    
    try:
        system = platform.system()
        file_path_str = str(file_path.absolute())
        
        if system == "Windows":
            os.startfile(file_path_str)
        elif system == "Darwin":
            subprocess.run(["open", file_path_str])
        else:
            subprocess.run(["xdg-open", file_path_str])
        
        print(f"Successfully opened: {file_path_str}")
        return {"status": "opened", "path": file_path_str}
    except Exception as e:
        print(f"Error opening file: {str(e)}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/show-in-folder")
async def show_in_folder(payload: dict):
    """Show file in folder/file explorer"""
    file_path = payload.get("path")
    if not file_path:
        return JSONResponse({"error": "File path required"}, status_code=400)
    
    file_path = Path(file_path)
    
    if not file_path.is_absolute():
        file_path = DEFAULT_DL_DIR / file_path
    
    print(f"Trying to show in folder: {file_path}")
    
    if not file_path.exists():
        print(f"File not found: {file_path}")
        file_path = file_path.parent
    
    try:
        system = platform.system()
        file_path_str = str(file_path.absolute())
        
        if system == "Windows":
            if file_path.is_file():
                subprocess.run(["explorer", "/select,", file_path_str])
            else:
                subprocess.run(["explorer", file_path_str])
        elif system == "Darwin":
            subprocess.run(["open", "-R", file_path_str])
        else:
            folder_path = str(file_path.parent if file_path.is_file() else file_path)
            subprocess.run(["xdg-open", folder_path])
        
        print(f"Successfully opened folder: {file_path_str}")
        return {"status": "shown", "path": file_path_str}
    except Exception as e:
        print(f"Error showing folder: {str(e)}")
        return JSONResponse({"error": str(e)}, status_code=500)

# TORRENT ENDPOINTS

@app.post("/torrent/add")
async def add_torrent(payload: dict):
    """Add a magnet link or torrent file"""
    magnet_link = payload.get("magnet")
    if not magnet_link:
        return JSONResponse({"error": "magnet link required"}, status_code=400)
    
    torrent_id = payload.get("id") or str(abs(hash(magnet_link)))[:12]
    
    manager = get_torrent_manager(str(TORRENT_DL_DIR))
    
    loop = asyncio.get_event_loop()
    
    def progress_sender(msg: dict):
        try:
            future = asyncio.run_coroutine_threadsafe(
                ws_manager.send(f"torrent_{torrent_id}", msg),
                loop
            )
            future.result(timeout=1.0)
        except Exception as e:
            print(f"Torrent progress sender error: {e}")
    
    result = manager.add_torrent(torrent_id, magnet_link, progress_sender)
    
    return {"id": torrent_id, "status": "started"}

@app.post("/torrent/cancel")
async def cancel_torrent_download(payload: dict):
    """Cancel a torrent download"""
    torrent_id = payload.get("id")
    if not torrent_id:
        return JSONResponse({"error": "id required"}, status_code=400)
    
    manager = get_torrent_manager(str(TORRENT_DL_DIR))
    result = manager.cancel_torrent(torrent_id)
    
    return result

@app.get("/torrent/status/{torrent_id}")
async def get_torrent_status(torrent_id: str):
    """Get status of a torrent"""
    manager = get_torrent_manager(str(TORRENT_DL_DIR))
    return manager.get_status(torrent_id)

@app.websocket("/ws/torrent_{torrent_id}")
async def torrent_websocket_endpoint(websocket: WebSocket, torrent_id: str):
    """WebSocket endpoint for torrent progress"""
    await websocket.accept()
    ws_manager.add_connection(f"torrent_{torrent_id}", websocket)
    print(f"Torrent WebSocket connected: {torrent_id}")
    
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        print(f"Torrent WebSocket disconnected: {torrent_id}")
    except Exception as e:
        print(f"Torrent WebSocket error: {e}")
    finally:
        ws_manager.remove_connection(f"torrent_{torrent_id}")

@app.get("/thumbnail")
async def thumbnail(url: str = Query(...)):
    try:
        thumb = get_thumbnail_for_url(url)
        return {"thumbnail": thumb}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/history/list")
async def api_history_list(limit: int = 200):
    try:
        items = list_history(limit=limit)
        return {"history": items}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.delete("/history/delete/{id}")
async def api_history_delete(id: str):
    try:
        ok = delete_history(id)
        return {"ok": True} if ok else JSONResponse({"error": "not found"}, status_code=404)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    ws_manager.add_connection(client_id, websocket)
    print(f"WebSocket connected: {client_id}")
    
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        print(f"WebSocket disconnected: {client_id}")
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        ws_manager.remove_connection(client_id)

@app.get("/ping")
async def ping():
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"message": "AI Video Downloader API", "status": "running"}
