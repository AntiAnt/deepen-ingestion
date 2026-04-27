import datetime
import re
import subprocess
from datetime import datetime as dt
from io import BytesIO
from pathlib import Path
from typing import Dict, Optional

import yt_dlp
from reliquery import Relic

class SourceTypeError(RuntimeError):
    pass

class AudioIngestion:
    def ingest_audio(self, path: str) -> Dict:
        raise NotImplementedError


class FilePathAudioIngestion(AudioIngestion):
    @staticmethod
    def _get_audio_duration(input_path: Path) -> Optional[float]:
        cmd = ["ffmpeg", "-y", "-i", str(input_path), "-f", "null", "-"]

        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL
        )
        _, stderr = process.communicate()
        
        output = stderr.decode(errors="ignore")
        match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", output)
        if match:
            h, m, s = match.groups()
            return int(h) * 3600 + int(m) * 60 + float(s)
        return None
    
    def ingest_audio(self, path: str) -> Dict:
        input_path = Path(path).expanduser()
        
        if not input_path.is_absolute():
            input_path.resolve()
        
        if not input_path.exists():
            raise FileNotFoundError(f"Audio file: {str(input_path)} not found")
        
        cmd = [
            "ffmpeg",
            "-y",
            "-i", str(input_path),
            "-ar", "16000",
            "-ac", "1",
            "-c:a", "pcm_s16le",
            "-f", "wav",
            "pipe:1"
        ]

        print(f"Ingestion: Converting to WAV: 16kHz, mono")

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL
        )

        wav_bytes, stderr = process.communicate()

        if process.returncode != 0:
            raise RuntimeError(f"FFmpeg failed: {stderr.decode()}")
        
        metadata = {
            "video_id": input_path.stem,
            "title": input_path.stem,
            "duration_seconds": self._get_audio_duration(input_path),
            "ingested_at": dt.now(datetime.timezone.utc).isoformat() + "Z",
            "stage": "audio_ready",
        }

        return {
            "audio": BytesIO(wav_bytes),
            "metadata": metadata
        }


class YTAudioIngestion(AudioIngestion):
    yt_dlp_opts = {
        "format": "bestaudio/best",
        "outtmpl": "%(id)s.%(ext)s",
        "noplaylist": True,
    }

    def ingest_audio(self, path) -> Dict:
        print(f"Ingestion: ingesting {path}")

        with yt_dlp.YoutubeDL(self.yt_dlp_opts) as ydl:
            info = ydl.extract_info(path, download=True)

        video_metadata = {
            "video_id": info["id"],
            "title": info.get("title", "Untitled"),
            "youtube_url": path,
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
            "metadata": video_metadata,
            "info": info,
        }


def get_ingestion_service(source_type: str) -> AudioIngestion:
    if source_type == "file-system":
        return FilePathAudioIngestion()
    elif source_type == "youtube":
        return YTAudioIngestion()
    else:
        raise SourceTypeError(f"Ingestion type not supported: {source_type}")
