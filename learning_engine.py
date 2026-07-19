"""Öz Yansıma (Self Reflection).

Yanıt verdikten kısa süre sonra "bunu daha iyi açıklayabilirdim" diyerek
yanıtı güncelleyebilme yeteneği. Öz değerlendirme bulgularına göre
eksik kavramları ekler veya güven uyarısını netleştirir.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from asena.engine.base import BaseEngine, EngineResult
from asena.engine.decision.self_evaluation import Degerlendirme

YANSIMA_PENCERESI_SN = 30.0


@dataclass
class YansimaSonucu:
    guncellendi_mi: bool
    yeni_yanit: str
    gerekce: str
    gecen_sure: float


class SelfReflection(BaseEngine):
    """Verilmiş yanıtı gözden geçirip gerektiğinde iyileştiren motor."""

    name = "self_reflection"
    group = "decision"

    def yansit(self, yanit: str, degerlendirme: Degerlendirme,
               yanit_zamani: float | None = None,
               ek_bilgiler: list[str] | None = None) -> YansimaSonucu:
        """30 saniyelik pencere içinde yanıtı iyileştirmeyi dener."""
        simdi = time.time()
        baslangic = yanit_zamani if yanit_zamani is not None else simdi
        gecen = simdi - baslangic
        if gecen > YANSIMA_PENCERESI_SN:
            return YansimaSonucu(
                guncellendi_mi=False, yeni_yanit=yanit,
                gerekce="Yansıma penceresi (30 sn) doldu.", gecen_sure=gecen,
            )
        if not degerlendirme.iyilestirilebilir_mi:
            return YansimaSonucu(
                guncellendi_mi=False, yeni_yanit=yanit,
                gerekce="Yanıt yeterli; iyileştirme gerekmiyor.",
                gecen_sure=gecen,
            )
        eklemeler: list[str] = []
        if degerlendirme.eksik_var_mi and ek_bilgiler:
            eklemeler.extend(ek_bilgiler)
        if degerlendirme.puan < 0.5:
            eklemeler.append(
                "Not: Bu yanıtın güveni düşük; kesinlik için ek bilgi gerekir."
            )
        if not eklemeler:
            return YansimaSonucu(
                guncellendi_mi=False, yeni_yanit=yanit,
                gerekce="İyileştirme için ek malzeme bulunamadı.",
                gecen_sure=gecen,
            )
        yeni = yanit.rstrip() + "\n" + "\n".join(f"- {e}" for e in eklemeler)
        return YansimaSonucu(
            guncellendi_mi=True, yeni_yanit=yeni,
            gerekce="Öz yansıma ile eksikler giderildi.", gecen_sure=gecen,
        )

    def process(self, girdi: dict[str, Any], **kwargs: Any) -> EngineResult:
        sonuc = self.yansit(
            str(girdi.get("yanit", "")), girdi["degerlendirme"],
            girdi.get("yanit_zamani"), list(girdi.get("ek_bilgiler", [])),
        )
        return EngineResult(
            data=sonuc, explanation=sonuc.gerekce,
            confidence=1.0 if sonuc.guncellendi_mi else 0.5,
        )
