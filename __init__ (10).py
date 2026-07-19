"""Bilgi Ekonomisi (Knowledge Economy).

Gereksiz bilgi ezberlenmez; kayıt kararı önem puanına göre verilir.
Eşiğin altındaki bilgi yalnızca geçici bellekte tutulur ve unutma
motoruna bırakılır.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from asena.engine.base import BaseEngine, EngineResult


@dataclass
class KayitKarari:
    kaydedilsin_mi: bool
    onem: float
    gerekce: str


class KnowledgeEconomy(BaseEngine):
    """Bilginin kayda değer olup olmadığına karar veren motor."""

    name = "knowledge_economy"
    group = "learning"
    dependencies = ("priority_engine",)

    def __init__(self, esik: float = 2.0) -> None:
        super().__init__()
        self.esik = esik

    def karar_ver(self, bilgi: str, onem: float) -> KayitKarari:
        """Önem puanına göre kayıt kararı verir."""
        if onem >= self.esik:
            return KayitKarari(
                kaydedilsin_mi=True, onem=onem,
                gerekce=f"Önem {onem} ≥ eşik {self.esik}; kalıcı belleğe alınır.",
            )
        return KayitKarari(
            kaydedilsin_mi=False, onem=onem,
            gerekce=f"Önem {onem} < eşik {self.esik}; yalnızca geçici bellekte tutulur.",
        )

    def process(self, girdi: dict[str, Any], **kwargs: Any) -> EngineResult:
        karar = self.karar_ver(
            str(girdi.get("bilgi", "")), float(girdi.get("onem", 0.0))
        )
        return EngineResult(
            data=karar, ok=karar.kaydedilsin_mi, explanation=karar.gerekce
        )
