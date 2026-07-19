"""Enerji Motoru (Energy Engine).

İnsan beyni gibi kaynak dağıtır: kolay probleme az, zor probleme çok.
Zorluk; bilinmeyen kelime sayısı, niyet türü ve bağlam genişliğinden
tahmin edilir; bütçe (adım sayısı, hipotez sayısı) buna göre verilir.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from asena.engine.base import BaseEngine, EngineResult


@dataclass
class EnerjiButcesi:
    zorluk: float                    # 0–1
    en_cok_adim: int
    en_cok_hipotez: int
    derinlik: int
    gerekce: str


class EnergyEngine(BaseEngine):
    """Problemin zorluğuna göre kaynak bütçesi veren motor."""

    name = "energy_engine"
    group = "governance"

    ZOR_NIYETLER: frozenset[str] = frozenset({"neden_sorusu", "soru", "emir"})

    def butce_hesapla(self, niyet: str, bilinmeyen_sayisi: int = 0,
                      kavram_sayisi: int = 0) -> EnerjiButcesi:
        """Zorluğu tahmin edip kaynak bütçesi üretir."""
        zorluk = 0.2
        if niyet in self.ZOR_NIYETLER:
            zorluk += 0.3
        zorluk += min(0.3, bilinmeyen_sayisi * 0.1)
        zorluk += min(0.2, kavram_sayisi * 0.02)
        zorluk = round(min(1.0, zorluk), 2)
        butce = EnerjiButcesi(
            zorluk=zorluk,
            en_cok_adim=3 + int(zorluk * 7),
            en_cok_hipotez=2 + int(zorluk * 3),
            derinlik=1 + int(zorluk * 4),
            gerekce=(
                f"Zorluk {zorluk:.2f}: {bilinmeyen_sayisi} bilinmeyen kelime, "
                f"niyet '{niyet}'"
            ),
        )
        return butce

    def process(self, girdi: dict[str, Any], **kwargs: Any) -> EngineResult:
        butce = self.butce_hesapla(
            str(girdi.get("niyet", "bildirim")),
            int(girdi.get("bilinmeyen_sayisi", 0)),
            int(girdi.get("kavram_sayisi", 0)),
        )
        return EngineResult(
            data=butce,
            explanation=(
                f"Bütçe: {butce.en_cok_adim} adım, {butce.en_cok_hipotez} hipotez, "
                f"derinlik {butce.derinlik} ({butce.gerekce})"
            ),
        )
