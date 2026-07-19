"""Bilgi Sıkıştırma (Knowledge Compression).

100.000 ayrıntılı bilgi yerine 10.000 üst düzey kavram üretir. Aynı
yüklem ve nesneyi paylaşan önermeler tek genelleştirilmiş önermede
birleştirilir: "aslan etçildir", "kaplan etçildir" → "aslan ve kaplan
etçildir" ve üst kavram varsa "kedigiller etçildir".
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from asena.engine.base import BaseEngine, EngineResult
from asena.knowledge.concept_engine import ConceptEngine


class KnowledgeCompression(BaseEngine):
    """Önerme kümelerini genelleştirilmiş bilgilere sıkıştıran motor."""

    name = "knowledge_compression"
    group = "memory"
    dependencies = ("concept_engine",)

    def __init__(self, kavram: ConceptEngine | None = None) -> None:
        super().__init__()
        self.kavram = kavram or ConceptEngine()

    def sikistir(self, onermeler: list[dict[str, Any]],
                 ust_kavram_kullan: bool = True) -> list[dict[str, Any]]:
        """Aynı (yüklem, nesne) çiftini paylaşan önermeleri birleştirir."""
        gruplar: dict[tuple[str, str], list[str]] = defaultdict(list)
        for o in onermeler:
            anahtar = (str(o.get("yuklem", "")), str(o.get("nesne") or ""))
            gruplar[anahtar].append(str(o.get("ozne", "")))
        sonuc: list[dict[str, Any]] = []
        for (yuklem, nesne), ozneler in gruplar.items():
            if len(ozneler) == 1:
                sonuc.append({"ozne": ozneler[0], "yuklem": yuklem, "nesne": nesne or None})
                continue
            ozet = None
            if ust_kavram_kullan:
                ortak = self.kavram.ortak_ust(ozneler[0], ozneler[1])
                if ortak and all(self.kavram.ust_mu(o, ortak) for o in ozneler):
                    ozet = ortak
            ozne = ozet or " ve ".join(sorted(set(ozneler)))
            sonuc.append({
                "ozne": ozne, "yuklem": yuklem, "nesne": nesne or None,
                "kaynak": f"{len(ozneler)} önermenin sıkıştırılması",
            })
        return sonuc

    def oran(self, onermeler: list[dict[str, Any]]) -> float:
        """Sıkıştırma oranı: çıktı / girdi."""
        if not onermeler:
            return 1.0
        return len(self.sikistir(onermeler)) / len(onermeler)

    def process(self, girdi: dict[str, Any], **kwargs: Any) -> EngineResult:
        onermeler = list(girdi.get("onermeler", []))
        sonuc = self.sikistir(onermeler)
        return EngineResult(
            data=sonuc,
            explanation=f"{len(onermeler)} önerme {len(sonuc)} özet bilgiye indirildi.",
        )
