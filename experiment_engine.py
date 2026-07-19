"""Üstbiliş (Metacognition).

Sistemin kendi düşünme sürecini değerlendirmesi: "Bu sonuca neden
ulaştım? Başka yöntem daha doğru olur muydu?" Akıl yürütme izini
analiz eder; hangi adımın belirleyici olduğunu ve alternatif
yöntemleri raporlar.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from asena.engine.base import BaseEngine, EngineResult

ALTERNATIF_YONTEMLER: dict[str, str] = {
    "mantık kur": "Benzetimsel yaklaşım da denenebilirdi.",
    "ilişki ara": "Derin nedensellik zinciri kurulabilirdi.",
    "tahmin üret": "Çoklu hipotez karşılaştırması yapılabilirdi.",
    "anla": "Bağlam motoru ile anlam ayrıştırması derinleştirilebilirdi.",
}


@dataclass
class MetakognisyonRaporu:
    belirleyici_adim: str
    zayif_adimlar: list[str]
    alternatifler: list[str]
    ozguven_notu: str
    iz_ozeti: list[tuple[str, str]] = field(default_factory=list)


class Metacognition(BaseEngine):
    """Kendi düşünme sürecini analiz eden motor."""

    name = "metacognition"
    group = "decision"

    def analiz_et(self, adimlar: list[tuple[str, str]],
                  guven: float) -> MetakognisyonRaporu:
        """Akıl yürütme izini değerlendirir."""
        belirleyici = "—"
        for ad, detay in adimlar:
            if ad == "tahmin üret":
                belirleyici = f"{ad}: {detay}"
        zayif = [
            ad for ad, detay in adimlar
            if "bulunamadı" in detay or "üretilemedi" in detay or "Eksik" in detay
        ]
        alternatifler = [
            ALTERNATIF_YONTEMLER[ad] for ad, _ in adimlar
            if ad in ALTERNATIF_YONTEMLER
        ]
        if guven >= 0.8:
            notu = "Süreç sağlıklı; sonuç güçlü kanıta dayanıyor."
        elif guven >= 0.5:
            notu = "Sonuç makul; ancak ek kanıt güveni artırırdı."
        else:
            notu = "Süreç zayıf kaldı; bilgi toplamak veya kullanıcıya sormak gerek."
        return MetakognisyonRaporu(
            belirleyici_adim=belirleyici, zayif_adimlar=zayif,
            alternatifler=alternatifler, ozguven_notu=notu, iz_ozeti=adimlar,
        )

    def process(self, girdi: dict[str, Any], **kwargs: Any) -> EngineResult:
        rapor = self.analiz_et(
            [tuple(a) for a in girdi.get("adimlar", [])],
            float(girdi.get("guven", 0.5)),
        )
        ozet = (
            f"Belirleyici adım: {rapor.belirleyici_adim}; "
            f"zayıf adımlar: {rapor.zayif_adimlar or 'yok'}; "
            f"not: {rapor.ozguven_notu}"
        )
        return EngineResult(data=rapor, explanation=ozet)
