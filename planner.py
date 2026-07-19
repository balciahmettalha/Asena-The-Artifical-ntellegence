"""Mimari Öz-Analiz (Self Architecture Analysis).

Sistem kendi modüllerini değerlendirir: "Logic Engine yavaş → optimize
edilmeli". Motorların sağlık durumunu ve (varsa) çalışma süresi
ölçümlerini toplayıp iyileştirme önerileri üretir.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from asena.engine.base import BaseEngine, EngineResult


@dataclass
class ModulRaporu:
    motor: str
    saglikli_mi: bool
    ortalama_sure_ms: float = 0.0
    oneriler: list[str] = field(default_factory=list)


class SelfArchitectureAnalysis(BaseEngine):
    """Kendi mimarisini denetleyen motor."""

    name = "self_architecture_analysis"
    group = "governance"

    YAVAS_ESIGI_MS = 100.0

    def __init__(self) -> None:
        super().__init__()
        self._sureler: dict[str, list[float]] = {}

    def olcum_kaydet(self, motor: str, sure_ms: float) -> None:
        """Motor çalışma süresi ölçümü kaydeder."""
        self._sureler.setdefault(motor, []).append(sure_ms)

    def analiz_et(self) -> list[ModulRaporu]:
        """Kayıtlı tüm motorların sağlık ve performans raporunu çıkarır."""
        raporlar: list[ModulRaporu] = []
        kayit = self.ctx.container.resolve("engine_registry")
        for ad in kayit.names():
            motor = kayit.get(ad)
            saglikli = motor.health_check()
            sureler = self._sureler.get(ad, [])
            ortalama = sum(sureler) / len(sureler) if sureler else 0.0
            oneriler: list[str] = []
            if not saglikli:
                oneriler.append("Motor bağlanmamış; başlatma sırası denetlenmeli.")
            if ortalama > self.YAVAS_ESIGI_MS:
                oneriler.append(
                    f"'{ad}' yavaş ({ortalama:.0f} ms); önbellek veya optimize gerekli."
                )
            raporlar.append(ModulRaporu(ad, saglikli, ortalama, oneriler))
        return raporlar

    def sure_olc(self, motor: str, islev: Any, *args: Any, **kwargs: Any) -> Any:
        """Bir motor çağrısının süresini ölçer ve kaydeder."""
        baslangic = time.perf_counter()
        sonuc = islev(*args, **kwargs)
        self.olcum_kaydet(motor, (time.perf_counter() - baslangic) * 1000)
        return sonuc

    def process(self, girdi: Any = None, **kwargs: Any) -> EngineResult:
        raporlar = self.analiz_et()
        sorunlu = [r for r in raporlar if r.oneriler]
        ozet = (
            f"{len(raporlar)} motor incelendi; {len(sorunlu)} motorda öneri var."
        )
        return EngineResult(data=raporlar, explanation=ozet)
