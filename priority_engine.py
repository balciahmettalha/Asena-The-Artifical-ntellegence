"""Kod Öz-Analizi (Code Self-Analysis).

Yazılan Python kodunu yeniden okuyup hız, RAM, temizlik ve güvenlik
açısından değerlendirir. Statik analiz yapar (ast); kodu çalıştırmaz.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import Any

from asena.engine.base import BaseEngine, EngineResult


@dataclass
class KodRaporu:
    fonksiyon_sayisi: int
    satir_sayisi: int
    en_uzun_fonksiyon: tuple[str, int]
    riskler: list[str] = field(default_factory=list)
    oneriler: list[str] = field(default_factory=list)
    puan: float = 1.0


class CodeSelfAnalysis(BaseEngine):
    """Python kodunu statik olarak denetleyen motor."""

    name = "code_self_analysis"
    group = "governance"

    UZUN_FONKSIYON_SINIRI = 40

    def analiz_et(self, kod: str) -> KodRaporu:
        """Kod metnini analiz eder; risk ve önerileri döndürür."""
        satirlar = kod.splitlines()
        try:
            agac = ast.parse(kod)
        except SyntaxError as exc:
            return KodRaporu(
                fonksiyon_sayisi=0, satir_sayisi=len(satirlar),
                en_uzun_fonksiyon=("", 0),
                riskler=[f"Sözdizimi hatası: satır {exc.lineno}"],
                puan=0.0,
            )
        fonksiyonlar = [
            d for d in ast.walk(agac)
            if isinstance(d, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        en_uzun = max(
            ((f.name, (f.end_lineno or f.lineno) - f.lineno) for f in fonksiyonlar),
            key=lambda t: t[1], default=("", 0),
        )
        riskler: list[str] = []
        oneriler: list[str] = []
        for dugum in ast.walk(agac):
            if isinstance(dugum, ast.Call) and isinstance(dugum.func, ast.Name):
                if dugum.func.id in {"eval", "exec"}:
                    riskler.append(f"'{dugum.func.id}' çağrısı: güvenlik riski.")
                if dugum.func.id == "input":
                    oneriler.append("input() kullanımı; arayüz katmanına taşınmalı.")
            if isinstance(dugum, ast.While):
                oneriler.append("while döngüsü: sonlanma koşulu doğrulanmalı (hız).")
        if en_uzun[1] > self.UZUN_FONKSIYON_SINIRI:
            oneriler.append(
                f"'{en_uzun[0]}' {en_uzun[1]} satır; parçalanması okunabilirliği artırır."
            )
        if len(fonksiyonlar) == 0 and len(satirlar) > 20:
            oneriler.append("Fonksiyonsuz uzun betik; modülerleştirme önerilir (temizlik).")
        puan = 1.0 - 0.2 * len(riskler) - 0.05 * len(oneriler)
        return KodRaporu(
            fonksiyon_sayisi=len(fonksiyonlar), satir_sayisi=len(satirlar),
            en_uzun_fonksiyon=en_uzun, riskler=riskler, oneriler=oneriler,
            puan=round(max(0.0, puan), 2),
        )

    def process(self, girdi: dict[str, Any], **kwargs: Any) -> EngineResult:
        rapor = self.analiz_et(str(girdi.get("kod", "")))
        ozet = (
            f"{rapor.fonksiyon_sayisi} fonksiyon, {rapor.satir_sayisi} satır; "
            f"{len(rapor.riskler)} risk, {len(rapor.oneriler)} öneri "
            f"(puan {rapor.puan:.2f})"
        )
        return EngineResult(
            data=rapor, ok=not rapor.riskler,
            confidence=rapor.puan, explanation=ozet,
        )
