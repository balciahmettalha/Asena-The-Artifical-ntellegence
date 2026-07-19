"""Yapılandırma yükleyici.

Varsayılan değerler ``default.toml`` içindedir; kullanıcı dosyası verilirse
üzerine birleştirilir (deep merge). Python 3.11+ ile gelen ``tomllib``
kullanılır — harici bağımlılık yoktur.
"""

from __future__ import annotations

import copy
import os
import tomllib
from pathlib import Path
from typing import Any

from asena.core.exceptions import ConfigurationError

_VARSAYILAN_YOL = Path(__file__).with_name("default.toml")


def _derin_birlestir(taban: dict[str, Any], uzerine: dict[str, Any]) -> dict[str, Any]:
    """İki sözlüğü özyinelemeli birleştirir; ``uzerine`` önceliklidir."""
    sonuc = copy.deepcopy(taban)
    for anahtar, deger in uzerine.items():
        if anahtar in sonuc and isinstance(sonuc[anahtar], dict) and isinstance(deger, dict):
            sonuc[anahtar] = _derin_birlestir(sonuc[anahtar], deger)
        else:
            sonuc[anahtar] = copy.deepcopy(deger)
    return sonuc


class Settings:
    """Nokta erişimli, salt-okunur yapılandırma görünümü.

    >>> ayar.get("bellek.kisa_sureli_kapasite")
    25
    """

    def __init__(self, veri: dict[str, Any]) -> None:
        self._veri = veri

    def get(self, yol: str, varsayilan: Any = None) -> Any:
        """Nokta ayrılmış yol ile değer döndürür; yoksa ``varsayilan``."""
        dugum: Any = self._veri
        for parca in yol.split("."):
            if not isinstance(dugum, dict) or parca not in dugum:
                return varsayilan
            dugum = dugum[parca]
        return dugum

    def gerektir(self, yol: str) -> Any:
        """Değer yoksa :class:`ConfigurationError` fırlatır."""
        deger = self.get(yol, None)
        if deger is None:
            raise ConfigurationError(f"Zorunlu yapılandırma eksik: '{yol}'")
        return deger

    def sozluk(self) -> dict[str, Any]:
        """Tam yapılandırmanın derin kopyasını verir."""
        return copy.deepcopy(self._veri)

    def __repr__(self) -> str:  # pragma: no cover
        bolumler = ", ".join(sorted(self._veri))
        return f"<Settings bölümler=[{bolumler}]>"


def load_settings(kullanici_yolu: str | Path | None = None) -> Settings:
    """Varsayılan + (varsa) kullanıcı TOML dosyasını birleştirerek yükler.

    ``ASENA_VERI_DIZINI`` ortam değişkeni tanımlıysa göreli veri yolları
    (veritabanı, günlük, corpus) o dizine bağlanır; böylece sistemin
    tüm kalıcı verisi tek kökte toplanır.
    """
    try:
        with open(_VARSAYILAN_YOL, "rb") as akim:
            taban = tomllib.load(akim)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise ConfigurationError(f"Varsayılan yapılandırma okunamadı: {exc}") from exc

    if kullanici_yolu is not None:
        try:
            with open(kullanici_yolu, "rb") as akim:
                uzerine = tomllib.load(akim)
        except (OSError, tomllib.TOMLDecodeError) as exc:
            raise ConfigurationError(f"Kullanıcı yapılandırması okunamadı: {exc}") from exc
        taban = _derin_birlestir(taban, uzerine)

    veri_koku = os.environ.get("ASENA_VERI_DIZINI")
    if veri_koku:
        kok = Path(veri_koku)
        for yol in ("veritabani.yol", "ogrenme.gunluk_dizini",
                    "egitim.corpus_dizini"):
            dugum = taban
            parcalar = yol.split(".")
            for parca in parcalar[:-1]:
                dugum = dugum.get(parca, {})
            son = parcalar[-1]
            deger = dugum.get(son)
            if isinstance(deger, str) and deger != ":memory:" \
                    and not Path(deger).is_absolute():
                dugum[son] = str(kok / deger)
    return Settings(taban)
