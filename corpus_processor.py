"""Fizik Uzmanı.

Fiziksel olguları neden-sonuç ilişkileri ve formüllerle açıklar. Formül
tabanındaki her kayıt bir denklem ailesidir; tek bilinmeyen kaldığında
çözülür ve sonuç fiziksel anlamıyla birlikte sunulur.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from asena.engine.base import BaseEngine, EngineResult

C_ISIGI = 299_792_458.0  # m/s
G_YERCEKIMI = 9.81       # m/s²


@dataclass(frozen=True)
class Formul:
    """Bir fizik formülü: değişkenler ve çözüm işlevleri."""

    ad: str
    degiskenler: tuple[str, ...]
    cozumler: dict[str, Callable[[dict[str, float]], float]]
    birim: dict[str, str]
    anlam: str


FORMULLER: list[Formul] = [
    Formul(
        ad="Newton'un ikinci yasası",
        degiskenler=("F", "m", "a"),
        cozumler={
            "F": lambda d: d["m"] * d["a"],
            "m": lambda d: d["F"] / d["a"],
            "a": lambda d: d["F"] / d["m"],
        },
        birim={"F": "N", "m": "kg", "a": "m/s²"},
        anlam="Kuvvet, kütleye ivme kazandırır; kütle büyüdükçe aynı kuvvet daha az ivme verir.",
    ),
    Formul(
        ad="Hız",
        degiskenler=("v", "d", "t"),
        cozumler={
            "v": lambda d: d["d"] / d["t"],
            "d": lambda d: d["v"] * d["t"],
            "t": lambda d: d["d"] / d["v"],
        },
        birim={"v": "m/s", "d": "m", "t": "s"},
        anlam="Hız, birim zamanda alınan yoldur.",
    ),
    Formul(
        ad="Kütle-enerji eşdeğerliği",
        degiskenler=("E", "m"),
        cozumler={
            "E": lambda d: d["m"] * C_ISIGI ** 2,
            "m": lambda d: d["E"] / C_ISIGI ** 2,
        },
        birim={"E": "J", "m": "kg"},
        anlam="Kütle donmuş enerjidir; az kütle çok büyük enerjiye karşılık gelir.",
    ),
    Formul(
        ad="Ohm yasası",
        degiskenler=("V", "I", "R"),
        cozumler={
            "V": lambda d: d["I"] * d["R"],
            "I": lambda d: d["V"] / d["R"],
            "R": lambda d: d["V"] / d["I"],
        },
        birim={"V": "V", "I": "A", "R": "Ω"},
        anlam="Gerilim, akım ile direncin çarpımıdır.",
    ),
    Formul(
        ad="Elektriksel güç",
        degiskenler=("P", "V", "I"),
        cozumler={
            "P": lambda d: d["V"] * d["I"],
            "V": lambda d: d["P"] / d["I"],
            "I": lambda d: d["P"] / d["V"],
        },
        birim={"P": "W", "V": "V", "I": "A"},
        anlam="Güç, birim zamanda harcanan enerjidir.",
    ),
    Formul(
        ad="Kinetik enerji",
        degiskenler=("Ek", "m", "v"),
        cozumler={
            "Ek": lambda d: 0.5 * d["m"] * d["v"] ** 2,
            "m": lambda d: 2 * d["Ek"] / d["v"] ** 2,
            "v": lambda d: (2 * d["Ek"] / d["m"]) ** 0.5,
        },
        birim={"Ek": "J", "m": "kg", "v": "m/s"},
        anlam="Hareket enerjisi; hızın karesiyle büyür.",
    ),
    Formul(
        ad="Potansiyel enerji",
        degiskenler=("Ep", "m", "h"),
        cozumler={
            "Ep": lambda d: d["m"] * G_YERCEKIMI * d["h"],
            "m": lambda d: d["Ep"] / (G_YERCEKIMI * d["h"]),
            "h": lambda d: d["Ep"] / (d["m"] * G_YERCEKIMI),
        },
        birim={"Ep": "J", "m": "kg", "h": "m"},
        anlam="Yükseklik, yer çekimine karşı depolanan enerjidir.",
    ),
]


@dataclass
class FizikCozumu:
    formul: str
    bilinmeyen: str
    deger: float
    birim: str
    anlam: str
    adimlar: list[str] = field(default_factory=list)


class PhysicsExpert(BaseEngine):
    """Fizik problemlerini çözen ve açıklayan uzman motor."""

    name = "physics_expert"
    group = "module"

    def coz(self, bilinenler: dict[str, float]) -> FizikCozumu | None:
        """Tek bilinmeyenli ilk uygun formülü bulur ve çözer."""
        for formul in FORMULLER:
            bilinmeyenler = [d for d in formul.degiskenler if d not in bilinenler]
            if len(bilinmeyenler) != 1:
                continue
            hedef = bilinmeyenler[0]
            try:
                deger = formul.cozumler[hedef](bilinenler)
            except (KeyError, ZeroDivisionError):
                continue
            adimlar = [
                f"Formül seçildi: {formul.ad}",
                "Bilinenler: "
                + ", ".join(f"{k} = {v}" for k, v in bilinenler.items()),
                f"Bilinmeyen {hedef} hesaplandı: {deger:g} {formul.birim[hedef]}",
            ]
            return FizikCozumu(
                formul=formul.ad, bilinmeyen=hedef, deger=deger,
                birim=formul.birim[hedef], anlam=formul.anlam, adimlar=adimlar,
            )
        return None

    def formulleri_listele(self) -> list[str]:
        return [f.ad for f in FORMULLER]

    def process(self, girdi: dict[str, Any], **kwargs: Any) -> EngineResult:
        bilinenler = {str(k): float(v) for k, v in dict(girdi).items()}
        cozum = self.coz(bilinenler)
        if cozum is None:
            return EngineResult.hata(
                "Bu bilinenlerle çözülebilen tek bilinmeyenli formül bulunamadı."
            )
        adimlar = "\n".join(f"  {a}" for a in cozum.adimlar)
        return EngineResult(
            data=cozum,
            explanation=(
                f"{cozum.bilinmeyen} = {cozum.deger:g} {cozum.birim}\n"
                f"{adimlar}\nAnlamı: {cozum.anlam}"
            ),
        )
