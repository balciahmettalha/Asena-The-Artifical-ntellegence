"""Benzetim Motoru (Analogy Engine).

Bilinmeyeni bilinenle açıklar: "CPU beyin gibi çalışır". Ayrıca klasik
``A : B :: C : ?`` benzetimlerini ilişki türü eşleşmesiyle çözer.
"""

from __future__ import annotations

from typing import Any

from asena.engine.base import BaseEngine, EngineResult
from asena.knowledge.knowledge_graph import KnowledgeGraph


class AnalogyEngine(BaseEngine):
    """İlişki örüntülerinden benzetim kuran motor."""

    name = "analogy_engine"
    group = "knowledge"
    dependencies = ("knowledge_graph",)

    def __init__(self, graf: KnowledgeGraph | None = None) -> None:
        super().__init__()
        self.graf = graf or KnowledgeGraph()

    # ------------------------------------------------------------------ açıklama
    def benzer_bul(self, kavram: str, en_cok: int = 3) -> list[tuple[str, float]]:
        """İlişki türü dağılımı en yakın bilinen kavramları döndürür."""
        hedef_turler = {k.tur for k in self.graf.komsular(kavram)}
        if not hedef_turler:
            return []
        skorlar: list[tuple[str, float]] = []
        for ad in self.graf.dugumler:
            if ad == kavram:
                continue
            turler = {k.tur for k in self.graf.komsular(ad)}
            if not turler:
                continue
            kesisim = len(hedef_turler & turler)
            birlesim = len(hedef_turler | turler)
            if kesisim:
                skorlar.append((ad, kesisim / birlesim))
        skorlar.sort(key=lambda x: -x[1])
        return skorlar[:en_cok]

    def acikla_ile(self, bilinmeyen: str) -> str:
        """Bilinmeyen kavramı en yakın bilinen kavramla açıklar."""
        benzerler = self.benzer_bul(bilinmeyen)
        if not benzerler:
            return f"'{bilinmeyen}' için henüz yeterli ilişki yok; öğrenilmesi gerek."
        ad, skor = benzerler[0]
        ortak = [
            k for k in self.graf.komsular(ad)
            if self.graf.iliski_var_mi(bilinmeyen, k.hedef, k.tur)
        ]
        if ortak:
            ilk = ortak[0]
            return (
                f"'{bilinmeyen}', '{ad}' gibi davranır: ikisi de "
                f"{ilk.tur} ilişkisiyle '{ilk.hedef}' bağlantılıdır "
                f"(benzerlik %{skor * 100:.0f})."
            )
        return f"'{bilinmeyen}' en çok '{ad}' kavramına benziyor (benzerlik %{skor * 100:.0f})."

    # ------------------------------------------------------------------ A:B::C:?
    def benzetim_coz(self, a: str, b: str, c: str) -> tuple[str | None, float]:
        """``A, B'ye neyse C de odur`` sorusunu çözer.

        A→B ilişki türünü bulur; C'den aynı türde çıkan düğümü döndürür.
        """
        turler = [k.tur for k in self.graf.komsular(a) if k.hedef == b]
        if not turler:
            return (None, 0.0)
        for tur in turler:
            adaylar = [k.hedef for k in self.graf.komsular(c, tur=tur)]
            if adaylar:
                return (adaylar[0], 0.8)
        return (None, 0.2)

    def process(self, girdi: dict[str, Any], **kwargs: Any) -> EngineResult:
        if "a" in girdi and "b" in girdi and "c" in girdi:
            cevap, guven = self.benzetim_coz(
                str(girdi["a"]), str(girdi["b"]), str(girdi["c"])
            )
            return EngineResult(
                data=cevap, confidence=guven,
                explanation=f"Benzetim sonucu: {cevap}",
            )
        metin = self.acikla_ile(str(girdi.get("kavram", "")))
        return EngineResult(data=metin, explanation=metin)
