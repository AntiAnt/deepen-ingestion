import datetime
import subprocess
from datetime import datetime as dt
from io import BytesIO
from pathlib import Path
from typing import Dict

import yt_dlp
from reliquery import Relic


class YTAudioIngestion:
    yt_dlp_opts = {
        "format": "bestaudio/best",
        "outtmpl": "%(id)s.%(ext)s",
        "noplaylist": True,
    }

    def ingest_audio(self, url) -> Dict:
        print(f"Ingestion: ingesting {url}")

        with yt_dlp.YoutubeDL(self.yt_dlp_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        video_metadata = {
            "video_id": info["id"],
            "title": info.get("title", "Untitled"),
            "youtube_url": url,
            "duration_seconds": info.get("duration"),
            "ingested_at": dt.now(datetime.timezone.utc).isoformat() + "Z",
            "stage": "audio_ready",
        }

        raw_file = Path(f"{video_metadata['video_id']}.{info['ext']}")

        # Convert to WAV (16kHz, mono, 16-bit)
        print(f"Ingestion: Converting to WAV: 16kHz, mono")
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            "pipe:0",
            "-ar",
            "16000",
            "-ac",
            "1",
            "-c:a",
            "pcm_s16le",  # Force 16-bit PCM
            "-f",
            "wav",
            "pipe:1",
        ]

        with raw_file.open("rb") as f:
            process = subprocess.Popen(
                cmd, stdin=f, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            wav_bytes, stderr = process.communicate()

        if process.returncode != 0:
            raise RuntimeError(f"FFmpeg failed: {stderr.decode()}")

        # Clean up raw file
        try:
            raw_file.unlink()
        except OSError as e:
            print(f"Warning: Could not delete raw file {raw_file}: {e}")

        print(f"Ingestion: Title - {video_metadata['title']}")

        return {
            "audio": BytesIO(wav_bytes),
            "video_metadata": video_metadata,
            "video_info": info,
        }


def get_ingestion_service():
    return YTAudioIngestion()
