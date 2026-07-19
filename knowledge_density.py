"""Çoklu Hipotez (Multiple Hypotheses).

Tek cevap yerine en çok 5 ihtimal üretir, her birini kanıt gücüyle
skorlar ve en mantıklısını seçer. Hipotezler; doğrudan bilgi, çıkarım,
benzetim ve varsayım kaynaklarından beslenir.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from asena.engine.base import BaseEngine, EngineResult


@dataclass
class Hipotez:
    metin: str
    kaynak: str                    # bilgi | cikarim | benzetim | varsayim
    skor: float = 0.0


class MultipleHypotheses(BaseEngine):
    """Soru için çoklu hipotez üretip sıralayan motor."""

    name = "multiple_hypotheses"
    group = "decision"

    KAYNAK_AGIRLIK: dict[str, float] = {
        "bilgi": 1.0, "cikarim": 0.8, "benzetim": 0.6, "varsayim": 0.4,
    }

    def __init__(self, en_cok: int = 5) -> None:
        super().__init__()
        self.en_cok = en_cok

    def uret(self, soru: str,
             kaynaklar: dict[str, list[str]] | None = None,
             skorlayici: Callable[[str, str], float] | None = None) -> list[Hipotez]:
        """Kaynaklardan hipotezler üretir ve skorlar."""
        kaynaklar = kaynaklar or {}
        hipotezler: list[Hipotez] = []
        for kaynak, metinler in kaynaklar.items():
            agirlik = self.KAYNAK_AGIRLIK.get(kaynak, 0.3)
            for metin in metinler:
                ek = skorlayici(soru, metin) if skorlayici else 0.0
                hipotezler.append(
                    Hipotez(metin=metin, kaynak=kaynak,
                            skor=round(min(1.0, agirlik + ek), 3))
                )
        hipotezler.sort(key=lambda h: -h.skor)
        return hipotezler[: self.en_cok]

    def en_iyisi(self, hipotezler: list[Hipotez]) -> Hipotez | None:
        return hipotezler[0] if hipotezler else None

    def process(self, girdi: dict[str, Any], **kwargs: Any) -> EngineResult:
        hipotezler = self.uret(
            str(girdi.get("soru", "")), girdi.get("kaynaklar"),
        )
        en_iyi = self.en_iyisi(hipotezler)
        if en_iyi is None:
            return EngineResult.hata("Hipotez üretilemedi.")
        return EngineResult(
            data={"en_iyi": en_iyi, "tumu": hipotezler},
            confidence=en_iyi.skor,
            explanation=f"En mantıklı hipotez ({en_iyi.kaynak}): {en_iyi.metin}",
        )
