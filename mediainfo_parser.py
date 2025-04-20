from typing import Dict, Optional
from models import (
    MediaGeneral,
    MediaVideo,
    AudioTrack,
    SubtitleTrack,
)


class MediaInfoParser:
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
        if not lang_code:
            return ""

        code = lang_code.strip().upper()
        if "(" in code and ")" in code:
            code = code[code.find("(") + 1 : code.find(")")].strip()

        return self.language_flags.get(code, "")

    def parse_file(self, file_path: str) -> Dict:
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
                elif line.startswith("Video"):
                    current_section = "video"
                    current_track = None
                    current_track_type = None
                    continue
                elif line.startswith("Audio"):
                    if current_track and current_track_type == "audio":
                        info["audio"].append(current_track.__dict__)
                    current_section = "audio"
                    current_track = AudioTrack()
                    current_track_type = "audio"
                    continue
                elif line.startswith("Text"):
                    if current_track and current_track_type == "audio":
                        info["audio"].append(current_track.__dict__)
                    current_section = "text"
                    current_track = None
                    current_track_type = "text"
                    continue
                elif line == "Menu":
                    current_section = "menu"
                    current_track = None
                    current_track_type = None
                    continue

                if ":" in line:
                    key, value = map(str.strip, line.split(":", 1))
                    self._parse_key_value(
                        key, value, current_section, info, current_track, current_track_type
                    )

            if current_track and current_track_type == "audio":
                info["audio"].append(current_track.__dict__)

            for track in info["audio"]:
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
        current_track: Optional[AudioTrack],
        current_track_type: Optional[str],
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

        elif section == "video":
            if key == "format":
                info["video"]["format"] = value
            elif key == "width":
                if "resolution" not in info["video"]:
                    info["video"]["resolution"] = {}
                info["video"]["resolution"]["width"] = value.replace("pixels", "").strip()
            elif key == "height":
                if "resolution" not in info["video"]:
                    info["video"]["resolution"] = {}
                info["video"]["resolution"]["height"] = value.replace("pixels", "").strip()
            elif key == "resolution":
                if "resolution" not in info["video"]:
                    info["video"]["resolution"] = {}
                # Handle both "1920x1080" and single value formats
                if "x" in value:
                    width, height = value.split("x")
                    info["video"]["resolution"]["width"] = width.strip()
                    info["video"]["resolution"]["height"] = height.strip()
                else:
                    info["video"]["resolution"]["width"] = value.strip()
                    info["video"]["resolution"]["height"] = value.strip()
            elif key in ["display aspect ratio", "aspect ratio"]:
                info["video"]["aspect_ratio"] = value
            elif key in ["frame rate", "frame rate mode"]:
                info["video"]["frame_rate"] = value
            elif key in ["bit rate", "nominal bit rate"]:
                info["video"]["bit_rate"] = value
            elif key in ["bit depth", "bit depth (bits)"]:
                info["video"]["bit_depth"] = value

        elif section == "audio" and current_track:
            if key == "language":
                current_track.language = value
            elif key == "format":
                current_track.format = value
            elif key in ["channel(s)", "channels"]:
                current_track.channels = value
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

        elif section == "text" and key == "language":
            info["subtitles"].append({
                "language": value,
                "flag": self.get_language_flag(value)
            })
