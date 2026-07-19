"""Uzun Vadeli Proje İzleyici (Long-term Project Tracker).

Haftalar süren projeleri unutmadan takip eder. Projeler JSON dosyasında
kalıcıdır; sistem yeniden başlatıldığında kaldığı yerden devam eder.
Dosya yazımı yalnızca proje veri dizinine yapılır (harici eylem değildir).
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from asena.engine.base import BaseEngine, EngineResult


@dataclass
class Proje:
    ad: str
    olusturma: float = field(default_factory=time.time)
    kilometre_taslari: list[dict[str, Any]] = field(default_factory=list)
    durum: str = "aktif"             # aktif | beklemede | tamamlandi
    notlar: list[str] = field(default_factory=list)


class ProjectTracker(BaseEngine):
    """Uzun soluklu projeleri kalıcı olarak izleyen motor."""

    name = "project_tracker"
    group = "planning"

    def __init__(self, dosya: str | Path | None = None) -> None:
        super().__init__()
        self._dosya = Path(dosya) if dosya else None
        self.projeler: dict[str, Proje] = {}
        if self._dosya and self._dosya.exists():
            self._yukle()

    # ------------------------------------------------------------------ kalıcılık
    def _yukle(self) -> None:
        try:
            veri = json.loads(self._dosya.read_text(encoding="utf-8"))  # type: ignore[union-attr]
            for ad, kayit in veri.items():
                self.projeler[ad] = Proje(**kayit)
        except (OSError, json.JSONDecodeError, TypeError):
            self.projeler = {}

    def _kaydet(self) -> None:
        if self._dosya is None:
            return
        self._dosya.parent.mkdir(parents=True, exist_ok=True)
        veri = {ad: asdict(p) for ad, p in self.projeler.items()}
        self._dosya.write_text(
            json.dumps(veri, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    # ------------------------------------------------------------------ izleme
    def proje_ekle(self, ad: str) -> Proje:
        proje = self.projeler.get(ad) or Proje(ad=ad)
        self.projeler[ad] = proje
        self._kaydet()
        return proje

    def kilometre_tasi_ekle(self, ad: str, tanim: str) -> None:
        proje = self.proje_ekle(ad)
        proje.kilometre_taslari.append(
            {"tanim": tanim, "zaman": time.time(), "tamam": False}
        )
        self._kaydet()

    def kilometre_tasi_tamamla(self, ad: str, tanim: str) -> bool:
        proje = self.projeler.get(ad)
        if proje is None:
            return False
        for tas in proje.kilometre_taslari:
            if tas["tanim"] == tanim:
                tas["tamam"] = True
                self._kaydet()
                return True
        return False

    def durum_raporu(self, ad: str) -> str:
        proje = self.projeler.get(ad)
        if proje is None:
            return f"'{ad}' adlı proje kayıtlı değil."
        tamam = sum(1 for t in proje.kilometre_taslari if t["tamam"])
        toplam = len(proje.kilometre_taslari)
        gun = (time.time() - proje.olusturma) / 86400
        return (
            f"Proje '{ad}': {proje.durum}; {tamam}/{toplam} kilometre taşı; "
            f"{gun:.0f} gündür izleniyor."
        )

    def aktif_projeler(self) -> list[str]:
        return [ad for ad, p in self.projeler.items() if p.durum == "aktif"]

    def process(self, girdi: dict[str, Any], **kwargs: Any) -> EngineResult:
        islem = girdi.get("islem", "rapor")
        if islem == "ekle":
            proje = self.proje_ekle(str(girdi["ad"]))
            return EngineResult(data=proje, explanation=f"Proje eklendi: {proje.ad}")
        return EngineResult(
            data=self.durum_raporu(str(girdi.get("ad", ""))),
            explanation="Proje durum raporu.",
        )
