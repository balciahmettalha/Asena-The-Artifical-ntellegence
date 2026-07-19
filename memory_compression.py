"""Kavram Motoru (Concept Engine).

Kelime değil kavram öğrenir: her kavram bir üst kavrama bağlanır ve
``kedi → hayvan → canlı → yaşam`` biçiminde hiyerarşi zincirleri kurulur.
Zincirler bilgi grafiğinin ``ust_tur`` kenarları üzerinde yaşar.
"""

from __future__ import annotations

from typing import Any

from asena.engine.base import BaseEngine, EngineResult
from asena.knowledge.knowledge_graph import KnowledgeGraph


class ConceptEngine(BaseEngine):
    """Kavram hiyerarşisini kuran ve sorgulayan motor."""

    name = "concept_engine"
    group = "knowledge"
    dependencies = ("knowledge_graph",)

    def __init__(self, graf: KnowledgeGraph | None = None) -> None:
        super().__init__()
        self.graf = graf or KnowledgeGraph()

    # ------------------------------------------------------------------ kurulum
    def kavram_ekle(self, ad: str, ust: str | None = None,
                    tanim: str = "") -> None:
        """Kavramı ekler; üst kavram verilirse hiyerarşiye bağlar."""
        self.graf.dugum_ekle(ad, tur="kavram", tanim=tanim)
        if ust:
            self.graf.dugum_ekle(ust, tur="kavram")
            self.graf.kenar_ekle(ad, ust, "ust_tur", 1.0)

    def kavram_ogren(self, ad: str, ust: str, tanim: str = "") -> str:
        """Bilinmeyen kelimeyi kavram ağına yerleştirir."""
        self.kavram_ekle(ad, ust=ust, tanim=tanim)
        if self._ctx is not None:
            from asena.core.event_bus import Event

            self.ctx.bus.publish(
                Event("bilgi.kavram_eklendi", {"ad": ad, "ust": ust},
                      source=self.name)
            )
        return ad

    # ------------------------------------------------------------------ sorgu
    def zincir(self, ad: str, derinlik: int = 8) -> list[str]:
        """Üst kavram zinciri: ``kedi → hayvan → canlı → yaşam``."""
        zincir = [ad]
        mevcut = ad
        for _ in range(derinlik):
            ustlar = self.graf.komsular(mevcut, tur="ust_tur")
            if not ustlar:
                break
            mevcut = ustlar[0].hedef
            zincir.append(mevcut)
        return zincir

    def alt_turler(self, ad: str) -> list[str]:
        """Kavramın doğrudan alt türleri."""
        return [k.kaynak for k in self.graf.komsular(ad, tur="ust_tur", yon="gelen")]

    def ortak_ust(self, a: str, b: str) -> str | None:
        """İki kavramın en yakın ortak üst kavramı."""
        za = self.zincir(a)
        for aday in self.zincir(b):
            if aday in za:
                return aday
        return None

    def ust_mu(self, alt: str, ust: str) -> bool:
        """``alt`` kavramı ``ust`` zincirinde mi? (kedi bir hayvan mı?)"""
        return ust in self.zincir(alt)

    # ------------------------------------------------------------------ motor
    def process(self, girdi: dict[str, Any], **kwargs: Any) -> EngineResult:
        islem = girdi.get("islem", "zincir")
        if islem == "ekle":
            self.kavram_ekle(str(girdi["ad"]), girdi.get("ust"),
                             str(girdi.get("tanim", "")))
            return EngineResult(data=girdi["ad"], explanation="Kavram eklendi.")
        if islem == "ust_mu":
            sonuc = self.ust_mu(str(girdi["alt"]), str(girdi["ust"]))
            return EngineResult(data=sonuc, explanation="Hiyerarşi sorgulandı.")
        zincir = self.zincir(str(girdi.get("ad", "")))
        return EngineResult(data=zincir, explanation=" → ".join(zincir))
