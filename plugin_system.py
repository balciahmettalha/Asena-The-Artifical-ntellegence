"""Evrensel Bilgi Kimliği (Universal Knowledge ID) üreteci.

Her bilgi ``KB-00000001`` biçiminde benzersiz kimlik alır; kullanım
yerleri bu kimlikle izlenir. Üreteç iş parçacığı güvenlidir ve
veritabanındaki son kimlikten devam edebilir.
"""

from __future__ import annotations

import re
import threading


class UniversalIDGenerator:
    """Sıralı ve tekil bilgi kimliği üretir."""

    ON_EK = "KB"
    GENISLIK = 8

    def __init__(self, baslangic: int = 0) -> None:
        self._sayaç = baslangic
        self._kilit = threading.Lock()

    @classmethod
    def kimlikten_sayi(cls, kimlik: str) -> int:
        """``KB-00000007`` → ``7``; geçersiz biçimde 0 döner."""
        eslesme = re.fullmatch(rf"{cls.ON_EK}-(\d{{{cls.GENISLIK}}})", kimlik or "")
        return int(eslesme.group(1)) if eslesme else 0

    @classmethod
    def mevcuttan_devam(cls, son_kimlik: str | None) -> "UniversalIDGenerator":
        """Veritabanındaki son kimlikten devam eden üreteç kurar."""
        return cls(cls.kimlikten_sayi(son_kimlik or ""))

    def uret(self) -> str:
        """Yeni benzersiz kimlik döndürür."""
        with self._kilit:
            self._sayaç += 1
            return f"{self.ON_EK}-{self._sayaç:0{self.GENISLIK}d}"

    @property
    def sayac(self) -> int:
        return self._sayaç
