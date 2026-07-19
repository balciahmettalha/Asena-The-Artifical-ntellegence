"""Çoklu Akıl Yürütme Motoru (Multi-Reasoning Engine).

Aynı probleme beş yaklaşımı paralel uygular ve karşılaştırır:
mantıksal, matematiksel, istatistiksel, deneysel ve benzetimsel.
Sonuçlar birleştirilir; uzlaşma varsa güven yükselir.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from asena.engine.base import BaseEngine, EngineResult


@dataclass
class YaklasimSonucu:
    yaklasim: str
    sonuc: str
    guven: float
    detay: str = ""


class MultiReasoningEngine(BaseEngine):
    """Farklı akıl yürütme tarzlarını karşılaştıran motor."""

    name = "multi_reasoning"
    group = "reason"

    def __init__(self) -> None:
        super().__init__()
        self._stratejiler: dict[str, Any] = {}

    def strateji_kaydet(self, yaklasim: str, islev: Any) -> None:
        """Bir yaklaşım için strateji işlevi kaydeder (Strategy deseni)."""
        self._stratejiler[yaklasim] = islev

    def karsilastir(self, problem: Any) -> list[YaklasimSonucu]:
        """Kayıtlı tüm yaklaşımları probleme uygular."""
        sonuclar: list[YaklasimSonucu] = []
        for yaklasim, islev in self._stratejiler.items():
            try:
                sonuc, guven, detay = islev(problem)
                sonuclar.append(YaklasimSonucu(yaklasim, str(sonuc),
                                               float(guven), str(detay)))
            except Exception as exc:  # noqa: BLE001
                sonuclar.append(YaklasimSonucu(yaklasim, "", 0.0, f"hata: {exc!r}"))
        return sorted(sonuclar, key=lambda s: -s.guven)

    @staticmethod
    def uzlasma(sonuclar: list[YaklasimSonucu]) -> tuple[str, float]:
        """Sonuçlar arası uzlaşma: en çok tekrarlanan sonuç + ortalama güven."""
        gecerli = [s for s in sonuclar if s.sonuc]
        if not gecerli:
            return ("", 0.0)
        sayac: dict[str, list[float]] = {}
        for s in gecerli:
            sayac.setdefault(s.sonuc, []).append(s.guven)
        en_iyi = max(sayac.items(), key=lambda kv: (len(kv[1]), sum(kv[1])))
        tekrar = len(en_iyi[1])
        guven = min(0.95, sum(en_iyi[1]) / tekrar + 0.1 * (tekrar - 1))
        return (en_iyi[0], round(guven, 2))

    def process(self, girdi: Any, **kwargs: Any) -> EngineResult:
        sonuclar = self.karsilastir(girdi)
        sonuc, guven = self.uzlasma(sonuclar)
        return EngineResult(
            data={"sonuclar": sonuclar, "uzlasma": sonuc},
            confidence=guven,
            explanation=f"Uzlaşma sonucu: {sonuc} (güven %{guven * 100:.0f})",
        )
