"""Duygu Çözümleme (Sentiment Analysis).

Karşı tarafın duygusunu çözümler: mutlu, üzgün, sinirli, heyecanlı.
ASENA duygulanım *üretmez*; yalnızca kullanıcının duygu durumunu anlar
ve yanıt üslubunu buna göre ayarlar.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from asena.engine.base import BaseEngine, EngineResult
from asena.syntax.morphology import tr_lower

DUYGU_SOZLUK: dict[str, set[str]] = {
    "mutlu": {"mutlu", "sevinçli", "harika", "süper", "güzel", "teşekkür", "sağol",
              "mükemmel", "bayıldım", "sevindim", "iyi"},
    "uzgun": {"üzgün", "kederli", "kötü", "berbat", "mutsuz", "ağlamak", "yalnız",
              "pişman", "maalesef"},
    "sinirli": {"sinirli", "öfkeli", "kızgın", "deli", "saçmalık", "yeter",
                "bıktım", "rezalet"},
    "heyecanli": {"heyecanlı", "sabırsız", "wow", "vay", "inanılmaz", "olağanüstü"},
}

OLUMSUZLUK: set[str] = {"değil", "hiç", "yok", "olmaz"}


@dataclass
class DuyguRaporu:
    duygu: str
    guven: float
    isaretler: list[str]


class SentimentAnalysis(BaseEngine):
    """Metinden duygu durumu çözümleyen motor."""

    name = "sentiment_analysis"
    group = "governance"

    def cozumle(self, metin: str) -> DuyguRaporu:
        """Metindeki duygu işaretlerini puanlar."""
        kucuk = tr_lower(metin)
        kelimeler = set(kucuk.replace(".", " ").replace(",", " ").split())
        olumsuz = bool(kelimeler & OLUMSUZLUK)
        skorlar: dict[str, float] = {}
        isaretler: list[str] = []
        for duygu, sozcukler in DUYGU_SOZLUK.items():
            eslesen = kelimeler & sozcukler
            if eslesen:
                skor = len(eslesen) * (0.5 if olumsuz else 1.0)
                skorlar[duygu] = skor
                isaretler.extend(sorted(eslesen))
        if "!" in metin and skorlar:
            for duygu in skorlar:
                skorlar[duygu] += 0.3
        if not skorlar:
            return DuyguRaporu("notr", 0.5, [])
        duygu = max(skorlar, key=skorlar.get)
        guven = min(0.95, 0.5 + 0.2 * skorlar[duygu])
        return DuyguRaporu(duygu, round(guven, 2), isaretler)

    def process(self, girdi: str, **kwargs: Any) -> EngineResult:
        rapor = self.cozumle(str(girdi))
        return EngineResult(
            data=rapor, confidence=rapor.guven,
            explanation=f"Duygu: {rapor.duygu} (işaretler: {', '.join(rapor.isaretler) or 'yok'})",
        )
