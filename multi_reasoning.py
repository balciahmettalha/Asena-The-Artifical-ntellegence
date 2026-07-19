"""Dikkat Sistemi (Attention System).

Binlerce bilgi arasından yalnızca en ilgili ~25 tanesini çalışma
belleğine alır. Skor; ilgililik (bağlamla ilişki), önem puanı ve
yenilik (recency) bileşenlerinden hesaplanır.
"""

from __future__ import annotations

import time
from typing import Any, Iterable

from asena.engine.base import BaseEngine, EngineResult
from asena.memory.workspace import Workspace


class AttentionSystem(BaseEngine):
    """Aday bilgileri skorlayıp çalışma belleğine seçen motor."""

    name = "attention"
    group = "memory"

    def __init__(self, workspace: Workspace | None = None,
                 kapasite: int = 25) -> None:
        super().__init__()
        self.workspace = workspace or Workspace(kapasite)
        self.kapasite = kapasite

    @staticmethod
    def skor(ilgililik: float, onem: float, yenilik: float) -> float:
        """Bileşik dikkat skoru: 0.5·ilgi + 0.3·önem + 0.2·yenilik."""
        return 0.5 * ilgililik + 0.3 * onem + 0.2 * yenilik

    def sec(self, adaylar: Iterable[dict[str, Any]],
            baglam: set[str] | None = None) -> list[dict[str, Any]]:
        """Adayları skorlar, en yüksek ``kapasite`` kadarını seçer.

        Her aday: ``{"anahtar", "deger", "onem", "zaman", "kavramlar"}``.
        """
        baglam = baglam or set()
        simdi = time.time()
        skorlu: list[tuple[float, dict[str, Any]]] = []
        for aday in adaylar:
            kavramlar = set(aday.get("kavramlar", ()))
            ilgililik = min(1.0, len(kavramlar & baglam) / 3) if baglam else 0.3
            onem = min(1.0, float(aday.get("onem", 1.0)) / 5)
            yas = max(0.0, simdi - float(aday.get("zaman", simdi)))
            yenilik = 1.0 / (1.0 + yas / 3600)
            s = self.skor(ilgililik, onem, yenilik)
            skorlu.append((s, aday))
        skorlu.sort(key=lambda x: -x[0])
        secilenler = [aday for _, aday in skorlu[: self.kapasite]]
        for s, aday in skorlu[: self.kapasite]:
            self.workspace.ekle(
                str(aday["anahtar"]), aday.get("deger"),
                guc=s, onem=float(aday.get("onem", 1.0)),
            )
        return secilenler

    def process(self, girdi: dict[str, Any], **kwargs: Any) -> EngineResult:
        secilen = self.sec(
            girdi.get("adaylar", []), set(girdi.get("baglam", set()))
        )
        return EngineResult(
            data=secilen,
            explanation=f"{len(secilen)} öğe çalışma belleğine alındı.",
        )
