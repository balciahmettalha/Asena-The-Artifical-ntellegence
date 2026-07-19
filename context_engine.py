"""Bellek Sıkıştırma (Memory Compression).

Çok sayıda benzer bilgiyi az sayıda özet kavrama indirger:
``aslan, kaplan, kedi → kedigiller``. Ortak üst kavramı bulan öğeler
tek özet düğümde birleştirilir.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from asena.engine.base import BaseEngine, EngineResult
from asena.knowledge.concept_engine import ConceptEngine


class MemoryCompression(BaseEngine):
    """Bellek öğelerini ortak kavramlara sıkıştıran motor."""

    name = "memory_compression"
    group = "memory"
    dependencies = ("concept_engine",)

    def __init__(self, kavram: ConceptEngine | None = None) -> None:
        super().__init__()
        self.kavram = kavram or ConceptEngine()

    def sikistir(self, ogeler: list[str],
                 hedef_oran: float = 0.2) -> dict[str, list[str]]:
        """Öğeleri ortak üst kavramlarına göre gruplar.

        Returns:
            ``{özet_kavram: [öğeler]}`` — özet bulunamayanlar kendi adıyla.
        """
        gruplar: dict[str, list[str]] = defaultdict(list)
        for oge in ogeler:
            zincir = self.kavram.zincir(oge)
            ozet = zincir[1] if len(zincir) > 1 else oge
            gruplar[ozet].append(oge)
        hedef = max(1, int(len(ogeler) * hedef_oran))
        if len(gruplar) <= hedef:
            return dict(gruplar)
        # En büyük grupları koru, kalanları tek tek üst kavrama taşı
        sirali = sorted(gruplar.items(), key=lambda kv: -len(kv[1]))
        sonuc: dict[str, list[str]] = {}
        for i, (ozet, uyeler) in enumerate(sirali):
            if i < hedef:
                sonuc[ozet] = uyeler
            else:
                for uye in uyeler:
                    sonuc.setdefault(uye, []).append(uye)
        return sonuc

    def ozet_metni(self, ogeler: list[str]) -> str:
        gruplar = self.sikistir(ogeler)
        satirlar = [
            f"- {ozet}: {len(uyeler)} öğe ({', '.join(uyeler[:4])}"
            + (", …" if len(uyeler) > 4 else "") + ")"
            for ozet, uyeler in sorted(gruplar.items())
        ]
        return (
            f"{len(ogeler)} öğe {len(gruplar)} özet kavrama sıkıştırıldı:\n"
            + "\n".join(satirlar)
        )

    def process(self, girdi: dict[str, Any], **kwargs: Any) -> EngineResult:
        metin = self.ozet_metni(list(girdi.get("ogeler", [])))
        return EngineResult(data=metin, explanation=metin)
