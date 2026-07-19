"""Bellek Motoru (Memory Engine).

Katmanlı belleğin tek giriş noktasıdır:

- **Kısa süreli**: :class:`Workspace` (dikkatle seçilen ~25 öğe).
- **Uzun süreli**: SQLite repository'leri (kelime, bilgi, ilişki, kural).
- **Konuşma hafızası**: oturum mesajları.
- **Önbellek**: sık erişilenler için LRU.

Bilinmeyen kelimeler anında kaydedilir ve ``bellek.bilinmeyen_kelime``
olayı yayınlanır; merak motoru bu olayla öğrenme ihtiyacı duyar.
"""

from __future__ import annotations

from typing import Any

from asena.core.event_bus import Event
from asena.database.repositories import (
    ConversationRepository,
    KnowledgeRepository,
    RelationRepository,
    RuleRepository,
    WordRepository,
)
from asena.engine.base import BaseEngine, EngineResult
from asena.knowledge.universal_id import UniversalIDGenerator
from asena.memory.cache import LRUCache
from asena.memory.workspace import Workspace


class MemoryEngine(BaseEngine):
    """Katmanlı bellek yöneticisi."""

    name = "memory_engine"
    group = "memory"

    def __init__(
        self,
        workspace: Workspace | None = None,
        kelime_repo: WordRepository | None = None,
        bilgi_repo: KnowledgeRepository | None = None,
        iliski_repo: RelationRepository | None = None,
        kural_repo: RuleRepository | None = None,
        konusma_repo: ConversationRepository | None = None,
        cache: LRUCache | None = None,
        kimlik_ureteci: UniversalIDGenerator | None = None,
    ) -> None:
        super().__init__()
        self.workspace = workspace or Workspace()
        self.kelimeler = kelime_repo
        self.bilgiler = bilgi_repo
        self.iliskiler = iliski_repo
        self.kurallar = kural_repo
        self.konusmalar = konusma_repo
        self.cache = cache or LRUCache()
        self.kimlikler = kimlik_ureteci or UniversalIDGenerator()

    # ------------------------------------------------------------- kelime hafızası
    def kelime_kaydet(self, yazim: str, kok: str | None = None,
                      tur: str | None = None, anlam: str | None = None,
                      onem: float = 1.0) -> str:
        """Kelimeyi uzun süreli belleğe kaydeder; yeni ise olay yayınlar."""
        yeni = True
        if self.kelimeler is not None:
            yeni = self.kelimeler.bul(yazim) is None
            self.kelimeler.ekle(yazim, kok=kok, tur=tur, anlam=anlam, onem=onem)
        if yeni and self._ctx is not None:
            self.ctx.bus.publish(
                Event("bellek.yeni_kelime", {"yazim": yazim, "kok": kok},
                      source=self.name)
            )
        return yazim

    def kelime_bul(self, yazim: str) -> dict[str, Any] | None:
        if self.kelimeler is None:
            return None
        self.kelimeler.erisim_kaydet(yazim)
        return self.kelimeler.bul(yazim)

    def bilinmeyen_kaydet(self, kok: str) -> None:
        """Bilinmeyen kelimeyi anında kaydeder ve merakı tetikler."""
        if self.kelimeler is not None and self.kelimeler.bul(kok) is None:
            self.kelimeler.ekle(kok, kok=kok, anlam=None, onem=1.0)
        if self._ctx is not None:
            self.ctx.bus.publish(
                Event("bellek.bilinmeyen_kelime", {"kok": kok}, source=self.name)
            )

    # -------------------------------------------------------------- bilgi hafızası
    def bilgi_kaydet(self, ozne: str, yuklem: str, nesne: str | None = None,
                     guven: float = 1.0, onem: float = 1.0,
                     kaynak: str = "kullanici",
                     gecerlilik: str | None = None) -> str:
        """Yeni bilgi önermesi kaydeder; evrensel kimliğini döndürür."""
        kimlik = self.kimlikler.uret()
        parcalar = [p for p in (ozne, nesne or "", yuklem) if p]
        onerme = " ".join([parcalar[0].capitalize(), *parcalar[1:]]) + "."
        if self.bilgiler is not None:
            self.bilgiler.ekle(
                kimlik, ozne, yuklem, nesne, onerme,
                guven=guven, onem=onem, kaynak=kaynak, gecerlilik=gecerlilik,
            )
        self.workspace.ekle(kimlik, onerme, onem=onem)
        if self._ctx is not None:
            self.ctx.bus.publish(
                Event("bilgi.eklendi", {"kimlik": kimlik, "onerme": onerme},
                      source=self.name)
            )
        return kimlik

    def bilgi_bul(self, kimlik: str) -> dict[str, Any] | None:
        if self.bilgiler is None:
            return None
        return self.cache.get_or(kimlik, lambda: self.bilgiler.bul(kimlik))

    def bilgi_ara(self, metin: str, limit: int = 10) -> list[dict[str, Any]]:
        if self.bilgiler is None:
            return []
        return self.bilgiler.ara(metin, limit=limit)

    def ozne_bilgileri(self, ozne: str) -> list[dict[str, Any]]:
        if self.bilgiler is None:
            return []
        return self.bilgiler.ozne_ile(ozne)

    # ------------------------------------------------------------- kural hafızası
    def kural_kaydet(self, kosul: str, sonuc: str, guven: float = 1.0) -> int:
        if self.kurallar is None:
            return 0
        return self.kurallar.ekle(kosul, sonuc, guven)

    def kurallar_tumu(self) -> list[dict[str, Any]]:
        return self.kurallar.tumu() if self.kurallar is not None else []

    # ----------------------------------------------------------- konuşma hafızası
    def mesaj_kaydet(self, konusma_id: int, rol: str, icerik: str) -> None:
        if self.konusmalar is not None:
            self.konusmalar.mesaj_ekle(konusma_id, rol, icerik)
        self.workspace.ekle(f"son_mesaj:{rol}", icerik, guc=0.8)

    def son_mesajlar(self, konusma_id: int, limit: int = 10) -> list[dict[str, Any]]:
        if self.konusmalar is None:
            return []
        return self.konusmalar.son_mesajlar(konusma_id, limit)

    # ------------------------------------------------------------------ motor
    def process(self, girdi: dict[str, Any], **kwargs: Any) -> EngineResult:
        islem = girdi.get("islem", "bilgi_ara")
        if islem == "bilgi_kaydet":
            kimlik = self.bilgi_kaydet(
                str(girdi["ozne"]), str(girdi["yuklem"]), girdi.get("nesne"),
            )
            return EngineResult(data=kimlik, explanation=f"Bilgi kaydedildi: {kimlik}")
        if islem == "kelime_kaydet":
            self.kelime_kaydet(str(girdi["yazim"]), girdi.get("kok"),
                               girdi.get("tur"), girdi.get("anlam"))
            return EngineResult(data=girdi["yazim"], explanation="Kelime kaydedildi.")
        sonuc = self.bilgi_ara(str(girdi.get("metin", "")))
        return EngineResult(data=sonuc, explanation=f"{len(sonuc)} bilgi bulundu.")
