"""Bilgi Yoğunluğu (Knowledge Density).

Temel bilgiler daha güçlü temsil edilir: çok bağlantılı kavramların
önem puanı yükseltilir, böylece unutma ve sıkıştırma süreçlerinde
korunurlar.
"""

from __future__ import annotations

from typing import Any

from asena.engine.base import BaseEngine, EngineResult
from asena.knowledge.knowledge_graph import KnowledgeGraph


class KnowledgeDensity(BaseEngine):
    """Kavram bağlantı yoğunluğunu önem puanına dönüştüren motor."""

    name = "knowledge_density"
    group = "learning"
    dependencies = ("knowledge_graph",)

    def __init__(self, graf: KnowledgeGraph | None = None) -> None:
        super().__init__()
        self.graf = graf or KnowledgeGraph()

    def yogunluk(self, kavram: str) -> float:
        """Bağlantı sayısından yoğunluk skoru üretir (logaritmik doyum)."""
        baglanti = len(self.graf.komsular(kavram)) + len(
            self.graf.komsular(kavram, yon="gelen")
        )
        if baglanti == 0:
            return 0.0
        import math

        return round(min(1.0, math.log1p(baglanti) / math.log1p(50)), 3)

    def onem_katmani(self, kavram: str) -> float:
        """Yoğunluğu 1–5 önem puanına çevirir."""
        return round(1.0 + 4.0 * self.yogunluk(kavram), 2)

    def en_yogunlar(self, adet: int = 10) -> list[tuple[str, float]]:
        """En yüksek yoğunluklu kavramları döndürür."""
        skorlar = [
            (ad, self.yogunluk(ad)) for ad in self.graf.dugumler
        ]
        skorlar.sort(key=lambda x: -x[1])
        return skorlar[:adet]

    def process(self, girdi: dict[str, Any], **kwargs: Any) -> EngineResult:
        kavram = str(girdi.get("kavram", ""))
        yogunluk = self.yogunluk(kavram)
        return EngineResult(
            data={"kavram": kavram, "yogunluk": yogunluk,
                  "onem": self.onem_katmani(kavram)},
            explanation=f"'{kavram}' yoğunluğu: {yogunluk}",
        )
