"""Soyutlama Motoru (Abstraction Engine).

İki yönde çalışır: yukarı soyutlama (kedi → canlı → madde) ve aşağı
somutlaştırma (canlı → hayvan → kedi). Kavram hiyerarşisini kullanır.
"""

from __future__ import annotations

from typing import Any

from asena.engine.base import BaseEngine, EngineResult
from asena.knowledge.concept_engine import ConceptEngine


class AbstractionEngine(BaseEngine):
    """Kavramlar arasında soyutlama/somutlaştırma yapan motor."""

    name = "abstraction_engine"
    group = "knowledge"
    dependencies = ("concept_engine",)

    def __init__(self, kavram: ConceptEngine | None = None) -> None:
        super().__init__()
        self.kavram = kavram or ConceptEngine()

    def yukari(self, ad: str, adim: int = 3) -> list[str]:
        """Yukarı soyutlama zinciri (kendisi hariç)."""
        return self.kavram.zincir(ad, derinlik=adim)[1:]

    def asagi(self, ad: str, derinlik: int = 2) -> list[str]:
        """Aşağı somutlaştırma: alt türleri ve onların alt türleri."""
        sonuc: list[str] = []
        sinir = [ad]
        for _ in range(derinlik):
            yeni: list[str] = []
            for kavram in sinir:
                yeni.extend(self.kavram.alt_turler(kavram))
            sonuc.extend(y for y in yeni if y not in sonuc)
            sinir = yeni
        return sonuc

    def soyutlama_seviyesi(self, ad: str) -> int:
        """Kavramın kökten uzaklığı: zincir uzunluğu ölçüsü."""
        return len(self.kavram.zincir(ad)) - 1

    def process(self, girdi: dict[str, Any], **kwargs: Any) -> EngineResult:
        yon = girdi.get("yon", "yukari")
        ad = str(girdi.get("ad", ""))
        if yon == "asagi":
            sonuc = self.asagi(ad, int(girdi.get("derinlik", 2)))
        else:
            sonuc = self.yukari(ad, int(girdi.get("adim", 3)))
        return EngineResult(data=sonuc, explanation=f"{yon} soyutlama: {' → '.join(sonuc)}")
