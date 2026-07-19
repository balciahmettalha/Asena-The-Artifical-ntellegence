"""Sebep-Sonuç Motoru (Cause-Effect Engine).

Olaylar arasında sebep-sonuç zinciri kurar:
``yağmur → yer ıslandı → kaygan → düşme riski``. Zincirler dünya
modelindeki kurallar üzerinden ileri (sonuç) ve geri (sebep) yayılır.
"""

from __future__ import annotations

from typing import Any

from asena.engine.base import BaseEngine, EngineResult
from asena.knowledge.world_model import WorldModel


class CauseEffectEngine(BaseEngine):
    """İleri ve geri sebep-sonuç zincirleri kuran motor."""

    name = "cause_effect"
    group = "reason"
    dependencies = ("world_model",)

    def __init__(self, dunya: WorldModel | None = None) -> None:
        super().__init__()
        self.dunya = dunya or WorldModel()

    def sonuc_zinciri(self, olay: str, derinlik: int = 4) -> list[str]:
        """Olaydan başlayan sonuç zinciri."""
        return [olay, *self.dunya.sonuclar(olay, derinlik)]

    def sebep_zinciri(self, sonuc: str, derinlik: int = 4) -> list[str]:
        """Sonuca götüren sebep zinciri (geriye doğru)."""
        zincir = [sonuc]
        mevcut = sonuc
        for _ in range(derinlik):
            sebepler = self.dunya.sebep_bul(mevcut)
            if not sebepler:
                break
            mevcut = sebepler[0]
            zincir.insert(0, mevcut)
        return zincir

    def zincir_metni(self, olay: str) -> str:
        zincir = self.sonuc_zinciri(olay)
        return " → ".join(zincir)

    def riskleri_acikla(self, olay: str) -> str:
        zincir = self.sonuc_zinciri(olay)
        if len(zincir) == 1:
            return f"'{olay}' için bilinen bir sonuç zinciri bulunamadı."
        return f"'{olay}' olursa: {' → '.join(zincir[1:])}."

    def process(self, girdi: dict[str, Any], **kwargs: Any) -> EngineResult:
        islem = girdi.get("islem", "sonuc")
        if islem == "sebep":
            zincir = self.sebep_zinciri(str(girdi.get("sonuc", "")))
            return EngineResult(data=zincir, explanation=" ← ".join(zincir))
        metin = self.riskleri_acikla(str(girdi.get("olay", "")))
        return EngineResult(data=metin, explanation=metin)
