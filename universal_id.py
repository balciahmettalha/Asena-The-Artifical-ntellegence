"""Zaman Algısı (Time Perception).

Geçmiş / şimdi / gelecek ayrımı yapar ve zamana bağlı çıkarımlar üretir:
"bugün yağmur → yarın şemsiye gerekebilir". Göreli gün ifadelerini
(dün, bugün, yarın) tarihe çevirir.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from asena.engine.base import BaseEngine, EngineResult

GORELI_GUNLER: dict[str, int] = {
    "dün": -1, "bugün": 0, "yarın": 1, "öbürgün": 2,
}


class TimePerception(BaseEngine):
    """Zamansal bağlamı çözümleyen motor."""

    name = "time_perception"
    group = "planning"

    @staticmethod
    def gun_coz(ifade: str, referans: date | None = None) -> date | None:
        """Göreli gün ifadesini tarihe çevirir."""
        referans = referans or date.today()
        fark = GORELI_GUNLER.get(ifade.strip().lower())
        return referans + timedelta(days=fark) if fark is not None else None

    @staticmethod
    def donem(metin: str) -> str:
        """Metnin zaman kipini belirler: gecmis | simdi | gelecek."""
        kucuk = metin.lower()
        if any(g in kucuk for g in ("yarın", "öbürgün", "gelecek", "-acak", "-ecek")):
            return "gelecek"
        if any(g in kucuk for g in ("dün", "geçen", "-dı", "-di", "-mış", "-miş")):
            return "gecmis"
        return "simdi"

    def oneri_uret(self, olay: str, gun_ifadesi: str) -> str:
        """Zamana bağlı öneri üretir: bugün yağmur → yarın şemsiye."""
        donem_gunu = self.gun_coz(gun_ifadesi)
        if olay == "yağmur" and gun_ifadesi in {"bugün", "yarın"}:
            return (
                f"{gun_ifadesi.capitalize()} yağmur bekleniyorsa "
                f"{(donem_gunu + timedelta(days=1)).isoformat() if donem_gunu else 'ertesi gün'} "
                "için şemsiye almak mantıklı olur."
            )
        return f"'{olay}' için zamana bağlı özel bir öneri bulunmuyor."

    def process(self, girdi: dict[str, Any], **kwargs: Any) -> EngineResult:
        metin = str(girdi.get("metin", ""))
        donem = self.donem(metin)
        return EngineResult(
            data={"donem": donem}, explanation=f"Metin '{donem}' dönemine ait."
        )
