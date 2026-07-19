"""Çalışma Belleği (Workspace).

Düşünme sırasında kullanılan geçici bellektir; insanın kısa süreli
belleği gibi sınırlı kapasiteye sahiptir. Dikkat sistemi buraya hangi
bilginin gireceğine karar verir; unutma motoru zayıflayanları ayıklar.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CalismaOgesi:
    anahtar: str
    deger: Any
    guc: float = 1.0                     # 0–1 arası etkinleşme gücü
    onem: float = 1.0
    giris_zamani: float = field(default_factory=time.time)
    erisim_sayisi: int = 0

    def eris(self, guclenme: float = 0.1) -> None:
        self.guc = min(1.0, self.guc + guclenme)
        self.erisim_sayisi += 1


class Workspace:
    """Sınırlı kapasiteli etkin çalışma alanı."""

    def __init__(self, kapasite: int = 25) -> None:
        self.kapasite = kapasite
        self._ogeler: dict[str, CalismaOgesi] = {}

    def ekle(self, anahtar: str, deger: Any, guc: float = 1.0,
             onem: float = 1.0) -> None:
        """Öğe ekler; kapasite doluysa en zayıf düşer."""
        if anahtar in self._ogeler:
            self._ogeler[anahtar].deger = deger
            self._ogeler[anahtar].eris()
            return
        if len(self._ogeler) >= self.kapasite:
            en_zayif = min(self._ogeler.values(), key=lambda o: o.guc)
            del self._ogeler[en_zayif.anahtar]
        self._ogeler[anahtar] = CalismaOgesi(
            anahtar=anahtar, deger=deger, guc=guc, onem=onem
        )

    def get(self, anahtar: str) -> Any | None:
        oge = self._ogeler.get(anahtar)
        if oge is None:
            return None
        oge.eris()
        return oge.deger

    def oge(self, anahtar: str) -> CalismaOgesi | None:
        return self._ogeler.get(anahtar)

    def etkinler(self, en_cok: int | None = None) -> list[CalismaOgesi]:
        """Güce göre sıralı etkin öğeler."""
        sirali = sorted(self._ogeler.values(), key=lambda o: -o.guc)
        return sirali[:en_cok] if en_cok else sirali

    def cikar(self, anahtar: str) -> None:
        self._ogeler.pop(anahtar, None)

    def guc_azalt(self, oran: float) -> list[str]:
        """Tüm öğelerin gücünü azaltır; silinenleri döndürür."""
        silinen: list[str] = []
        for anahtar, oge in list(self._ogeler.items()):
            oge.guc *= oran
            if oge.guc < 0.05:
                del self._ogeler[anahtar]
                silinen.append(anahtar)
        return silinen

    def temizle(self) -> None:
        self._ogeler.clear()

    def __len__(self) -> int:
        return len(self._ogeler)

    def __contains__(self, anahtar: str) -> bool:
        return anahtar in self._ogeler
