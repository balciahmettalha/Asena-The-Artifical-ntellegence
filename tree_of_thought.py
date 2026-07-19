"""Unutma Motoru (Forgetting Engine).

İnsan beyni gibi gereksiz bilgiyi zamanla zayıflatır ve siler. Ebbinghaus
eğrisinden esinlenen üstel azalma kullanılır; sık erişilen bilgi güçlenir,
erişilmeyen silinir.
"""

from __future__ import annotations

import math
import time
from typing import Any

from asena.engine.base import BaseEngine, EngineResult
from asena.memory.workspace import Workspace


class ForgettingEngine(BaseEngine):
    """Anı gücünü zamana ve erişime göre yöneten motor."""

    name = "forgetting"
    group = "memory"

    def __init__(self, workspace: Workspace | None = None,
                 esik: float = 0.05) -> None:
        super().__init__()
        self.workspace = workspace or Workspace()
        self.esik = esik

    @staticmethod
    def hatirlama_gucu(erisim_sayisi: int, gecen_saat: float) -> float:
        """Ebbinghaus benzeri: erişim arttıkça unutma yavaşlar.

        ``güç = e^(-t / (24 · (1 + erişim)))`` — her erişim anıyı bir gün
        daha dayanıklı kılar.
        """
        kararlilik = 24.0 * (1 + erisim_sayisi)
        return math.exp(-gecen_saat / kararlilik)

    def calisma_bellegi_gec(self, oran: float | None = None) -> list[str]:
        """Çalışma belleğindeki güçleri azaltır; silinenleri döndürür."""
        if oran is not None:
            return self.workspace.guc_azalt(oran)
        silinen: list[str] = []
        simdi = time.time()
        for oge in list(self.workspace.etkinler()):
            saat = (simdi - oge.giris_zamani) / 3600
            oge.guc = self.hatirlama_gucu(oge.erisim_sayisi, saat)
            if oge.guc < self.esik:
                self.workspace.cikar(oge.anahtar)
                silinen.append(oge.anahtar)
        return silinen

    def onem_azalt(self, kelime_repo: Any, oran: float = 0.95,
                   alt_sinir: float = 0.1) -> int:
        """Uzun süreli kelime belleğindeki önem puanlarını azaltır.

        Çok erişilen kelimeler korunur; hiç erişilmeyenler önem eşiğinin
        altına düşer. Silinen öğe sayısını döndürür.
        """
        etkilenen = 0
        for kayit in kelime_repo.tumu():
            yeni_onem = float(kayit["onem"]) * oran
            if int(kayit.get("erisim_sayisi", 0)) > 5:
                continue  # sık kullanılan korunur
            if yeni_onem < alt_sinir:
                etkilenen += 1
                continue
            kelime_repo.onem_guncelle(str(kayit["yazim"]), yeni_onem)
        return etkilenen

    def process(self, girdi: dict[str, Any], **kwargs: Any) -> EngineResult:
        silinen = self.calisma_bellegi_gec(girdi.get("oran"))
        return EngineResult(
            data=silinen, explanation=f"{len(silinen)} anı unutuldu."
        )
