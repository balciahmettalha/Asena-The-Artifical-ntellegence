"""Bilgi Evrimi (Knowledge Evolution).

Bilginin zamanla değişimini saklar. Örnek: Plüton 2006 öncesi gezegen,
sonrasında cüce gezegendir. Geçerlilik etiketi (dönem) ile hangi bilginin
hangi dönemde doğru sayıldığı sorgulanabilir.
"""

from __future__ import annotations

from typing import Any

from asena.database.repositories import KnowledgeRepository
from asena.engine.base import BaseEngine, EngineResult


class KnowledgeEvolution(BaseEngine):
    """Zamana bağlı bilgi geçerliliğini yöneten motor."""

    name = "knowledge_evolution"
    group = "knowledge"

    def __init__(self, repo: KnowledgeRepository | None = None) -> None:
        super().__init__()
        self._repo = repo

    def donem_ata(self, kimlik: str, gecerlilik: str) -> bool:
        """Bilgiye geçerlilik dönemi atar (örn. ``"2006 öncesi"``)."""
        if self._repo is None or self._repo.bul(kimlik) is None:
            return False
        self._repo.gecerlilik_guncelle(kimlik, gecerlilik)
        return True

    def doneminde_gecerli_mi(self, kayit: dict[str, Any], donem: str) -> bool:
        """Kaydın verilen dönemde geçerli olup olmadığını denetler."""
        gecerlilik = (kayit.get("gecerlilik") or "").strip()
        if not gecerlilik:
            return True  # dönemsiz bilgi her dönemde geçerli
        return gecerlilik == donem

    def konu_evrimi(self, ozne: str) -> list[dict[str, Any]]:
        """Bir özne hakkındaki tüm bilgileri dönemleriyle döndürür."""
        if self._repo is None:
            return []
        return self._repo.ozne_ile(ozne, limit=100)

    def evrim_ozeti(self, ozne: str) -> str:
        """Özne hakkındaki bilgi evrimini okunabilir özetler."""
        kayitlar = self.konu_evrimi(ozne)
        if not kayitlar:
            return f"'{ozne}' hakkında kayıtlı bilgi yok."
        satirlar = []
        for k in kayitlar:
            donem = k.get("gecerlilik") or "dönemsiz"
            satirlar.append(f"- [{donem}] {k['onerme']} (v{k['surum']})")
        return f"'{ozne}' bilgisinin evrimi:\n" + "\n".join(satirlar)

    def process(self, girdi: dict[str, Any], **kwargs: Any) -> EngineResult:
        if girdi.get("islem") == "donem_ata":
            ok = self.donem_ata(str(girdi["kimlik"]), str(girdi["gecerlilik"]))
            if not ok:
                return EngineResult.hata("Bilgi kaydı bulunamadı.")
            return EngineResult(data=True, explanation="Geçerlilik dönemi atandı.")
        ozet = self.evrim_ozeti(str(girdi.get("ozne", "")))
        return EngineResult(data=ozet, explanation=ozet)
