"""Amaç Motoru (Goal Engine).

Kendine görev planı oluşturur: ``oyun yap → motor seç → dosyaları
oluştur → kod yaz → test → düzelt``. Hedefler hiyerarşiktir; her hedefin
durumu (bekliyor, sürüyor, tamamlandı) izlenir.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from asena.engine.base import BaseEngine, EngineResult

# Bilinen hedef türleri için hazır adım şablonları
HEDEF_SABLONLARI: dict[str, list[str]] = {
    "oyun yap": ["motor seç", "dosyaları oluştur", "kod yaz", "test et", "hataları düzelt"],
    "kod yaz": ["gereksinimi anla", "tasarım yap", "kodu yaz", "test et"],
    "öğren": ["kaynak belirle", "veriyi işle", "ilişkilendir", "doğrula", "kaydet"],
    "proje geliştir": ["planla", "modülleri böl", "uygula", "bütünle", "doğrula"],
    "araştır": ["soruyu netleştir", "bilgi topla", "karşılaştır", "sonuç çıkar"],
}


@dataclass
class Hedef:
    ad: str
    adimlar: list[str] = field(default_factory=list)
    durum: str = "bekliyor"          # bekliyor | suruyor | tamamlandi
    once: str | None = None          # üst hedef
    tamamlanan: int = 0

    @property
    def ilerleme(self) -> float:
        return self.tamamlanan / len(self.adimlar) if self.adimlar else 0.0


class GoalEngine(BaseEngine):
    """Hedef oluşturan ve izleyen motor."""

    name = "goal_engine"
    group = "planning"

    def __init__(self) -> None:
        super().__init__()
        self.hedefler: dict[str, Hedef] = {}

    def hedef_olustur(self, ad: str, adimlar: list[str] | None = None,
                      once: str | None = None) -> Hedef:
        """Yeni hedef kurar; bilinen türse şablondan adımlar üretir."""
        if adimlar is None:
            adimlar = next(
                (list(s) for anahtar, s in HEDEF_SABLONLARI.items()
                 if anahtar in ad.lower()),
                ["hedefi analiz et", "adımları belirle", "uygula", "doğrula"],
            )
        hedef = Hedef(ad=ad, adimlar=adimlar, once=once)
        self.hedefler[ad] = hedef
        return hedef

    def baslat(self, ad: str) -> None:
        if ad in self.hedefler:
            self.hedefler[ad].durum = "suruyor"

    def adim_tamamla(self, ad: str) -> Hedef | None:
        hedef = self.hedefler.get(ad)
        if hedef is None:
            return None
        hedef.tamamlanan = min(len(hedef.adimlar), hedef.tamamlanan + 1)
        if hedef.tamamlanan >= len(hedef.adimlar):
            hedef.durum = "tamamlandi"
        return hedef

    def siradaki_adim(self, ad: str) -> str | None:
        hedef = self.hedefler.get(ad)
        if hedef is None or hedef.tamamlanan >= len(hedef.adimlar):
            return None
        return hedef.adimlar[hedef.tamamlanan]

    def aktif_hedefler(self) -> list[Hedef]:
        return [h for h in self.hedefler.values() if h.durum != "tamamlandi"]

    def process(self, girdi: dict[str, Any], **kwargs: Any) -> EngineResult:
        islem = girdi.get("islem", "olustur")
        if islem == "olustur":
            hedef = self.hedef_olustur(str(girdi["ad"]), girdi.get("adimlar"))
            return EngineResult(
                data=hedef,
                explanation=f"Hedef kuruldu: {hedef.ad} ({len(hedef.adimlar)} adım).",
            )
        if islem == "adim_tamamla":
            hedef = self.adim_tamamla(str(girdi["ad"]))
            if hedef is None:
                return EngineResult.hata("Hedef bulunamadı.")
            return EngineResult(
                data=hedef,
                explanation=f"İlerleme: %{hedef.ilerleme * 100:.0f} ({hedef.durum}).",
            )
        aktif = self.aktif_hedefler()
        return EngineResult(data=aktif, explanation=f"{len(aktif)} aktif hedef.")
