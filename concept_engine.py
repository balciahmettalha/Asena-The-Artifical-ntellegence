"""Öğrenme Stratejisi (Learning Strategy).

Matematik, dil, kodlama ve fizik için farklı öğrenme stratejileri
uygulanır. Stratejiler değiştirilebilir nesnelerdir (Strategy deseni).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from asena.engine.base import BaseEngine, EngineResult


@dataclass(frozen=True)
class Strateji:
    alan: str
    adimlar: tuple[str, ...]
    odak: str


STRATEJILER: dict[str, Strateji] = {
    "matematik": Strateji(
        "matematik",
        ("kavramı tanımla", "kuralı çıkar", "örnek çöz", "ters işlemle doğrula"),
        "kural ve doğrulama",
    ),
    "dil": Strateji(
        "dil",
        ("kelimeyi çözümle", "bağlamda gözle", "ilişkilendir", "tekrarla"),
        "bağlam ve ilişki",
    ),
    "kodlama": Strateji(
        "kodlama",
        ("sözdizimini öğren", "küçük örnek yaz", "hata ayıkla", "yeniden düzenle"),
        "uygulama ve hata analizi",
    ),
    "fizik": Strateji(
        "fizik",
        ("olguyu gözle", "neden-sonuç kur", "formüle dök", "simülasyonla sına"),
        "nedensellik ve doğrulama",
    ),
}


class LearningStrategy(BaseEngine):
    """Alana uygun öğrenme stratejisini seçen motor."""

    name = "learning_strategy"
    group = "learning"

    def strateji_sec(self, alan: str) -> Strateji:
        return STRATEJILER.get(alan, STRATEJILER["dil"])

    def plan_uret(self, alan: str, konu: str) -> list[str]:
        """Konu için stratejiye göre adım listesi üretir."""
        strateji = self.strateji_sec(alan)
        return [f"{adim} ({konu})" for adim in strateji.adimlar]

    def process(self, girdi: dict[str, Any], **kwargs: Any) -> EngineResult:
        alan = str(girdi.get("alan", "dil"))
        konu = str(girdi.get("konu", ""))
        plan = self.plan_uret(alan, konu)
        return EngineResult(
            data=plan, explanation=f"{alan} için {len(plan)} adımlık öğrenme planı."
        )
