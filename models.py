"""
NOTICE OF LICENSE.

Copyright 2025 @AnabolicsAnonymous

Licensed under the Affero General Public License v3.0 (AGPL-3.0)

This program is free software: you can redistribute it and/or modify
it under the terms of the Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
"""

from datetime import datetime
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class MediaResolution:
    """Class for storing media width and height"""
    width: str = ""
    height: str = ""


@dataclass
class MediaGeneral:
    """Class for storing media general information"""
    format: str = ""
    duration: str = ""
    bitrate: str = ""
    size: str = ""
    frame_rate: str = ""
    complete_name: str = ""


@dataclass
class MediaVideo:
    """Class for the video section of mediainfo"""
    format: str = ""
    width: str = ""
    height: str = ""
    aspect_ratio: str = ""
    frame_rate: str = ""
    bit_rate: str = ""
    bit_depth: str = ""


@dataclass
class AudioTrack:
    """Class for storing audio track information"""
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
    """Class for storing subtitle track information"""
    language: str = ""
    flag: str = ""


@dataclass
class MediaInfo:
    """Class for storing mediainfo data"""
    media_id: str
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
        media_id: Optional[str] = None,
        filename: Optional[str] = None,
        original_filename: Optional[str] = None,
        uploaded_on: Optional[datetime] = None,
        expiration: Optional[datetime] = None,
        password: Optional[str] = None,
        raw_output: Optional[str] = None,
        parsed_info: Optional[Dict] = None,
    ):
        self.media_id = media_id
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
            self.video = MediaVideo(**parsed_info["video"])
        if "audio" in parsed_info:
            self.audio = [AudioTrack(**track) for track in parsed_info["audio"]]
        if "subtitles" in parsed_info:
            self.subtitles = [SubtitleTrack(**track) for track in parsed_info["subtitles"]]

    @classmethod
    def from_dict(cls, data: Dict) -> "MediaInfo":
        """Create a MediaInfo object from a dictionary"""
        media = cls()
        media.media_id = data.get("id") or data.get("media_id")
        media.filename = data.get("filename")
        media.original_filename = data.get("original_filename")
        media.uploaded_on = datetime.fromisoformat(data.get("uploaded_on")) \
            if data.get("uploaded_on") else None
        media.expiration = datetime.fromisoformat(data.get("expiration")) \
            if data.get("expiration") else None
        media.password = data.get("password")
        media.raw_output = data.get("raw_output")

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
        """Convert the MediaInfo object to a dictionary"""
        return {
            "id": self.media_id,
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
                },
                "audio": [track.__dict__ for track in self.audio],
                "subtitles": [sub.__dict__ for sub in self.subtitles]
            }
        }
