"""Çelişki Avcısı (Contradiction Hunter).

Belirli aralıklarla bilgi tabanını tarayıp gizli çelişkileri bulur:
aynı özne-yüklem çiftinde çok sayıda farklı nesne, düşük güvenli
bilgilerle yüksek güvenli bilgilerin çatışması gibi örüntüleri raporlar.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Callable

from asena.engine.base import BaseEngine, EngineResult


@dataclass
class Suphe:
    """Taramada saptanan şüpheli örüntü."""

    tur: str
    aciklama: str
    ilgili_kimlikler: list[str]


class ContradictionHunter(BaseEngine):
    """Bilgi tabanını düzenli tarayan gizli çelişki avcısı."""

    name = "contradiction_hunter"
    group = "reason"

    def __init__(self, zit_mi: Callable[[str, str], bool] | None = None) -> None:
        super().__init__()
        self._zit_mi = zit_mi or (lambda a, b: False)

    def tara(self, bilgiler: list[dict[str, Any]]) -> list[Suphe]:
        """Tüm aktif bilgileri tarar; şüpheli örüntüleri döndürür."""
        supheler: list[Suphe] = []
        gruplar: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        for b in bilgiler:
            gruplar[(str(b.get("ozne", "")), str(b.get("yuklem", "")))].append(b)

        for (ozne, yuklem), grup in gruplar.items():
            nesneler = {str(g.get("nesne") or "") for g in grup}
            nesneler.discard("")
            # Zıt nesneler
            nesne_liste = sorted(nesneler)
            for i, a in enumerate(nesne_liste):
                for b in nesne_liste[i + 1:]:
                    if self._zit_mi(a, b):
                        supheler.append(Suphe(
                            tur="zit_nesne",
                            aciklama=(
                                f"'{ozne} {yuklem}' için hem '{a}' hem '{b}' "
                                "kayıtlı; bu iki değer zıttır."
                            ),
                            ilgili_kimlikler=[
                                str(g["id"]) for g in grup
                                if str(g.get("nesne") or "") in {a, b}
                            ],
                        ))
            # Güven çatışması: aynı iddianın çok farklı güvenlerle tekrarı
            guvenler = [float(g.get("guven", 1.0)) for g in grup]
            if guvenler and max(guvenler) - min(guvenler) > 0.6 and len(grup) > 1:
                supheler.append(Suphe(
                    tur="guven_cakismasi",
                    aciklama=(
                        f"'{ozne} {yuklem}' kayıtları arasında büyük güven "
                        f"farkı var ({min(guvenler):.2f}–{max(guvenler):.2f})."
                    ),
                    ilgili_kimlikler=[str(g["id"]) for g in grup],
                ))
        return supheler

    def rapor(self, bilgiler: list[dict[str, Any]]) -> str:
        supheler = self.tara(bilgiler)
        if not supheler:
            return "Bilgi tabanında gizli çelişki bulunamadı."
        satirlar = [f"- [{s.tur}] {s.aciklama}" for s in supheler]
        return f"{len(supheler)} şüpheli örüntü bulundu:\n" + "\n".join(satirlar)

    def process(self, girdi: list[dict[str, Any]], **kwargs: Any) -> EngineResult:
        supheler = self.tara(list(girdi))
        return EngineResult(
            data=supheler, confidence=1.0 if not supheler else 0.4,
            explanation=f"{len(supheler)} şüpheli örüntü.",
        )
