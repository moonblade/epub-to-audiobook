#!/usr/bin/env python3.12
import json
import re
from pathlib import Path
from typing import Any, Optional

from config import VOICE_MAPPINGS_PATH


def extract_book_title(filename: str) -> str:
    name = Path(filename).stem
    
    date_pattern = r'^\d{4}-\d{2}-\d{2}\s*-\s*'
    name = re.sub(date_pattern, '', name)
    
    chapter_patterns = [
        r'\s*-\s*[Cc]hapter\s*\d+.*$',
        r'\s*-\s*[Cc]h\s*\d+.*$',
        r'\s*[Cc]hapter\s*\d+.*$',
        r'\s*-\s*[Bb]ook\s*\d+.*$',
        r'\s*-\s*[Pp]art\s*\d+.*$',
    ]
    
    for pattern in chapter_patterns:
        name = re.sub(pattern, '', name)
    
    slug = name.lower().strip()
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    slug = re.sub(r'^-+|-+$', '', slug)
    
    return slug or "unknown"


class VoiceMappingStore:
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or VOICE_MAPPINGS_PATH
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def _get_mapping_file(self, book_slug: str) -> Path:
        return self.storage_path / f"{book_slug}.json"
    
    def load(self, book_slug: str) -> dict[str, Any]:
        mapping_file = self._get_mapping_file(book_slug)
        
        if mapping_file.exists():
            try:
                data = json.loads(mapping_file.read_text())
                return {
                    "pitch_shifts": data.get("pitch_shifts", {}),
                    "genders": data.get("genders", {}),
                }
            except (json.JSONDecodeError, KeyError):
                pass
        
        return {
            "pitch_shifts": {},
            "genders": {},
        }
    
    def save(self, book_slug: str, pitch_shifts: dict[str, float], genders: dict[str, str]) -> None:
        mapping_file = self._get_mapping_file(book_slug)
        
        data = {
            "pitch_shifts": pitch_shifts,
            "genders": genders,
        }
        
        mapping_file.write_text(json.dumps(data, indent=2))
    
    def get_book_slug(self, filename: str) -> str:
        return extract_book_title(filename)
    
    def list_books(self) -> list[str]:
        return [f.stem for f in self.storage_path.glob("*.json")]
    
    def get_mapping_summary(self, book_slug: str) -> Optional[dict[str, Any]]:
        mapping = self.load(book_slug)
        if not mapping["pitch_shifts"]:
            return None
        
        return {
            "book": book_slug,
            "characters": len(mapping["pitch_shifts"]) - 1,
            "pitch_shifts": mapping["pitch_shifts"],
        }
