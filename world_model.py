"""Dünya Simülasyonu (World Simulation).

"Bunu yaparsam ne olur?" sorusuna çoklu ihtimal üretir (en çok 10) ve
olasılıklarına göre sıralar. İhtimaller dünya modelinin sebep-sonuç
kurallarından türetilir.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from asena.engine.base import BaseEngine, EngineResult
from asena.knowledge.world_model import WorldModel


@dataclass
class Ihtimal:
    sonuc: str
    olasilik: float
    zincir: list[str]


class WorldSimulation(BaseEngine):
    """Eylem sonuçlarını olasılıklarıyla simüle eden motor."""

    name = "world_simulation"
    group = "planning"
    dependencies = ("world_model",)

    def __init__(self, dunya: WorldModel | None = None,
                 en_cok_ihtimal: int = 10) -> None:
        super().__init__()
        self.dunya = dunya or WorldModel()
        self.en_cok = en_cok_ihtimal

    def simule_et(self, eylem: str) -> list[Ihtimal]:
        """Eylemin olası sonuçlarını zincir derinliğiyle ağırlıklandırır."""
        zincir = self.dunya.sonuclar(eylem, derinlik=5)
        ihtimaller: list[Ihtimal] = []
        for i, sonuc in enumerate(zincir):
            olasilik = round(0.9 ** (i + 1), 3)  # derinleştikçe olasılık düşer
            ihtimaller.append(Ihtimal(sonuc=sonuc, olasilik=olasilik,
                                      zincir=[eylem, *zincir[: i + 1]]))
        ihtimaller.sort(key=lambda x: -x.olasilik)
        return ihtimaller[: self.en_cok]

    def en_olasi(self, eylem: str) -> Ihtimal | None:
        ihtimaller = self.simule_et(eylem)
        return ihtimaller[0] if ihtimaller else None

    def process(self, girdi: dict[str, Any], **kwargs: Any) -> EngineResult:
        eylem = str(girdi.get("eylem", ""))
        ihtimaller = self.simule_et(eylem)
        if not ihtimaller:
            return EngineResult(
                ok=False, confidence=0.2,
                explanation=f"'{eylem}' için simülasyon üretilemedi; dünya modelinde kural yok.",
            )
        ozet = "; ".join(
            f"{i.sonuc} (%{i.olasilik * 100:.0f})" for i in ihtimaller[:3]
        )
        return EngineResult(
            data=ihtimaller, confidence=ihtimaller[0].olasilik,
            explanation=f"En olası sonuçlar: {ozet}",
        )
