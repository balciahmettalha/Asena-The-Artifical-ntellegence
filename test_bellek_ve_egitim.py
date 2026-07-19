"""Nedensellik Zinciri (Causal Chain).

Her bilginin sebebini izler: ``elma düştü → yer çekimi → kütle →
uzay-zaman eğriliği``. "Neden?" sorularına derinlikli yanıt üretir;
zincir bilinen en derin sebebe kadar iner.
"""

from __future__ import annotations

from typing import Any

from asena.engine.base import BaseEngine, EngineResult
from asena.knowledge.world_model import WorldModel

# Derin bilimsel sebep zincirleri
DERIN_SEBEPLER: dict[str, str] = {
    "elma düştü": "yer çekimi",
    "yer çekimi": "kütle çekimi",
    "kütle çekimi": "kütle",
    "kütle": "uzay-zaman eğriliği",
    "uzay-zaman eğriliği": "genel görelilik kuramı",
    "su buharlaşır": "ısı enerjisi",
    "ısı enerjisi": "moleküler hareket",
    "yağmur": "su buharının yoğunlaşması",
    "su buharının yoğunlaşması": "havadaki su buharının soğuması",
    "gök gürültüsü": "yıldırımın havayı ısıtması",
    "yıldırım": "bulutlardaki elektrik yükü dengesizliği",
    "gökkuşağı": "ışığın su damlalarında kırılması",
}


class CausalChain(BaseEngine):
    """'Neden?' zincirlerini derinlemesine izleyen motor."""

    name = "causal_chain"
    group = "reason"
    dependencies = ("world_model",)

    def __init__(self, dunya: WorldModel | None = None) -> None:
        super().__init__()
        self.dunya = dunya or WorldModel()

    def neden_zinciri(self, olgu: str, derinlik: int = 6) -> list[str]:
        """Olgudan başlayıp en derin bilinen sebebe inen zincir."""
        zincir = [olgu]
        mevcut = olgu
        for _ in range(derinlik):
            sebep = DERIN_SEBEPLER.get(mevcut)
            if sebep is None:
                sebepler = self.dunya.sebep_bul(mevcut)
                sebep = sebepler[0] if sebepler else None
            if sebep is None or sebep in zincir:
                break
            zincir.append(sebep)
            mevcut = sebep
        return zincir

    def acikla(self, olgu: str) -> str:
        """'Neden?' sorusuna zincir hâlinde Türkçe açıklama üretir."""
        zincir = self.neden_zinciri(olgu)
        if len(zincir) == 1:
            return f"'{olgu}' olgusunun sebebi henüz bilgi tabanında yok."
        adimlar = [f"'{olgu}', çünkü {zincir[1]}."]
        for i in range(1, len(zincir) - 1):
            adimlar.append(f"{zincir[i].capitalize()}, çünkü {zincir[i + 1]}.")
        return " ".join(adimlar)

    def process(self, girdi: dict[str, Any], **kwargs: Any) -> EngineResult:
        olgu = str(girdi.get("olgu", girdi))
        zincir = self.neden_zinciri(olgu)
        return EngineResult(
            data=zincir, confidence=0.5 + 0.1 * len(zincir),
            explanation=self.acikla(olgu),
        )
