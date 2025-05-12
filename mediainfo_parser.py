"""
NOTICE OF LICENSE.

Copyright 2025 @AnabolicsAnonymous

Licensed under the Affero General Public License v3.0 (AGPL-3.0)

This program is free software: you can redistribute it and/or modify
it under the terms of the Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
"""

from typing import Dict, Optional, Union
from models import AudioTrack, SubtitleTrack

class MediaInfoParser:
    """Class for parsing MediaInfo output into a dictionary"""
    def __init__(self):
        self.language_flags = {
            "JP": "🇯🇵",
            "JA": "🇯🇵",
            "EN": "🇺🇸",
            "US": "🇺🇸",
            "GB": "🇬🇧",
            "FR": "🇫🇷",
            "ES": "🇪🇸",
            "DE": "🇩🇪",
            "IT": "🇮🇹",
            "CN": "🇨🇳",
            "ZH": "🇨🇳",
            "KO": "🇰🇷",
            "KR": "🇰🇷",
            "RU": "🇷🇺",
        }

    def get_language_flag(self, lang_code: Optional[str]) -> str:
        """Get the language flag for a given language code"""
        if not lang_code:
            return ""

        code = lang_code.strip().upper()
        if "(" in code and ")" in code:
            code = code[code.find("(") + 1 : code.find(")")].strip()

        return self.language_flags.get(code, "")

    def parse_file(self, file_path: str) -> Dict:
        """Parse the MediaInfo output file into a dictionary"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = "\n".join(line.strip() for line in f if line.strip())

            info = {
                "general": {},
                "video": {},
                "audio": [],
                "subtitles": []
            }

            current_section = None
            current_track = None
            current_track_type = None

            for line in content.split("\n"):
                line = line.strip()
                if not line:
                    continue
                if line == "General":
                    current_section = "general"
                    current_track = None
                    current_track_type = None
                    continue
                if line.startswith("Video"):
                    current_section = "video"
                    current_track = None
                    current_track_type = None
                    continue
                if line.startswith("Audio"):
                    if current_track and current_track_type == "audio":
                        info["audio"].append(current_track.__dict__)
                    current_section = "audio"
                    current_track = AudioTrack()
                    current_track_type = "audio"
                    continue
                if line.startswith("Text"):
                    if current_track and current_track_type == "audio":
                        info["audio"].append(current_track.__dict__)
                    if current_track and current_track_type == "text":
                        info["subtitles"].append(current_track.__dict__)
                    current_section = "text"
                    current_track = SubtitleTrack()
                    current_track_type = "text"
                    continue
                if line == "Menu":
                    if current_track and current_track_type == "text":
                        info["subtitles"].append(current_track.__dict__)
                    current_section = "menu"
                    current_track = None
                    current_track_type = None
                    continue

                if ":" in line:
                    key, value = map(str.strip, line.split(":", 1))
                    self._parse_key_value(
                        key, value, current_section, info, current_track
                    )

            if current_track and current_track_type == "audio":
                info["audio"].append(current_track.__dict__)

            if current_track and current_track_type == "text":
                info["subtitles"].append(current_track.__dict__)

            for track in info["audio"]:
                if track.get("language"):
                    track["flag"] = self.get_language_flag(track["language"])

            for track in info["subtitles"]:
                if track.get("language"):
                    track["flag"] = self.get_language_flag(track["language"])

            return info

        except Exception as e:
            print(f"Error parsing MediaInfo: {str(e)}")
            raise

    def _parse_key_value(
        self,
        key: str,
        value: str,
        section: str,
        info: Dict,
        current_track: Union[AudioTrack, SubtitleTrack, None],
    ) -> None:
        key = key.lower()

        if section == "general":
            if key == "format":
                info["general"]["format"] = value
            elif key == "duration":
                info["general"]["duration"] = value
            elif key in ["overall bit rate", "bit rate"]:
                info["general"]["bitrate"] = value
            elif key in ["file size", "size"]:
                info["general"]["size"] = value
            elif key == "frame rate":
                info["general"]["frame_rate"] = value
            elif key == "complete name":
                info["general"]["complete_name"] = value
            elif key == "movie name":
                info["general"]["movie_name"] = value

        elif section == "video":
            if key == "format":
                info["video"]["format"] = value
            elif key == "width":
                info["video"]["width"] = value.replace("pixels", "").replace(" ", "").strip()
            elif key == "height":
                info["video"]["height"] = value.replace("pixels", "").replace(" ", "").strip()
            elif key in ["display aspect ratio", "aspect ratio"]:
                info["video"]["aspect_ratio"] = value
            elif key in ["frame rate", "frame rate mode"]:
                info["video"]["frame_rate"] = value
            elif key in ["bit rate", "nominal bit rate"]:
                info["video"]["bit_rate"] = value
            elif key in ["bit depth", "bit depth (bits)"]:
                info["video"]["bit_depth"] = value
            elif key == "hdr format":
                info["video"]["hdr_format"] = value
            elif key == "color primaries":
                info["video"]["color_primaries"] = value
            elif key == "transfer characteristics":
                info["video"]["transfer_characteristics"] = value
            elif key == "title":
                info["video"]["title"] = value
            elif key == "stream size":
                info["video"]["stream_size"] = value

        elif section == "audio" and current_track:
            if key == "language":
                current_track.language = value
            elif key == "format":
                current_track.format = value
            elif key == "channel layout":
                main_channel_names = ["Lscr", "Rscr", "C", "Lc", "Rc", "L", "R", "Lw", "Rw", "Lss", "Rss", "Ls", "Rs", "Lsd", "Rsd", "Lb", "Rb", "Cb", "M"]
                height_channel_names = ["Bfc", "Bfl", "Bfr", "Tfc", "Vhl", "Vhr", "Tfl", "Tfr", "Tsl", "Tsr", "Lvs", "Rvs", "Tbl", "Tbr", "Tbc", "Tc"]
                lfe_channel_names = ["LFE", "LFE2"]
                main_channels = 0
                lfe_channels = 0
                height_channels = 0
                channels = value.split()
                for channel in channels:
                    if channel in main_channel_names:
                        main_channels += 1
                        continue
                    if channel in lfe_channel_names:
                        lfe_channels += 1
                        continue
                    if channel in height_channel_names:
                        height_channels += 1
                current_track.channels = f"{main_channels}.{lfe_channels}{f'.{height_channels}' if height_channels > 0 else ''}"
            elif key in ["bit rate", "nominal bit rate"]:
                current_track.bit_rate = value
            elif key == "format settings":
                current_track.format_settings = value
            elif key in ["sampling rate", "sampling frequency"]:
                current_track.sampling_rate = value
            elif key == "commercial name":
                current_track.commercial_name = value
            elif key == "title":
                current_track.title = value
            elif key == "stream size":
                current_track.stream_size = value
            elif key == "default":
                current_track.default = value

        elif section == "text" and current_track:
            if key == "language":
                current_track.language = value
            elif key == "title":
                current_track.title = value
            elif key == "default":
                current_track.default = value
            elif key == "forced":
                current_track.forced = value
