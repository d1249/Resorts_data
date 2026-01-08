from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Dict, Optional


class DiskCache:
    def __init__(self, base_dir: Path, ttl_days: int = 30) -> None:
        self.base_dir = base_dir
        self.ttl_seconds = ttl_days * 86400
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _hash_key(self, key: str) -> str:
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    def _path_for(self, namespace: str, key: str) -> Path:
        safe_namespace = namespace.replace("/", "_")
        return self.base_dir / safe_namespace / f"{self._hash_key(key)}.json"

    def get(self, namespace: str, key: str) -> Optional[Dict[str, Any]]:
        path = self._path_for(namespace, key)
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
        ts = payload.get("timestamp", 0)
        if self.ttl_seconds and time.time() - ts > self.ttl_seconds:
            return None
        return payload.get("data")

    def set(self, namespace: str, key: str, data: Dict[str, Any]) -> None:
        path = self._path_for(namespace, key)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"timestamp": time.time(), "data": data}
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
