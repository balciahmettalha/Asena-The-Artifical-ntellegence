"""Kendi kendine genişleme motoru.

ASENA eksik gördüğü bir yeteneği kendisi kodlayamaz; ama sözleşmeye uygun
bir eklenti iskeleti üreterek kullanıcıya hazır zemin sunar. İskelet dosya
yazımı :class:`Eylem.DOSYA_YAZMA` onayı olmadan asla yapılmaz.

Ayrıca sisteme kayıtlı motor gruplarını tarayarak hangi yeteneklerin
eklentiyle genişletilebileceğine dair Türkçe bir çözümleme sunar.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from asena.core.consent import Eylem
from asena.core.exceptions import EngineError
from asena.engine.base import BaseEngine, EngineResult

#: Üretilen eklenti iskeletinin şablonu (sözleşmeyle bire bir uyumlu).
ISKELET_SABLONU = '''"""{ad} — ASENA eklentisi.

Bu iskelet SelfExtension motoru tarafından üretildi.
"""

from __future__ import annotations

from asena.engine.base import EngineContext
from asena.plugins import AsenaPlugin


class {sinif}(AsenaPlugin):
    ad = "{ad}"
    surum = "0.1.0"
    aciklama = "{aciklama}"

    def baglan(self, ctx: EngineContext) -> None:
        self.ctx = ctx

    def kapat(self) -> None:
        pass


def eklenti_olustur() -> {sinif}:
    return {sinif}()
'''


class SelfExtension(BaseEngine):
    """Eklenti iskeleti üretir ve genişleme önerileri sunar."""

    name = "self_extension"
    group = "genisletilebilirlik"

    # ------------------------------------------------------------ üretim
    def iskelet_uret(self, ad: str, hedef_dizin: str | Path,
                     aciklama: str = "") -> Path:
        """Sözleşmeye uygun eklenti iskeletini dosyaya yazar.

        Dosya yazma onayı gerektirir; onay yoksa
        :class:`ConsentRequiredError` fırlatılır.

        Returns:
            Yazılan dosyanın yolu.
        """
        self.ctx.consent.gerektir(Eylem.DOSYA_YAZMA)
        temiz = "".join(c if c.isalnum() or c == "_" else "_" for c in ad.strip())
        if not temiz or temiz[0].isdigit():
            raise EngineError(f"Geçersiz eklenti adı: '{ad}'")
        sinif = "".join(parca.capitalize() for parca in temiz.split("_"))
        dizin = Path(hedef_dizin)
        dizin.mkdir(parents=True, exist_ok=True)
        dosya = dizin / f"{temiz}.py"
        if dosya.exists():
            raise EngineError(f"Dosya zaten var: '{dosya}'")
        dosya.write_text(
            ISKELET_SABLONU.format(
                ad=temiz, sinif=sinif,
                aciklama=aciklama or f"{temiz} eklentisi",
            ),
            encoding="utf-8",
        )
        _yayinla(self.ctx.bus, "eklenti.iskelet_uretildi", {
            "ad": temiz, "dosya": str(dosya),
        })
        return dosya

    # ---------------------------------------------------------- çözümleme
    def yetenek_analizi(self) -> list[str]:
        """Kayıtlı motor gruplarına bakarak genişleme önerileri üretir."""
        kayitli = self.ctx.container.resolve("engine_registry")
        gruplar = {m.group for m in (kayitli.get(ad) for ad in kayitli.names())}
        oneriler: list[str] = []
        adaylar: dict[str, str] = {
            "dil": "Yeni dil desteği (ör. İngilizce sözdizimi çözümleyici) eklentisi.",
            "modul": "Yeni uzmanlık modülü (kimya, biyoloji, tarih) eklentisi.",
            "dis_api": "Dış veri kaynağı bağlayıcısı eklentisi (onay ilkesiyle).",
            "arayuz": "Yeni kullanıcı arayüzü (web, ses) eklentisi.",
        }
        for grup, oneri in adaylar.items():
            if grup not in gruplar:
                oneriler.append(oneri)
        if not oneriler:
            oneriler.append(
                "Çekirdek gruplar tam; eklentiyle yeni uzmanlık alanı "
                "(modül grubu) veya arayüz eklenebilir."
            )
        return oneriler

    # ---------------------------------------------------------------- motor
    def process(self, girdi: Any = None, **kwargs: Any) -> EngineResult:
        ad = kwargs.get("ad")
        hedef = kwargs.get("hedef_dizin")
        if ad and hedef:
            dosya = self.iskelet_uret(str(ad), hedef,
                                      str(kwargs.get("aciklama", "")))
            return EngineResult(
                data={"dosya": str(dosya)},
                explanation=f"'{ad}' eklenti iskeleti üretildi: {dosya}",
            )
        oneriler = self.yetenek_analizi()
        return EngineResult(
            data={"oneriler": oneriler},
            explanation=f"{len(oneriler)} genişleme önerisi üretildi.",
        )


def _yayinla(bus: Any, ad: str, payload: dict[str, Any]) -> None:
    """Modül içi olay yayınlama kısayolu."""
    from asena.core.event_bus import Event

    bus.publish(Event(name=ad, payload=payload, source="self_extension"))
