"""Kullanıcı onayı yöneticisi — ASENA'nın güven ilkesinin çekirdeği.

Kullanıcı onayı olmadan hiçbir harici eylem (internet erişimi, dosya yazımı,
kod çalıştırma, sistem çağrısı) başlatılmaz. İzin verilmeyen eylem denemesi
:class:`ConsentRequiredError` fırlatır; çağıran taraf kullanıcıdan açık onay
isteyebilir.
"""

from __future__ import annotations

import threading
from enum import Enum

from asena.core.exceptions import ConsentRequiredError


class Eylem(str, Enum):
    """Onay gerektiren harici eylem türleri."""

    INTERNET = "internet"
    DOSYA_YAZMA = "dosya_yazma"
    DOSYA_OKUMA_DISI = "dosya_okuma_disi"  # proje dizini dışı okuma
    KOD_CALISTIRMA = "kod_calistirma"
    SISTEM_CAGRISI = "sistem_cagrisi"
    EGITIM_VERISI = "egitim_verisi"  # eğitim için dış kaynaktan veri alma


class ConsentManager:
    """Oturum boyunca verilen onayları tutar ve denetler."""

    def __init__(self) -> None:
        self._izinler: set[Eylem] = set()
        self._kilit = threading.RLock()

    def izin_ver(self, eylem: Eylem) -> None:
        """Kullanıcının açık onayını kaydeder."""
        with self._kilit:
            self._izinler.add(eylem)

    def izin_geri_al(self, eylem: Eylem) -> None:
        with self._kilit:
            self._izinler.discard(eylem)

    def izin_var_mi(self, eylem: Eylem) -> bool:
        with self._kilit:
            return eylem in self._izinler

    def gerektir(self, eylem: Eylem) -> None:
        """İzin yoksa :class:`ConsentRequiredError` fırlatır."""
        if not self.izin_var_mi(eylem):
            raise ConsentRequiredError(
                f"'{eylem.value}' eylemi için kullanıcı onayı gerekli. "
                "Onay verilmeden bu işlem başlatılmaz."
            )

    def aktif_izinler(self) -> list[str]:
        with self._kilit:
            return sorted(e.value for e in self._izinler)
