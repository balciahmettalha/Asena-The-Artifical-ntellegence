"""Karar Motoru (Decision Engine).

Birden çok seçeneğin artılarını ve eksilerini tartar, en mantıklı seçimi
yapar. Puan = Σ(artı ağırlıkları) − Σ(eksi ağırlıkları); beraberlikte
açıklama üretilir.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from asena.engine.base import BaseEngine, EngineResult


@dataclass
class Secenek:
    ad: str
    artilar: list[tuple[str, float]] = field(default_factory=list)
    eksiler: list[tuple[str, float]] = field(default_factory=list)

    @property
    def puan(self) -> float:
        return sum(a for _, a in self.artilar) - sum(e for _, e in self.eksiler)


class DecisionEngine(BaseEngine):
    """Artı/eksi tartımıyla seçim yapan motor."""

    name = "decision_engine"
    group = "decision"

    def karar_ver(self, secenekler: list[Secenek]) -> dict[str, Any]:
        """Seçenekleri puanlar; kazananı ve gerekçeyi döndürür."""
        if not secenekler:
            return {"secim": None, "gerekce": "Değerlendirilecek seçenek yok."}
        sirali = sorted(secenekler, key=lambda s: -s.puan)
        kazanan = sirali[0]
        if len(sirali) > 1 and sirali[1].puan == kazanan.puan:
            return {
                "secim": None,
                "gerekce": (
                    f"'{kazanan.ad}' ile '{sirali[1].ad}' eşit puanda; "
                    "ek ölçüt gerekli."
                ),
                "puanlar": {s.ad: s.puan for s in sirali},
            }
        gerekce = (
            f"'{kazanan.ad}' seçildi: {len(kazanan.artilar)} artı "
            f"(+{sum(a for _, a in kazanan.artilar):.1f}), "
            f"{len(kazanan.eksiler)} eksi (−{sum(e for _, e in kazanan.eksiler):.1f}); "
            f"net puan {kazanan.puan:.1f}."
        )
        return {
            "secim": kazanan.ad,
            "gerekce": gerekce,
            "puanlar": {s.ad: s.puan for s in sirali},
        }

    def process(self, girdi: dict[str, Any], **kwargs: Any) -> EngineResult:
        secenekler = [
            Secenek(
                ad=str(s["ad"]),
                artilar=[(str(a), float(w)) for a, w in s.get("artilar", [])],
                eksiler=[(str(a), float(w)) for a, w in s.get("eksiler", [])],
            )
            for s in girdi.get("secenekler", [])
        ]
        sonuc = self.karar_ver(secenekler)
        return EngineResult(
            data=sonuc, ok=sonuc["secim"] is not None,
            explanation=sonuc["gerekce"],
        )
