# downloader.py
import threading
from pathlib import Path
from yt_dlp import YoutubeDL
from urllib.parse import urlparse, parse_qs


def build_ydl_options(out_dir: str, mode: str, format_id: str):
    """Build yt-dlp configuration based on mode and format."""
    out_path = str(Path(out_dir) / "%(title)s.%(ext)s")

    opts = {
        "outtmpl": out_path,
        "quiet": False,
        "no_warnings": False,
        "progress_hooks": [],
        "nocheckcertificate": True,
    }

    if mode == "audio":
        opts["format"] = format_id or "bestaudio"
        opts["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ]
    else:
        opts["format"] = format_id or "bestvideo+bestaudio/best"
        opts["merge_output_format"] = "mp4"

    return opts


def run_download(url: str, out_dir: str, mode: str, format_id: str,
                 progress_callback, cancel_event: threading.Event):
    """Run actual download with yt-dlp and send progress callbacks."""
    out_path = Path(out_dir)
    out_path.mkdir(exist_ok=True, parents=True)

    def hook(data):
        if cancel_event.is_set():
            raise Exception("Download cancelled by user")

        status = data.get("status")

        if status == "downloading":
            progress_callback({
                "status": "downloading",
                "downloaded_bytes": data.get("downloaded_bytes", 0),
                "total_bytes": data.get("total_bytes")
                    or data.get("total_bytes_estimate", 0),
                "speed": data.get("speed", 0),
                "eta": data.get("eta", 0),
            })

        elif status == "finished":
            progress_callback({"status": "finished_file"})

    opts = build_ydl_options(out_dir, mode, format_id)
    opts["progress_hooks"].append(hook)

    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        title = info.get("title") or "video"
        ext = info.get("ext") or ("mp3" if mode == "audio" else "mp4")

        final_path = str(out_path / f"{title}.{ext}")

        progress_callback({
            "status": "finished",
            "result": {"final_path": final_path}
        })

        return {"final_path": final_path}


def run_download_in_thread(url: str, out_dir: str, mode: str, format_id: str,
                           progress_callback, cancel_event: threading.Event):
    """Run downloader in a separate thread for async behavior."""

    def runner():
        try:
            progress_callback({"status": "started"})
            run_download(url, out_dir, mode, format_id, progress_callback, cancel_event)
        except Exception as e:
            progress_callback({"status": "error", "error": str(e)})

    thread = threading.Thread(target=runner, daemon=True)
    thread.start()
    return thread


def get_thumbnail_for_url(url: str) -> str:
    """Extract YouTube video ID from URL and convert to thumbnail."""
    try:
        parsed = urlparse(url)

        if "youtu" in (parsed.hostname or ""):
            if "youtu.be" in parsed.hostname:
                video_id = parsed.path.lstrip("/")
            else:
                video_id = parse_qs(parsed.query).get("v", [None])[0]

            if video_id:
                return f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"

    except Exception:
        pass

    return ""
