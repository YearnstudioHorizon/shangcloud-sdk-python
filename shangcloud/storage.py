from __future__ import annotations

import threading
from abc import ABC, abstractmethod


class TempVarStorage(ABC):
    @abstractmethod
    def set_temp_variable(self, key: str, value: str) -> None:
        pass

    @abstractmethod
    def get_temp_variable(self, key: str) -> str:
        pass

    @abstractmethod
    def delete_temp_variable(self, key: str) -> None:
        pass


class RamKv(TempVarStorage):
    def __init__(self) -> None:
        self._storage: dict[str, str] = {}
        self._lock = threading.Lock()

    def set_temp_variable(self, key: str, value: str) -> None:
        with self._lock:
            self._storage[key] = value

    def get_temp_variable(self, key: str) -> str:
        with self._lock:
            if key not in self._storage:
                raise KeyError(f"Key '{key}' not found")
            return self._storage[key]

    def delete_temp_variable(self, key: str) -> None:
        with self._lock:
            self._storage.pop(key, None)
