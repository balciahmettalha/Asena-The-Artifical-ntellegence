"""Kavram Üretimi (Concept Generation).

İki kavramın ilişki kümelerini birleştirerek yeni kavram üretir:
``elektrik + su → elektrikli hidro sistem`` gibi. Yeni kavram, iki
kaynağın ilişkilerini devralır ve grafa eklenir.
"""

from __future__ import annotations

from typing import Any

from asena.engine.base import BaseEngine, EngineResult
from asena.knowledge.knowledge_graph import KnowledgeGraph


class ConceptGeneration(BaseEngine):
    """Var olan kavramlardan yeni kavram türeten motor."""

    name = "concept_generation"
    group = "knowledge"
    dependencies = ("knowledge_graph",)

    def __init__(self, graf: KnowledgeGraph | None = None) -> None:
        super().__init__()
        self.graf = graf or KnowledgeGraph()

    def birlestir(self, a: str, b: str, yeni_ad: str | None = None) -> dict[str, Any]:
        """İki kavramı birleştirir; miras alınan ilişkileri döndürür."""
        ad = yeni_ad or f"{a}_{b}"
        miras: list[tuple[str, str]] = []
        for kaynak in (a, b):
            for kenar in self.graf.komsular(kaynak):
                self.graf.kenar_ekle(ad, kenar.hedef, kenar.tur,
                                     kenar.agirlik * 0.9, kalici=False)
                miras.append((kenar.tur, kenar.hedef))
        self.graf.kenar_ekle(ad, a, "bilesen", 1.0, kalici=False)
        self.graf.kenar_ekle(ad, b, "bilesen", 1.0, kalici=False)
        return {"ad": ad, "miras": miras}

    def tanim_uret(self, a: str, b: str, yeni_ad: str | None = None) -> str:
        """Birleşik kavram için Türkçe tanım cümlesi üretir."""
        sonuc = self.birlestir(a, b, yeni_ad)
        miraslar = ", ".join(sorted({h for _, h in sonuc["miras"]})[:5])
        return (
            f"'{sonuc['ad']}' kavramı üretildi: {a} ve {b} bileşenlerinden "
            f"gelir; {miraslar} özelliklerini devralır."
        )

    def process(self, girdi: dict[str, Any], **kwargs: Any) -> EngineResult:
        a, b = str(girdi.get("a", "")), str(girdi.get("b", ""))
        if not a or not b:
            return EngineResult.hata("Birleştirilecek iki kavram gerekli.")
        tanim = self.tanim_uret(a, b, girdi.get("yeni_ad"))
        return EngineResult(data=tanim, explanation=tanim)
