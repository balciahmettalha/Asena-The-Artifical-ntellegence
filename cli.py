"""Eklenti sistemi — ASENA'nın genişletilebilirlik motoru.

Üçüncü taraf eklentiler :class:`AsenaPlugin` sözleşmesini uygular.
Bir eklenti dosyası yüklemek Python kodu çalıştırmak demektir; bu yüzden
:meth:`PluginSystem.dizinden_yukle` çağrısı :class:`Eylem.KOD_CALISTIRMA`
onayı olmadan hiçbir dosyayı içe aktarmaz (onay ilkesi).

Eklenti dosyası sözleşmesi::

    # benim_eklentim.py
    from asena.plugins import AsenaPlugin

    class BenimEklentim(AsenaPlugin):
        ad = "benim_eklentim"
        surum = "1.0.0"
        aciklama = "Örnek eklenti"

        def baglan(self, ctx):
            self.ctx = ctx

        def kapat(self):
            pass

    def eklenti_olustur():          # zorunlu fabrika
        return BenimEklentim()
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

from asena.core.consent import Eylem
from asena.core.exceptions import EngineError
from asena.engine.base import BaseEngine, EngineContext, EngineResult


class AsenaPlugin:
    """Eklentilerin uyguladığı sözleşme (temel sınıf).

    Attributes:
        ad: Eklentinin benzersiz adı.
        surum: Sürüm dizgesi (``major.minor.patch``).
        aciklama: Türkçe kısa tanım.
    """

    ad: str = "isimsiz"
    surum: str = "0.0.0"
    aciklama: str = ""

    def baglan(self, ctx: EngineContext) -> None:  # pragma: no cover — sözleşme
        """Eklenti sisteme bağlanırken çağrılır."""
        raise NotImplementedError

    def kapat(self) -> None:  # pragma: no cover — sözleşme
        """Eklenti kaldırılırken çağrılır."""
        raise NotImplementedError


class PluginSystem(BaseEngine):
    """Eklentileri kaydeder, doğrular, yükler ve kaldırır."""

    name = "plugin_system"
    group = "genisletilebilirlik"

    def __init__(self) -> None:
        super().__init__()
        self._eklentiler: dict[str, AsenaPlugin] = {}

    # -------------------------------------------------------------- yönetim
    def ekle(self, eklenti: AsenaPlugin) -> None:
        """Eklentiyi doğrular ve sisteme bağlar."""
        self._dogrula(eklenti)
        if eklenti.ad in self._eklentiler:
            raise EngineError(f"Eklenti zaten yüklü: '{eklenti.ad}'")
        eklenti.baglan(self.ctx)
        self._eklentiler[eklenti.ad] = eklenti
        _yayinla(self.ctx.bus, "eklenti.yuklendi", {
            "ad": eklenti.ad, "surum": eklenti.surum,
        })

    def kaldir(self, ad: str) -> None:
        """Eklentiyi kapatır ve kayıttan siler."""
        eklenti = self._eklentiler.pop(ad, None)
        if eklenti is None:
            raise EngineError(f"Eklenti bulunamadı: '{ad}'")
        eklenti.kapat()
        _yayinla(self.ctx.bus, "eklenti.kaldirildi", {"ad": ad})

    def getir(self, ad: str) -> AsenaPlugin:
        try:
            return self._eklentiler[ad]
        except KeyError as exc:
            raise EngineError(f"Eklenti bulunamadı: '{ad}'") from exc

    def liste(self) -> list[dict[str, str]]:
        """Yüklü eklentilerin özet listesini döndürür."""
        return [
            {"ad": e.ad, "surum": e.surum, "aciklama": e.aciklama}
            for e in sorted(self._eklentiler.values(), key=lambda x: x.ad)
        ]

    # -------------------------------------------------------------- yükleme
    def dizinden_yukle(self, dizin: str | Path) -> list[str]:
        """Dizindeki ``*.py`` eklenti dosyalarını yükler.

        Kod çalıştırma onayı gerektirir; onay yoksa
        :class:`ConsentRequiredError` fırlatılır ve hiçbir dosya
        içe aktarılmaz.

        Returns:
            Başarıyla yüklenen eklenti adları.
        """
        self.ctx.consent.gerektir(Eylem.KOD_CALISTIRMA)
        kok = Path(dizin)
        if not kok.is_dir():
            raise EngineError(f"Eklenti dizini yok: '{kok}'")
        yuklenen: list[str] = []
        for dosya in sorted(kok.glob("*.py")):
            if dosya.name.startswith("_"):
                continue
            eklenti = self._dosyadan_uret(dosya)
            if eklenti.ad in self._eklentiler:
                continue
            self.ekle(eklenti)
            yuklenen.append(eklenti.ad)
        return yuklenen

    def _dosyadan_uret(self, dosya: Path) -> AsenaPlugin:
        """Tek dosyadan eklenti örneği üretir."""
        modul_adi = f"asena_eklenti_{dosya.stem}"
        spec = importlib.util.spec_from_file_location(modul_adi, dosya)
        if spec is None or spec.loader is None:
            raise EngineError(f"Eklenti yüklenemedi: '{dosya}'")
        modul = importlib.util.module_from_spec(spec)
        try:
            sys.modules[modul_adi] = modul
            spec.loader.exec_module(modul)
        except Exception as exc:  # noqa: BLE001 — eklenti hatası sarmalanır
            sys.modules.pop(modul_adi, None)
            raise EngineError(
                f"Eklenti '{dosya.name}' çalıştırılırken hata: {exc}"
            ) from exc
        fabrika = getattr(modul, "eklenti_olustur", None)
        if not callable(fabrika):
            sys.modules.pop(modul_adi, None)
            raise EngineError(
                f"Eklenti '{dosya.name}' içinde 'eklenti_olustur' fabrikası yok."
            )
        eklenti = fabrika()
        self._dogrula(eklenti)
        return eklenti

    @staticmethod
    def _dogrula(eklenti: Any) -> None:
        """Eklentinin sözleşmeye uyduğunu denetler."""
        for nitelik in ("ad", "surum", "aciklama", "baglan", "kapat"):
            if not hasattr(eklenti, nitelik):
                raise EngineError(
                    f"Eklenti sözleşmeye uymuyor: '{nitelik}' eksik."
                )
        if not isinstance(eklenti.ad, str) or not eklenti.ad.strip():
            raise EngineError("Eklenti adı boş olamaz.")

    # ---------------------------------------------------------------- motor
    def process(self, girdi: Any = None, **kwargs: Any) -> EngineResult:
        return EngineResult(
            data=self.liste(),
            explanation=f"{len(self._eklentiler)} eklenti yüklü.",
        )


def _yayinla(bus: Any, ad: str, payload: dict[str, Any]) -> None:
    """Modül içi olay yayınlama kısayolu."""
    from asena.core.event_bus import Event

    bus.publish(Event(name=ad, payload=payload, source="plugin_system"))

    def shutdown(self) -> None:
        for ad in list(self._eklentiler):
            try:
                self.kaldir(ad)
            except EngineError:
                continue
