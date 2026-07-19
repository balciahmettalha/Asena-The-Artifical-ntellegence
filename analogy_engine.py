"""Öğrenme Günlüğü (Learning Journal).

Günlük öğrenme raporu tutar: yeni kelime, ilişki, kural ve kavram
sayıları. Olay veri yolundaki öğrenme olaylarına abone olarak kendiliğinden
işler; kayıtlar veritabanında saklanır.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from asena.core.event_bus import Event
from asena.database.repositories import JournalRepository
from asena.engine.base import BaseEngine, EngineResult

_OLAY_ALAN = {
    "ogrenme.kelime": "yeni_kelime",
    "ogrenme.iliski": "yeni_iliski",
    "ogrenme.kural": "yeni_kural",
    "ogrenme.kavram": "yeni_kavram",
}


class LearningJournal(BaseEngine):
    """Günlük öğrenme istatistiklerini kaydeden motor."""

    name = "learning_journal"
    group = "learning"

    def __init__(self, repo: JournalRepository | None = None) -> None:
        super().__init__()
        self._repo = repo
        self._yerel: dict[str, dict[str, int]] = {}

    def on_bind(self, ctx: Any) -> None:
        for olay in _OLAY_ALAN:
            ctx.bus.subscribe(olay, self._olay_isle)

    def _olay_isle(self, olay: Event) -> None:
        alan = _OLAY_ALAN.get(olay.name)
        if alan:
            self.artir(alan)

    def artir(self, alan: str, miktar: int = 1) -> None:
        """Bugünün sayacını artırır."""
        bugun = date.today().isoformat()
        if self._repo is not None:
            self._repo.gunluk_artir(bugun, alan, miktar)
        else:
            gunluk = self._yerel.setdefault(bugun, {})
            gunluk[alan] = gunluk.get(alan, 0) + miktar

    def gunluk_rapor(self, tarih: str | None = None) -> str:
        """Belirli bir günün raporunu üretir."""
        gun = tarih or date.today().isoformat()
        if self._repo is not None:
            kayit = self._repo.gunluk(gun) or {}
        else:
            kayit = self._yerel.get(gun, {})
        return (
            f"{gun} öğrenme raporu: "
            f"{kayit.get('yeni_kelime', 0)} yeni kelime, "
            f"{kayit.get('yeni_iliski', 0)} yeni ilişki, "
            f"{kayit.get('yeni_kural', 0)} yeni kural, "
            f"{kayit.get('yeni_kavram', 0)} yeni kavram."
        )

    def process(self, girdi: Any = None, **kwargs: Any) -> EngineResult:
        rapor = self.gunluk_rapor()
        return EngineResult(data=rapor, explanation=rapor)
