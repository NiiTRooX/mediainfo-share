from datetime import datetime
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class MediaResolution:
    width: str = ""
    height: str = ""


@dataclass
class MediaGeneral:
    format: str = ""
    duration: str = ""
    bitrate: str = ""
    size: str = ""
    frame_rate: str = ""


@dataclass
class MediaVideo:
    format: str = ""
    resolution: MediaResolution = field(default_factory=MediaResolution)
    aspect_ratio: str = ""
    frame_rate: str = ""
    bit_rate: str = ""
    bit_depth: str = ""


@dataclass
class AudioTrack:
    language: str = ""
    format: str = ""
    channels: str = ""
    bit_rate: str = ""
    format_settings: str = ""
    sampling_rate: str = ""
    commercial_name: str = ""
    title: str = ""
    flag: str = ""


@dataclass
class SubtitleTrack:
    language: str = ""
    flag: str = ""


@dataclass
class MediaInfo:
    id: str
    filename: str
    original_filename: str
    uploaded_on: datetime
    expiration: Optional[datetime] = None
    password: Optional[str] = None
    raw_output: str = ""
    general: MediaGeneral = field(default_factory=MediaGeneral)
    video: MediaVideo = field(default_factory=MediaVideo)
    audio: List[AudioTrack] = field(default_factory=list)
    subtitles: List[SubtitleTrack] = field(default_factory=list)

    def __init__(
        self,
        id: Optional[str] = None,
        filename: Optional[str] = None,
        original_filename: Optional[str] = None,
        uploaded_on: Optional[datetime] = None,
        expiration: Optional[datetime] = None,
        password: Optional[str] = None,
        raw_output: Optional[str] = None,
        parsed_info: Optional[Dict] = None,
    ):
        self.id = id
        self.filename = filename
        self.original_filename = original_filename
        self.uploaded_on = uploaded_on
        self.expiration = expiration
        self.password = password
        self.raw_output = raw_output
        self.general = MediaGeneral()
        self.video = MediaVideo()
        self.audio: List[AudioTrack] = []
        self.subtitles: List[SubtitleTrack] = []
        
        if parsed_info:
            self._parse_info(parsed_info)
    
    def _parse_info(self, parsed_info: Dict) -> None:
        """Parse the parsed_info dictionary into the appropriate fields."""
        if "general" in parsed_info:
            self.general = MediaGeneral(**parsed_info["general"])
        if "video" in parsed_info:
            video_data = parsed_info["video"].copy()
            if "resolution" in video_data:
                self.video.resolution = MediaResolution(**video_data.pop("resolution"))
            self.video = MediaVideo(**video_data)
        if "audio" in parsed_info:
            self.audio = [AudioTrack(**track) for track in parsed_info["audio"]]
        if "subtitles" in parsed_info:
            self.subtitles = [SubtitleTrack(**track) for track in parsed_info["subtitles"]]

    @classmethod
    def from_dict(cls, data: Dict) -> "MediaInfo":
        media = cls()
        media.id = data.get("id")
        media.filename = data.get("filename")
        media.original_filename = data.get("original_filename")
        media.uploaded_on = datetime.fromisoformat(data.get("uploaded_on")) if data.get("uploaded_on") else None
        media.expiration = datetime.fromisoformat(data.get("expiration")) if data.get("expiration") else None
        media.password = data.get("password")
        media.raw_output = data.get("raw_output")
        
        # Handle both parsed and parsed_info fields for backward compatibility
        parsed = data.get("parsed") or data.get("parsed_info")
        if parsed:
            if isinstance(parsed, str):
                try:
                    parsed = json.loads(parsed)
                except json.JSONDecodeError:
                    parsed = {}
            
            if isinstance(parsed, dict):
                media._parse_info(parsed)
        
        return media

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "filename": self.filename,
            "original_filename": self.original_filename,
            "uploaded_on": self.uploaded_on.isoformat() if self.uploaded_on else None,
            "expiration": self.expiration.isoformat() if self.expiration else None,
            "password": self.password,
            "raw_output": self.raw_output,
            "parsed_info": {
                "general": self.general.__dict__,
                "video": {
                    **self.video.__dict__,
                    "resolution": self.video.resolution.__dict__
                },
                "audio": [track.__dict__ for track in self.audio],
                "subtitles": [sub.__dict__ for sub in self.subtitles]
            }
        }
