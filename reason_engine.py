"""Bellek önbelleği (Memory Cache): sık erişilen veriler için LRU.

Sözdizim çözümlemeleri, bilgi grafiği düğümleri ve tekrarlanan sorgu
sonuçları burada tutulur; gereksiz yeniden hesaplama yapılmaz.
"""

from __future__ import annotations

import threading
from collections import OrderedDict
from typing import Any


class LRUCache:
    """Kapasite sınırlı, iş parçacığı güvenli LRU önbelleği."""

    def __init__(self, kapasite: int = 1024) -> None:
        self._kapasite = max(1, kapasite)
        self._veri: OrderedDict[Any, Any] = OrderedDict()
        self._kilit = threading.RLock()
        self._isabet = 0
        self._iskalama = 0

    def get(self, anahtar: Any) -> Any | None:
        with self._kilit:
            if anahtar not in self._veri:
                self._iskalama += 1
                return None
            self._isabet += 1
            self._veri.move_to_end(anahtar)
            return self._veri[anahtar]

    def put(self, anahtar: Any, deger: Any) -> None:
        with self._kilit:
            if anahtar in self._veri:
                self._veri.move_to_end(anahtar)
            self._veri[anahtar] = deger
            if len(self._veri) > self._kapasite:
                self._veri.popitem(last=False)

    def get_or(self, anahtar: Any, uretici) -> Any:
        """Önbellekte yoksa üretip saklar."""
        deger = self.get(anahtar)
        if deger is not None:
            return deger
        deger = uretici()
        self.put(anahtar, deger)
        return deger

    def istatistik(self) -> dict[str, Any]:
        with self._kilit:
            toplam = self._isabet + self._iskalama
            return {
                "boyut": len(self._veri),
                "kapasite": self._kapasite,
                "isabet": self._isabet,
                "iskalama": self._iskalama,
                "isabet_orani": (self._isabet / toplam) if toplam else 0.0,
            }

    def temizle(self) -> None:
        with self._kilit:
            self._veri.clear()
