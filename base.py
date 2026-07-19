"""Deney Motoru (Experiment Engine).

Bir fikri kabul etmeden önce test eder: N deneme → sonuç → karar.
Denemeler saf işlevler üzerinde yürütülür; yan etkili işlemler onay
gerektirir.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from asena.engine.base import BaseEngine, EngineResult


@dataclass
class DeneySonucu:
    deneme_sayisi: int
    basarili: int
    basari_orani: float
    kabul_edildi_mi: bool
    ornekler: list[Any] = field(default_factory=list)


class ExperimentEngine(BaseEngine):
    """Hipotezleri tekrarlanan denemelerle sınavan motor."""

    name = "experiment_engine"
    group = "learning"

    def __init__(self, kabul_esigi: float = 0.8) -> None:
        super().__init__()
        self.kabul_esigi = kabul_esigi

    def deney_yap(self, deneme: Callable[[int], bool],
                  sayi: int = 100) -> DeneySonucu:
        """``deneme(i)`` işlevini ``sayi`` kez çalıştırıp başarıyı ölçer."""
        basarili = 0
        ornekler: list[Any] = []
        for i in range(sayi):
            try:
                sonuc = bool(deneme(i))
            except Exception:  # noqa: BLE001 — hatalı deneme başarısız sayılır
                sonuc = False
            if sonuc:
                basarili += 1
                if len(ornekler) < 3:
                    ornekler.append(i)
        oran = basarili / sayi if sayi else 0.0
        return DeneySonucu(
            deneme_sayisi=sayi, basarili=basarili, basari_orani=round(oran, 3),
            kabul_edildi_mi=oran >= self.kabul_esigi, ornekler=ornekler,
        )

    def process(self, girdi: dict[str, Any], **kwargs: Any) -> EngineResult:
        deneme = girdi.get("deneme")
        if not callable(deneme):
            return EngineResult.hata("Deneme işlevi verilmedi.")
        sonuc = self.deney_yap(deneme, int(girdi.get("sayi", 100)))
        karar = "kabul edildi" if sonuc.kabul_edildi_mi else "reddedildi"
        return EngineResult(
            data=sonuc, confidence=sonuc.basari_orani,
            explanation=(
                f"{sonuc.deneme_sayisi} denemede {sonuc.basarili} başarı "
                f"(%{sonuc.basari_orani * 100:.0f}); fikir {karar}."
            ),
        )
