"""Hata Sınıflandırma (Error Classification).

Hatalar türüne göre sınıflandırılır: mantık, matematik, bilgi eksikliği,
çelişki, dil ve yanlış varsayım. Sınıflandırma, öğrenme motorunun hangi
alana odaklanacağını belirler.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from asena.engine.base import BaseEngine, EngineResult

HATA_TURLERI = ("mantik", "matematik", "bilgi_eksikligi", "celiski", "dil",
                "yanlis_varsayim")


@dataclass
class HataKaydi:
    tur: str
    aciklama: str
    kanit: str = ""
    oneri: str = ""


class ErrorClassification(BaseEngine):
    """Hataları türlerine ayıran ve düzeltme öneren motor."""

    name = "error_classification"
    group = "decision"

    _IPUCLARI: dict[str, tuple[str, ...]] = {
        "matematik": ("hesap", "toplam", "bölme", "çarpma", "sayı", "aritmetik", "sıfıra"),
        "mantik": ("geçersiz çıkarım", "tümevarım hatası", "safsata", "çelişik öncül"),
        "bilgi_eksikligi": ("bilinmiyor", "kayıt yok", "eksik bilgi", "tanınmıyor"),
        "celiski": ("çelişki", "zıt", "uyuşmazlık"),
        "dil": ("yazım", "dil bilgisi", "anlaşılamadı", "çözümlenemedi"),
        "yanlis_varsayim": ("varsayım", "farz", "sanıl"),
    }

    def siniflandir(self, hata_metni: str) -> HataKaydi:
        """Hata metnini türüne göre sınıflandırır."""
        kucuk = hata_metni.lower()
        for tur, ipuclari in self._IPUCLARI.items():
            if any(ipucu in kucuk for ipucu in ipuclari):
                return HataKaydi(
                    tur=tur, aciklama=hata_metni,
                    kanit=next(i for i in ipuclari if i in kucuk),
                    oneri=self._oneri(tur),
                )
        return HataKaydi(tur="bilgi_eksikligi", aciklama=hata_metni,
                         oneri=self._oneri("bilgi_eksikligi"))

    @staticmethod
    def _oneri(tur: str) -> str:
        oneriler = {
            "mantik": "Öncüller gözden geçirilmeli; çıkarım zinciri yeniden kurulmalı.",
            "matematik": "İşlem adımları tek tek doğrulanmalı.",
            "bilgi_eksikligi": "Eksik kavram öğrenilmeli veya kullanıcıya sorulmalı.",
            "celiski": "Çelişkili bilgiler sürümlenmeli; güncel olan seçilmeli.",
            "dil": "Girdi yeniden çözümlenmeli; yazım denetimi yapılmalı.",
            "yanlis_varsayim": "Varsayımlar açıkça listelenip doğrulanmalı.",
        }
        return oneriler.get(tur, "Hata kaydedilmeli.")

    def process(self, girdi: dict[str, Any], **kwargs: Any) -> EngineResult:
        kayit = self.siniflandir(str(girdi.get("hata", "")))
        return EngineResult(
            data=kayit,
            explanation=f"Hata türü: {kayit.tur} — öneri: {kayit.oneri}",
        )
