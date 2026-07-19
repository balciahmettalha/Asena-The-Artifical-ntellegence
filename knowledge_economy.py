"""Öz Değerlendirme (Self-Evaluation).

Her yanıttan sonra dört soru sorulur: Doğru mu? Eksik mi? Çelişki var
mı? Daha iyi olabilir mi? Yanıt; güven puanı, kapsanan kavramlar ve
çelişki denetimiyle puanlanır.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from asena.engine.base import BaseEngine, EngineResult


@dataclass
class Degerlendirme:
    dogru_mu: bool
    eksik_var_mi: bool
    celiski_var_mi: bool
    iyilestirilebilir_mi: bool
    puan: float
    notlar: list[str] = field(default_factory=list)


class SelfEvaluation(BaseEngine):
    """Üretilen yanıtları dört ölçütle değerlendiren motor."""

    name = "self_evaluation"
    group = "decision"

    def degerlendir(self, soru: str, yanit: str, guven: float,
                    kavramlar: list[str] | None = None,
                    celiski_var_mi: bool = False) -> Degerlendirme:
        kavramlar = kavramlar or []
        notlar: list[str] = []
        dogru_mu = guven >= 0.5 and bool(yanit.strip())
        if not dogru_mu:
            notlar.append("Güven düşük veya yanıt boş; doğruluk şüpheli.")
        kapsanan = sum(1 for k in kavramlar if k and k in yanit)
        eksik_var_mi = bool(kavramlar) and kapsanan < len(kavramlar)
        if eksik_var_mi:
            eksikler = [k for k in kavramlar if k and k not in yanit]
            notlar.append(f"Yanıtta eksik kavramlar: {', '.join(eksikler[:5])}")
        if celiski_var_mi:
            notlar.append("Bilgi tabanıyla çelişki saptandı.")
        iyilestirilebilir_mi = eksik_var_mi or guven < 0.7 or celiski_var_mi
        puan = guven
        if celiski_var_mi:
            puan *= 0.5
        if eksik_var_mi:
            puan *= 0.8
        return Degerlendirme(
            dogru_mu=dogru_mu, eksik_var_mi=eksik_var_mi,
            celiski_var_mi=celiski_var_mi,
            iyilestirilebilir_mi=iyilestirilebilir_mi,
            puan=round(puan, 3), notlar=notlar,
        )

    def process(self, girdi: dict[str, Any], **kwargs: Any) -> EngineResult:
        d = self.degerlendir(
            str(girdi.get("soru", "")), str(girdi.get("yanit", "")),
            float(girdi.get("guven", 0.5)),
            list(girdi.get("kavramlar", [])),
            bool(girdi.get("celiski_var_mi", False)),
        )
        ozet = (
            f"Doğru: {d.dogru_mu}, eksik: {d.eksik_var_mi}, "
            f"çelişki: {d.celiski_var_mi}, iyileştirilebilir: {d.iyilestirilebilir_mi} "
            f"(puan {d.puan:.2f})"
        )
        return EngineResult(data=d, confidence=d.puan, explanation=ozet)
