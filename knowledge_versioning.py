"""Planlayıcı (Planner).

Uzun görevleri adımlara böler, adımlar arası bağımlılıkları izler ve
kritik yolu (en uzun bağımlılık zinciri) hesaplar. Çevrimli bağımlılık
varsa hata döndürür.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from asena.engine.base import BaseEngine, EngineResult


@dataclass
class Adim:
    ad: str
    bagimliliklar: list[str] = field(default_factory=list)
    sure: int = 1                    # göreli süre birimi


class Planner(BaseEngine):
    """Bağımlılık çözümleyen ve kritik yol bulan planlayıcı."""

    name = "planner"
    group = "planning"

    def planla(self, adimlar: list[Adim]) -> dict[str, Any]:
        """Adımları topolojik sıralar ve kritik yolu hesaplar."""
        harita = {a.ad: a for a in adimlar}
        for a in adimlar:
            for b in a.bagimliliklar:
                if b not in harita:
                    return {"hata": f"Bilinmeyen bağımlılık: '{b}' ({a.ad})"}
        siralama = self._topolojik(harita)
        if siralama is None:
            return {"hata": "Çevrimli bağımlılık saptandı; plan çözülemez."}
        kritik = self._kritik_yol(harita)
        return {"siralama": siralama, "kritik_yol": kritik,
                "toplam_sure": sum(harita[a].sure for a in kritik)}

    @staticmethod
    def _topolojik(harita: dict[str, Adim]) -> list[str] | None:
        giris = {ad: len(a.bagimliliklar) for ad, a in harita.items()}
        kuyruk = [ad for ad, d in giris.items() if d == 0]
        siralama: list[str] = []
        while kuyruk:
            ad = kuyruk.pop(0)
            siralama.append(ad)
            for diger, a in harita.items():
                if ad in a.bagimliliklar:
                    giris[diger] -= 1
                    if giris[diger] == 0:
                        kuyruk.append(diger)
        return siralama if len(siralama) == len(harita) else None

    @staticmethod
    def _kritik_yol(harita: dict[str, Adim]) -> list[str]:
        """En uzun toplam süreli bağımlılık zinciri."""
        en_uzun: dict[str, tuple[int, list[str]]] = {}

        def hesapla(ad: str) -> tuple[int, list[str]]:
            if ad in en_uzun:
                return en_uzun[ad]
            a = harita[ad]
            if not a.bagimliliklar:
                en_uzun[ad] = (a.sure, [ad])
                return en_uzun[ad]
            en_iyi = max((hesapla(b) for b in a.bagimliliklar),
                         key=lambda t: t[0])
            en_uzun[ad] = (a.sure + en_iyi[0], [*en_iyi[1], ad])
            return en_uzun[ad]

        return max((hesapla(ad)[1] for ad in harita), key=len, default=[])

    def process(self, girdi: dict[str, Any], **kwargs: Any) -> EngineResult:
        adimlar = [
            Adim(ad=str(a["ad"]),
                 bagimliliklar=list(a.get("bagimliliklar", [])),
                 sure=int(a.get("sure", 1)))
            for a in girdi.get("adimlar", [])
        ]
        sonuc = self.planla(adimlar)
        if "hata" in sonuc:
            return EngineResult.hata(sonuc["hata"])
        return EngineResult(
            data=sonuc,
            explanation=(
                f"{len(sonuc['siralama'])} adım planlandı; kritik yol: "
                f"{' → '.join(sonuc['kritik_yol'])}"
            ),
        )
