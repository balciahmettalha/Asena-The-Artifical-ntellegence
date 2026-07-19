"""Bilgi Kaynaştırma (Knowledge Fusion).

Farklı bilgilerden yeni bilgi üretir. İki düzeyde çalışır:

1. Kural tabanlı kaynaştırma: bilinen kavram çiftleri
   (elektrik + manyetizma → elektromanyetizma).
2. Genel kaynaştırma: aynı özneli iki önermenin yüklemlerini birleştirir.
"""

from __future__ import annotations

from typing import Any

from asena.engine.base import BaseEngine, EngineResult

# (a, b) → (yeni kavram, açıklama)
FUZYON_KURALLARI: dict[frozenset[str], tuple[str, str]] = {
    frozenset({"elektrik", "manyetizma"}): (
        "elektromanyetizma",
        "Elektrik ve manyetizma birbirini üretir; ikisi tek bir etkileşimdir.",
    ),
    frozenset({"elektrik", "su"}): (
        "elektrikli hidro sistem",
        "Su elektrolizle ayrıştırılabilir; elektrik enerjisi kimyasal enerjiye dönüşür.",
    ),
    frozenset({"beyin", "bilgisayar"}): (
        "bilişsel sistem",
        "Beyin gibi bilgi işleyen yapay sistemler kurulabilir.",
    ),
    frozenset({"ısı", "hareket"}): (
        "termodinamik",
        "Isı ile iş arasındaki dönüşümü inceleyen bilim dalı.",
    ),
}


class KnowledgeFusion(BaseEngine):
    """Bilgileri kaynaştırarak yeni bilgi üreten motor."""

    name = "knowledge_fusion"
    group = "knowledge"

    def kavram_kaynastir(self, a: str, b: str) -> tuple[str, str] | None:
        """Bilinen kavram çiftini kaynaştırır; kural yoksa ``None``."""
        return FUZYON_KURALLARI.get(frozenset({a, b}))

    def onerme_kaynastir(self, o1: dict[str, Any], o2: dict[str, Any]) -> dict[str, Any] | None:
        """Aynı özneli iki önermeyi tek önermede birleştirir."""
        if o1.get("ozne") != o2.get("ozne"):
            return None
        yuklemler = {str(o1.get("yuklem", "")), str(o2.get("yuklem", ""))}
        yuklemler.discard("")
        if len(yuklemler) < 2:
            return None
        yeni = " ve ".join(sorted(yuklemler))
        return {
            "ozne": o1["ozne"],
            "yuklem": yeni,
            "nesne": None,
            "onerme": f"{o1['ozne'].capitalize()} {yeni}.",
            "guven": min(float(o1.get("guven", 1.0)), float(o2.get("guven", 1.0))) * 0.95,
            "kaynak": "kaynastirma",
        }

    def process(self, girdi: dict[str, Any], **kwargs: Any) -> EngineResult:
        if "a" in girdi and "b" in girdi:
            sonuc = self.kavram_kaynastir(str(girdi["a"]), str(girdi["b"]))
            if sonuc is None:
                return EngineResult(
                    ok=False, confidence=0.2,
                    explanation="Bu kavram çifti için kaynaştırma kuralı yok.",
                )
            ad, aciklama = sonuc
            return EngineResult(
                data={"kavram": ad, "aciklama": aciklama},
                confidence=0.9, explanation=aciklama,
            )
        sonuc = self.onerme_kaynastir(girdi.get("o1", {}), girdi.get("o2", {}))
        if sonuc is None:
            return EngineResult.hata("Önermeler kaynaştırılamadı (özne ortak değil).")
        return EngineResult(data=sonuc, explanation=sonuc["onerme"])
