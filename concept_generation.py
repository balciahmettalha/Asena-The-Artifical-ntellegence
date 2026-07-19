"""Öncelik Motoru (Priority Engine).

Bilgilere önem puanı verir: ``2+2=4 ★★★★★``, ``mahalledeki kırmızı
araba ★``. Puan; genellik (herkes için geçerlilik), ilişki sayısı ve
kaynak güvenilirliğinden hesaplanır.
"""

from __future__ import annotations

from typing import Any

from asena.engine.base import BaseEngine, EngineResult


class PriorityEngine(BaseEngine):
    """Bilginin önem puanını hesaplayan motor."""

    name = "priority_engine"
    group = "learning"

    GENEL_KAVRAMLAR: frozenset[str] = frozenset({
        "matematik", "fizik", "mantık", "su", "insan", "zaman", "enerji",
        "sayı", "dil", "bilgi", "yaşam", "canlı",
    })

    def puanla(self, bilgi: str, kavramlar: list[str] | None = None,
               iliski_sayisi: int = 0, kaynak_guveni: float = 0.5) -> float:
        """1–5 arası önem puanı (★ karşılığı) hesaplar."""
        kavramlar = kavramlar or []
        genellik = 1.0 + sum(
            1.0 for k in kavramlar if k in self.GENEL_KAVRAMLAR
        )
        iliski = min(2.0, iliski_sayisi / 5)
        guven = max(0.0, min(1.0, kaynak_guveni))
        puan = 1.0 + genellik + iliski + guven
        return round(min(5.0, puan), 2)

    @staticmethod
    def yildiz(puan: float) -> str:
        """Puanı yıldız gösterimine çevirir."""
        dolu = max(1, min(5, round(puan)))
        return "★" * dolu + "☆" * (5 - dolu)

    def process(self, girdi: dict[str, Any], **kwargs: Any) -> EngineResult:
        puan = self.puanla(
            str(girdi.get("bilgi", "")),
            list(girdi.get("kavramlar", [])),
            int(girdi.get("iliski_sayisi", 0)),
            float(girdi.get("kaynak_guveni", 0.5)),
        )
        return EngineResult(
            data={"puan": puan, "yildiz": self.yildiz(puan)},
            explanation=f"Önem puanı: {puan} {self.yildiz(puan)}",
        )
