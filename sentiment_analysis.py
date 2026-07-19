"""Güven Motoru (Confidence Engine).

Güven yalnızca bir yüzde değildir; güvenin *nedeni* de hesaplanır:
kanıt sayısı, destekleyen bilgi miktarı ve kaynak güvenilirliği birlikte
değerlendirilir.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from asena.engine.base import BaseEngine, EngineResult


@dataclass
class GuvenRaporu:
    puan: float                       # 0–1
    kanit_sayisi: int
    destekleyen_bilgi: int
    kaynak_guvenilirligi: float
    neden: str


class ConfidenceEngine(BaseEngine):
    """Kanıt temelli güven hesaplayan motor."""

    name = "confidence_engine"
    group = "decision"

    def hesapla(self, kanit_sayisi: int = 0, destekleyen_bilgi: int = 0,
                kaynak_guvenilirligi: float = 0.5,
                celiski_var_mi: bool = False) -> GuvenRaporu:
        """Bileşenlerden toplam güven puanı üretir.

        ``puan = 0.4·kanıt + 0.3·destek + 0.3·kaynak``; çelişki varsa yarıya
        düşer. Kanıt ve destek bileşenleri logaritmik doyuma gider.
        """
        kanit_bilesen = min(1.0, kanit_sayisi / 5)
        destek_bilesen = min(1.0, destekleyen_bilgi / 10)
        kaynak_bilesen = max(0.0, min(1.0, kaynak_guvenilirligi))
        puan = 0.4 * kanit_bilesen + 0.3 * destek_bilesen + 0.3 * kaynak_bilesen
        if celiski_var_mi:
            puan *= 0.5
        neden = (
            f"{kanit_sayisi} kanıt (bileşen {kanit_bilesen:.2f}), "
            f"{destekleyen_bilgi} destekleyen bilgi (bileşen {destek_bilesen:.2f}), "
            f"kaynak güvenilirliği {kaynak_bilesen:.2f}"
            + ("; çelişki cezası uygulandı" if celiski_var_mi else "")
        )
        return GuvenRaporu(
            puan=round(puan, 3), kanit_sayisi=kanit_sayisi,
            destekleyen_bilgi=destekleyen_bilgi,
            kaynak_guvenilirligi=kaynak_bilesen, neden=neden,
        )

    def process(self, girdi: dict[str, Any], **kwargs: Any) -> EngineResult:
        rapor = self.hesapla(
            int(girdi.get("kanit_sayisi", 0)),
            int(girdi.get("destekleyen_bilgi", 0)),
            float(girdi.get("kaynak_guvenilirligi", 0.5)),
            bool(girdi.get("celiski_var_mi", False)),
        )
        return EngineResult(
            data=rapor, confidence=rapor.puan,
            explanation=f"Güven %{rapor.puan * 100:.0f} — {rapor.neden}.",
        )
