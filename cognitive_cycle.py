"""Sohbet Modu (Chat Mode).

ASENA'nın birincil çalışma modu: kullanıcıyla sohbet eder, soruları
yanıtlar ve sohbet sırasında öğrenir. Eğik çizgi komutlarıyla sistemin
iç durumu (iz, merak, günlük, yetkiler) incelenebilir.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from asena.chat.session import Session
from asena.core.consent import Eylem

if TYPE_CHECKING:
    from asena.core.cognitive_core import CognitiveCore

KOMUTLAR = {
    "/iz": "Son yanıtın akıl yürütme izini gösterir",
    "/merak": "Öğrenmek istediği konuları listeler",
    "/günlük": "Bugünkü öğrenme raporunu gösterir",
    "/yetki": "Harici eylem yetkisi verir: /yetki internet",
    "/yetkiler": "Aktif yetkileri listeler",
    "/motorlar": "Yüklü motorları listeler",
    "/yardım": "Komut listesini gösterir",
    "/çıkış": "Sohbeti sonlandırır",
}


class ChatMode:
    """Sohbet akışını yöneten sınıf."""

    def __init__(self, cekirdek: "CognitiveCore") -> None:
        self.c = cekirdek
        self.oturum = Session(cekirdek).ac()
        self._son_iz: list[tuple[str, str]] = []

    # ------------------------------------------------------------------ komutlar
    def _komut_mu(self, metin: str) -> str | None:
        kucuk = metin.strip().lower()
        if kucuk.startswith("/iz"):
            if not self._son_iz:
                return "Henüz gösterilecek akıl yürütme izi yok."
            satirlar = [f"  {i + 1}. [{ad}] {detay}" for i, (ad, detay) in enumerate(self._son_iz)]
            return "Akıl yürütme izi:\n" + "\n".join(satirlar)
        if kucuk.startswith("/merak"):
            merak = self.c.motor("curiosity_engine")
            kayit = merak.siradaki_merak()
            if kayit is None:
                return "Şu an bekleyen merak kaydı yok."
            return (
                f"Öğrenmek istediğim konu: '{kayit.konu}' "
                f"(öncelik {kayit.oncelik:.2f}) — {merak.arastirma_istegi(kayit.konu)}"
            )
        if kucuk.startswith("/günlük"):
            return self.c.motor("learning_journal").gunluk_rapor()
        if kucuk.startswith("/yetkiler"):
            aktif = self.c.consent.aktif_izinler()
            return "Aktif yetkiler: " + (", ".join(aktif) if aktif else "yok")
        if kucuk.startswith("/yetki"):
            parcalar = kucuk.split(maxsplit=1)
            if len(parcalar) < 2:
                return "Kullanım: /yetki <eylem> (örn. /yetki internet)"
            try:
                eylem = Eylem(parcalar[1].strip())
            except ValueError:
                return f"Bilinmeyen eylem: '{parcalar[1]}'. Geçerli: {[e.value for e in Eylem]}"
            self.c.consent.izin_ver(eylem)
            return f"'{eylem.value}' yetkisi verildi."
        if kucuk.startswith("/motorlar"):
            return f"{len(self.c.registry)} motor yüklü:\n  " + ", ".join(self.c.registry.names())
        if kucuk.startswith("/yardım") or kucuk.startswith("/yardim"):
            return "Komutlar:\n" + "\n".join(
                f"  {k}: {v}" for k, v in KOMUTLAR.items()
            )
        if kucuk.startswith("/çıkış") or kucuk.startswith("/cikis"):
            return "__CIKIS__"
        return None

    # ------------------------------------------------------------------ sohbet
    def soyle(self, metin: str) -> str:
        """Bir kullanıcı iletisini işler ve ASENA'nın yanıtını döndürür."""
        komut_yaniti = self._komut_mu(metin)
        if komut_yaniti is not None:
            return komut_yaniti
        self.oturum.mesaj_kaydet("kullanici", metin)
        yanit = self.c.dongu.calis(metin)
        self._son_iz = yanit.iz
        self.oturum.mesaj_kaydet("asena", yanit.metin)
        return yanit.metin

    def kapat(self) -> None:
        self.oturum.kapat()
