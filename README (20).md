"""Akıl Yürütme Motoru (Reason Engine).

Her yanıttan önce çok adımlı akıl yürütme uygular:

``anla → parçala → mantık kur → ilişki ara → eksik bilgi bul →
tahmin üret → kontrol et → yaz``

Her adım izlenebilir bir kayda (AkilYurutmeIz) işlenir; böylece sistem
sonucuna nasıl ulaştığını açıklayabilir (metakognisyon altyapısı).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from asena.engine.base import BaseEngine, EngineResult
from asena.logic.logic_engine import Kural, LogicEngine, Onerme


@dataclass
class AkilYurutmeIz:
    """Çok adımlı akıl yürütmenin izlenebilir kaydı."""

    adimlar: list[tuple[str, str]] = field(default_factory=list)
    sonuc: str = ""
    guven: float = 0.0
    eksik_bilgi: list[str] = field(default_factory=list)

    def adim(self, ad: str, detay: str) -> None:
        self.adimlar.append((ad, detay))

    def metin(self) -> str:
        satirlar = [f"{i + 1}. [{ad}] {detay}" for i, (ad, detay) in enumerate(self.adimlar)]
        return "\n".join(satirlar)


class ReasonEngine(BaseEngine):
    """Çok adımlı akıl yürütme hattını yöneten motor."""

    name = "reason_engine"
    group = "reason"
    dependencies = ("logic_engine",)

    def __init__(self, mantik: LogicEngine | None = None,
                 en_cok_adim: int = 8) -> None:
        super().__init__()
        self.mantik = mantik or LogicEngine()
        self.en_cok_adim = en_cok_adim

    # ------------------------------------------------------------------ adımlar
    def dusun(self, soru: str, onermeler: list[str],
              kurallar: list[str] | None = None,
              iliskili_bilgiler: list[str] | None = None) -> AkilYurutmeIz:
        """Tam akıl yürütme hattını çalıştırır."""
        iz = AkilYurutmeIz()
        kurallar = kurallar or []
        iliskili_bilgiler = iliskili_bilgiler or []

        # 1. anla
        iz.adim("anla", f"Soru: {soru}")
        # 2. parçala
        o_nesneler = [Onerme.coz(m) for m in onermeler]
        iz.adim("parçala", f"{len(o_nesneler)} önerme, {len(kurallar)} kural ayrıştırıldı.")
        # 3. mantık kur
        k_nesneler = [Kural.coz(k) for k in kurallar if "=>" in k]
        tumu = self.mantik.modus_ponens(o_nesneler, k_nesneler,
                                        tur_siniri=self.en_cok_adim)
        turetilen = tumu[len(o_nesneler):]
        iz.adim("mantık kur", f"{len(turetilen)} yeni önerme türetildi.")
        # 4. ilişki ara
        if iliskili_bilgiler:
            iz.adim("ilişki ara", f"{len(iliskili_bilgiler)} ilişkili bilgi bulundu.")
        else:
            iz.adim("ilişki ara", "Bellekte ilişkili bilgi bulunamadı.")
        # 5. eksik bilgi bul
        soru_kokleri = {k for k in soru.lower().split() if len(k) > 2}
        bilinen = {o.ozne for o in tumu} | {o.nesne for o in tumu if o.nesne}
        eksik = sorted(soru_kokleri - bilinen - {"nedir", "neden", "nasıl", "mi", "mı"})
        iz.eksik_bilgi = eksik
        if eksik:
            iz.adim("eksik bilgi bul", f"Eksik: {', '.join(eksik)}")
        # 6. tahmin üret
        if turetilen:
            iz.sonuc = str(turetilen[-1])
            iz.guven = 0.8
        elif iliskili_bilgiler:
            iz.sonuc = iliskili_bilgiler[0]
            iz.guven = 0.5
        else:
            iz.sonuc = ""
            iz.guven = 0.2
        iz.adim("tahmin üret", iz.sonuc or "Tahmin üretilemedi.")
        # 7. kontrol et
        celiski = [o for o in tumu if not self.mantik.tutarli_mi(o, tumu)]
        if celiski:
            iz.guven *= 0.5
            iz.adim("kontrol et", f"{len(celiski)} çelişki bulundu; güven düşürüldü.")
        else:
            iz.adim("kontrol et", "Çelişki bulunamadı.")
        # 8. yaz
        iz.adim("yaz", f"Güven: %{iz.guven * 100:.0f}")
        return iz

    def process(self, girdi: dict[str, Any], **kwargs: Any) -> EngineResult:
        iz = self.dusun(
            str(girdi.get("soru", "")),
            list(girdi.get("onermeler", [])),
            list(girdi.get("kurallar", [])),
            list(girdi.get("iliskili_bilgiler", [])),
        )
        return EngineResult(
            data=iz, confidence=iz.guven,
            explanation=iz.sonuc or "Sonuca ulaşılamadı.",
        )
