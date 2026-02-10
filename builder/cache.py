#!/usr/bin/env python3
"""
Measurement Cache - Persistent storage for actual compiled measurements
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional


class MeasurementCache:
    """Manages persistent cache of measured element sizes"""
    
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = cache_dir / "measurements.json"
        self._data = None
    
    def load(self) -> Dict:
        """Load cache from disk"""
        if self._data is None:
            if self.cache_file.exists():
                try:
                    with open(self.cache_file) as f:
                        self._data = json.load(f)
                except (json.JSONDecodeError, IOError):
                    self._data = {}
            else:
                self._data = {}
        return self._data
    
    def save(self):
        """Save cache to disk"""
        if self._data is not None:
            with open(self.cache_file, "w") as f:
                json.dump(self._data, f, indent=2)
    
    def get(self, content_hash: str) -> Optional[Dict]:
        """Get cached measurement by content hash"""
        data = self.load()
        return data.get(content_hash)
    
    def set(self, content_hash: str, measurement: Dict):
        """Store measurement in cache"""
        data = self.load()
        measurement["cached_at"] = datetime.now().isoformat()
        data[content_hash] = measurement
        self._data = data
        self.save()
    
    def clear(self):
        """Clear all cached measurements"""
        self._data = {}
        self.save()
    
    def stats(self) -> Dict:
        """Get cache statistics"""
        data = self.load()
        return {
            "total_entries": len(data),
            "cache_file": str(self.cache_file),
            "size_bytes": self.cache_file.stat().st_size if self.cache_file.exists() else 0
        }
    
    def invalidate_old(self, days: int = 30):
        """Remove entries older than specified days"""
        from datetime import timedelta
        
        data = self.load()
        cutoff = datetime.now() - timedelta(days=days)
        
        to_remove = []
        for key, value in data.items():
            cached_at = value.get("cached_at")
            if cached_at:
                cached_date = datetime.fromisoformat(cached_at)
                if cached_date < cutoff:
                    to_remove.append(key)
        
        for key in to_remove:
            del data[key]
        
        self._data = data
        self.save()
        
        return len(to_remove)
