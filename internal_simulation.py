"""İç Tartışma (Internal Discussion).

Sanal uzmanlar (matematik, fizik, mantık) arasında iç tartışma yürütür
ve ortak karara varır. Her uzman görüş bildirir; görüşler ağırlıklandırılıp
uzlaştırılır.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from asena.engine.base import BaseEngine, EngineResult


@dataclass
class UzmanGorusu:
    uzman: str
    gorus: str
    guven: float
    gerekce: str = ""


class InternalDiscussion(BaseEngine):
    """Sanal uzman görüşlerini uzlaştıran motor."""

    name = "internal_discussion"
    group = "governance"

    UZMAN_AGIRLIK: dict[str, float] = {
        "matematik": 1.0, "fizik": 1.0, "mantik": 1.2, "dil": 0.8,
    }

    def __init__(self) -> None:
        super().__init__()
        self._uzmanlar: dict[str, Callable[[Any], UzmanGorusu]] = {}

    def uzman_kaydet(self, alan: str, gorus_uretici: Callable[[Any], UzmanGorusu]) -> None:
        self._uzmanlar[alan] = gorus_uretici

    def tartistir(self, konu: Any) -> dict[str, Any]:
        """Tüm uzmanların görüşünü alıp ortak karar üretir."""
        gorusler: list[UzmanGorusu] = []
        for alan, uretici in self._uzmanlar.items():
            try:
                gorusler.append(uretici(konu))
            except Exception as exc:  # noqa: BLE001
                gorusler.append(UzmanGorusu(alan, "", 0.0, f"hata: {exc!r}"))
        oy: dict[str, float] = {}
        for g in gorusler:
            if g.gorus:
                agirlik = self.UZMAN_AGIRLIK.get(g.uzman, 1.0) * g.guven
                oy[g.gorus] = oy.get(g.gorus, 0.0) + agirlik
        karar = max(oy, key=oy.get) if oy else ""
        return {
            "karar": karar,
            "oy_dagilimi": oy,
            "gorusler": gorusler,
            "uzlasma_var_mi": bool(karar) and len(oy) <= max(1, len(gorusler) // 2 + 1),
        }

    def process(self, girdi: Any, **kwargs: Any) -> EngineResult:
        sonuc = self.tartistir(girdi)
        if not sonuc["karar"]:
            return EngineResult.hata("Uzmanlardan geçerli görüş alınamadı.")
        return EngineResult(
            data=sonuc, confidence=max(sonuc["oy_dagilimi"].values()),
            explanation=f"İç tartışma kararı: {sonuc['karar']}",
        )
