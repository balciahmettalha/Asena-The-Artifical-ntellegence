"""Öğrenme Motoru (Learning Engine).

Beş öğrenme modunu destekler: çevrim içi (online), aktif (soru sorarak),
artımlı (incremental), sürekli (continual) ve öz denetimli
(self-supervised). Yeni kelime, ilişki, kural ve kavramlar ilgili
katmanlara işlenir ve öğrenme günlüğüne yazılır.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from asena.core.event_bus import Event
from asena.engine.base import BaseEngine, EngineResult


class OgrenmeModu(str, Enum):
    ONLINE = "online"                  # sohbet sırasında anlık
    AKTIF = "aktif"                    # soru sorarak öğrenme
    ARTIMLI = "artimli"                # eskiyi koruyarak üstüne ekleme
    SUREKLI = "surekli"                # kesintisiz eğitim modu
    OZ_DENETIMLI = "oz_denetimli"      # etiketsiz veriden örüntü çıkarma


class LearningEngine(BaseEngine):
    """Öğrenme isteklerini ilgili katmanlara dağıtan motor."""

    name = "learning_engine"
    group = "learning"
    dependencies = ("memory_engine",)

    def __init__(self) -> None:
        super().__init__()
        self.mod = OgrenmeModu.ONLINE
        self._sayac = {"kelime": 0, "iliski": 0, "kural": 0, "kavram": 0}

    # ------------------------------------------------------------------ öğren
    def kelime_ogren(self, yazim: str, kok: str | None = None,
                     tur: str | None = None, anlam: str | None = None) -> str:
        bellek = self.ctx.container.resolve("memory_engine")
        bellek.kelime_kaydet(yazim, kok=kok, tur=tur, anlam=anlam)
        self._sayac["kelime"] += 1
        self._olay("ogrenme.kelime", {"yazim": yazim})
        return yazim

    def iliski_ogren(self, kaynak: str, hedef: str, tur: str,
                     agirlik: float = 1.0) -> None:
        graf = self.ctx.container.resolve("knowledge_graph")
        graf.kenar_ekle(kaynak, hedef, tur, agirlik)
        self._sayac["iliski"] += 1
        self._olay("ogrenme.iliski", {"kaynak": kaynak, "hedef": hedef, "tur": tur})

    def kural_ogren(self, kosul: str, sonuc: str, guven: float = 1.0) -> None:
        bellek = self.ctx.container.resolve("memory_engine")
        bellek.kural_kaydet(kosul, sonuc, guven)
        self._sayac["kural"] += 1
        self._olay("ogrenme.kural", {"kosul": kosul, "sonuc": sonuc})

    def kavram_ogren(self, ad: str, ust: str, tanim: str = "") -> None:
        kavram = self.ctx.container.resolve("concept_engine")
        kavram.kavram_ogren(ad, ust, tanim)
        self._sayac["kavram"] += 1
        self._olay("ogrenme.kavram", {"ad": ad, "ust": ust})

    def oz_denetimli_oruntu(self, kelimeler: list[str]) -> dict[str, int]:
        """Etiketsiz metinden birlikte geçme örüntüleri çıkarır."""
        birliktelik: dict[str, int] = {}
        for i, a in enumerate(kelimeler):
            for b in kelimeler[i + 1: i + 4]:
                if a != b:
                    anahtar = f"{a}~{b}" if a < b else f"{b}~{a}"
                    birliktelik[anahtar] = birliktelik.get(anahtar, 0) + 1
        return birliktelik

    def sayac(self) -> dict[str, int]:
        return dict(self._sayac)

    def _olay(self, ad: str, veri: dict[str, Any]) -> None:
        self.ctx.bus.publish(Event(ad, veri, source=self.name))

    def process(self, girdi: dict[str, Any], **kwargs: Any) -> EngineResult:
        islem = girdi.get("islem", "kelime")
        if islem == "iliski":
            self.iliski_ogren(str(girdi["kaynak"]), str(girdi["hedef"]),
                              str(girdi.get("tur", "ilgili")))
            return EngineResult(explanation="İlişki öğrenildi.")
        if islem == "kural":
            self.kural_ogren(str(girdi["kosul"]), str(girdi["sonuc"]))
            return EngineResult(explanation="Kural öğrenildi.")
        if islem == "kavram":
            self.kavram_ogren(str(girdi["ad"]), str(girdi["ust"]),
                              str(girdi.get("tanim", "")))
            return EngineResult(explanation="Kavram öğrenildi.")
        self.kelime_ogren(str(girdi["yazim"]), girdi.get("kok"),
                          girdi.get("tur"), girdi.get("anlam"))
        return EngineResult(explanation="Kelime öğrenildi.")
