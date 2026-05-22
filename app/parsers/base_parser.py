from __future__ import annotations

from abc import ABC, abstractmethod


class BaseParser(ABC):
    @abstractmethod
    def parse(self, raw_content: str, source_url: str | None = None) -> list[dict]:
        raise NotImplementedError
