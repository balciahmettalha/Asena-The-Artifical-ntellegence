"""Çelişki Motoru (Contradiction Engine).

Yeni bilgi geldiğinde eski bilgiyle çelişip çelişmediğini denetler.
Çelişki kaynakları: açık olumsuzluk, zıt kavramlar (sıcak/soğuk) ve
aynı özne-yüklem çiftinde birbiriyle bağdaşmayan nesneler.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from asena.engine.base import BaseEngine, EngineResult
from asena.logic.logic_engine import Onerme


@dataclass
class Celiski:
    """Saptanan bir çelişkinin kaydı."""

    yeni: str
    mevcut: str
    tur: str                       # olumsuzluk | zit_kavram | nesne_cakismasi
    aciklama: str


class ContradictionEngine(BaseEngine):
    """Yeni bilgiyi bilgi tabanıyla karşılaştıran motor."""

    name = "contradiction_engine"
    group = "reason"

    def __init__(self, zit_mi: Callable[[str, str], bool] | None = None) -> None:
        super().__init__()
        self._zit_mi = zit_mi or (lambda a, b: False)

    def denetle(self, yeni: Onerme, taban: list[Onerme]) -> list[Celiski]:
        """Yeni önermenin tabanla çelişkilerini döndürür."""
        celiskiler: list[Celiski] = []
        for eski in taban:
            # 1. Açık olumsuzluk: aynı önerme, zıt işaret
            if (
                eski.ozne == yeni.ozne and eski.yuklem == yeni.yuklem
                and eski.nesne == yeni.nesne and eski.olumsuz != yeni.olumsuz
            ):
                celiskiler.append(Celiski(
                    yeni=str(yeni), mevcut=str(eski), tur="olumsuzluk",
                    aciklama="Aynı önermenin olumlu ve olumsuz hâli mevcut.",
                ))
            # 2. Zıt kavramlar: aynı özne, zıt yüklemler
            elif (
                eski.ozne == yeni.ozne and eski.nesne == yeni.nesne
                and not eski.olumsuz and not yeni.olumsuz
                and self._zit_mi(eski.yuklem, yeni.yuklem)
            ):
                celiskiler.append(Celiski(
                    yeni=str(yeni), mevcut=str(eski), tur="zit_kavram",
                    aciklama=f"'{eski.yuklem}' ile '{yeni.yuklem}' zıt kavramlardır.",
                ))
        return celiskiler

    def tutarli_mi(self, yeni: Onerme, taban: list[Onerme]) -> bool:
        return not self.denetle(yeni, taban)

    def process(self, girdi: dict[str, Any], **kwargs: Any) -> EngineResult:
        yeni = Onerme.coz(str(girdi.get("yeni", "")))
        taban = [Onerme.coz(m) for m in girdi.get("taban", [])]
        celiskiler = self.denetle(yeni, taban)
        return EngineResult(
            data=celiskiler, confidence=1.0 if not celiskiler else 0.2,
            explanation=(
                "Çelişki yok." if not celiskiler
                else f"{len(celiskiler)} çelişki: {celiskiler[0].aciklama}"
            ),
        )
