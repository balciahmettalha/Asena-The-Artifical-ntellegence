"""Merak Motoru (Curiosity Engine).

Bilmediği kavramları fark eder ve öğrenme ihtiyacı duyar; ancak yalnızca
kullanıcı onay verirse eyleme geçer (ör. dış kaynaktan araştırma). Onay
olmadan tek yaptığı, ihtiyacı kayda geçirmektir.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from asena.core.consent import Eylem
from asena.core.event_bus import Event
from asena.engine.base import BaseEngine, EngineResult


@dataclass
class MerakKaydi:
    konu: str
    neden: str
    onay_bekliyor: bool = True
    oncelik: float = 0.5


class CuriosityEngine(BaseEngine):
    """Bilinmeyeni tespit edip öğrenme ihtiyacı üreten motor."""

    name = "curiosity_engine"
    group = "learning"

    def __init__(self) -> None:
        super().__init__()
        self.kuyruk: list[MerakKaydi] = []

    def on_bind(self, ctx: Any) -> None:
        ctx.bus.subscribe("bellek.bilinmeyen_kelime", self._bilinmeyen_isle)

    def _bilinmeyen_isle(self, olay: Event) -> None:
        kok = str(olay.payload.get("kok", ""))
        if kok:
            self.fark_et(kok, "Sohbette bilinmeyen kelime geçti.")

    def fark_et(self, konu: str, neden: str, oncelik: float = 0.5) -> MerakKaydi:
        """Öğrenme ihtiyacını kuyruğa ekler."""
        mevcut = next((k for k in self.kuyruk if k.konu == konu), None)
        if mevcut:
            mevcut.oncelik = min(1.0, mevcut.oncelik + 0.1)
            return mevcut
        kayit = MerakKaydi(konu=konu, neden=neden, oncelik=oncelik)
        self.kuyruk.append(kayit)
        return kayit

    def arastirma_istegi(self, konu: str) -> str:
        """Dış kaynak araştırması için onay ister; onay yoksa bildirir."""
        try:
            self.ctx.consent.gerektir(Eylem.INTERNET)
        except Exception:
            return (
                f"'{konu}' hakkında daha fazla öğrenmek isterim; ancak "
                "internet erişimi için onayınız gerekli. Onay verirseniz "
                "araştırma yapabilirim."
            )
        return f"'{konu}' için araştırma onayı mevcut."

    def siradaki_merak(self) -> MerakKaydi | None:
        """En yüksek öncelikli bekleyen merak kaydı."""
        bekleyen = [k for k in self.kuyruk if k.onay_bekliyor]
        return max(bekleyen, key=lambda k: k.oncelik, default=None)

    def process(self, girdi: dict[str, Any], **kwargs: Any) -> EngineResult:
        kayit = self.fark_et(
            str(girdi.get("konu", "")), str(girdi.get("neden", "")),
            float(girdi.get("oncelik", 0.5)),
        )
        return EngineResult(
            data=kayit,
            explanation=f"'{kayit.konu}' öğrenme ihtiyacı kaydedildi.",
        )
