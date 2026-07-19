"""Bilgi Sürümleme (Knowledge Versioning).

Yanlış bilgi silinmez; arşivlenir. Her güncelleme ``v1 → v2 → v3``
geçmişi ve değişim nedeniyle kaydedilir. Böylece bilginin nasıl ve
neden değiştiği izlenebilir.
"""

from __future__ import annotations

from typing import Any

from asena.database.repositories import KnowledgeRepository
from asena.engine.base import BaseEngine, EngineResult


class KnowledgeVersioning(BaseEngine):
    """Bilgi güncellemelerini sürüm geçmişiyle yöneten motor."""

    name = "knowledge_versioning"
    group = "knowledge"

    def __init__(self, repo: KnowledgeRepository | None = None) -> None:
        super().__init__()
        self._repo = repo

    def guncelle(self, kimlik: str, yeni_onerme: str, neden: str,
                 yeni_guven: float | None = None) -> dict[str, Any] | None:
        """Bilgiyi günceller; eski hâlini sürüm geçmişine işler.

        Returns:
            Güncelleme özeti; kayıt yoksa ``None``.
        """
        if self._repo is None:
            return None
        eski = self._repo.bul(kimlik)
        if eski is None:
            return None
        self._repo.surum_kaydet(
            kimlik, int(eski["surum"]), str(eski["onerme"]), neden
        )
        self._repo.surum_artir(kimlik)
        self._repo.execute_guncelle(
            kimlik, yeni_onerme,
            yeni_guven if yeni_guven is not None else float(eski["guven"]),
        )
        return {
            "kimlik": kimlik,
            "eski": eski["onerme"],
            "yeni": yeni_onerme,
            "yeni_surum": int(eski["surum"]) + 1,
            "neden": neden,
        }

    def gecmis(self, kimlik: str) -> list[dict[str, Any]]:
        """Bilginin tüm sürüm geçmişini döndürür."""
        if self._repo is None:
            return []
        return self._repo.surumler(kimlik)

    def gecmis_metni(self, kimlik: str) -> str:
        surumler = self.gecmis(kimlik)
        if not surumler:
            return "Bu bilgi için sürüm geçmişi yok."
        satirlar = [
            f"v{s['surum_no']}: {s['icerik']} — neden: {s.get('degisim_nedeni') or '-'}"
            for s in surumler
        ]
        return "Sürüm geçmişi:\n" + "\n".join(satirlar)

    def process(self, girdi: dict[str, Any], **kwargs: Any) -> EngineResult:
        if girdi.get("islem") == "guncelle":
            sonuc = self.guncelle(
                str(girdi["kimlik"]), str(girdi["yeni_onerme"]),
                str(girdi.get("neden", "")), girdi.get("yeni_guven"),
            )
            if sonuc is None:
                return EngineResult.hata("Bilgi kaydı bulunamadı.")
            return EngineResult(
                data=sonuc, explanation=f"Bilgi v{sonuc['yeni_surum']} sürümüne güncellendi."
            )
        metin = self.gecmis_metni(str(girdi.get("kimlik", "")))
        return EngineResult(data=metin, explanation=metin)
