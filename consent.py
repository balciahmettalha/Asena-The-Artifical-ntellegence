"""Sohbet oturumu.

Her oturum veritabanında bir konuşma kaydıyla izlenir; mesajlar kalıcı
belleğe yazılır. Böylece ASENA önceki konuşmaları hatırlar.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from asena.core.cognitive_core import CognitiveCore


@dataclass
class Session:
    """Tek bir sohbet oturumu."""

    cekirdek: "CognitiveCore"
    konusma_id: int = 0
    gecmis: list[tuple[str, str]] = field(default_factory=list)

    def ac(self) -> "Session":
        self.konusma_id = self.cekirdek.konusmalar.konusma_ac(mod="sohbet")
        return self

    def mesaj_kaydet(self, rol: str, icerik: str) -> None:
        self.gecmis.append((rol, icerik))
        self.cekirdek.motor("memory_engine").mesaj_kaydet(
            self.konusma_id, rol, icerik
        )

    def son_mesajlar(self, limit: int = 10) -> list[dict[str, Any]]:
        return self.cekirdek.konusmalar.son_mesajlar(self.konusma_id, limit)

    def kapat(self) -> None:
        self.cekirdek.konusmalar.konusma_kapat(self.konusma_id)
