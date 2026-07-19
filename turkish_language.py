"""Kodlama Uzmanı.

Python kodunu yazma, analiz etme ve hata ayıklama konularında uzman
modül. Analizler soyut sözdizimi ağacı (ast) üzerinden yapılır; kod
çalıştırılmaz (güvenlik ilkesi).
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import Any

from asena.engine.base import BaseEngine, EngineResult

KOD_SABLONLARI: dict[str, str] = {
    "fonksiyon": 'def {ad}({parametreler}):\n    """{aciklama}"""\n    {govde}\n',
    "sinif": (
        'class {ad}:\n    """{aciklama}"""\n\n'
        "    def __init__(self):\n        pass\n"
    ),
    "dongu": "for oge in {koleksiyon}:\n    {govde}\n",
}


@dataclass
class KodAnalizi:
    fonksiyonlar: list[str]
    siniflar: list[str]
    ice_aktarmalar: list[str]
    karmasiklik: int
    bulgular: list[str] = field(default_factory=list)


class CodingExpert(BaseEngine):
    """Kod yazma ve analiz etme uzmanı."""

    name = "coding_expert"
    group = "module"

    # ------------------------------------------------------------------ analiz
    def analiz_et(self, kod: str) -> KodAnalizi:
        """Kodun yapısını çıkarır ve olası hataları işaretler."""
        try:
            agac = ast.parse(kod)
        except SyntaxError as exc:
            return KodAnalizi([], [], [], 0,
                              [f"Sözdizimi hatası (satır {exc.lineno}): {exc.msg}"])
        fonksiyonlar: list[str] = []
        siniflar: list[str] = []
        aktarmalar: list[str] = []
        bulgular: list[str] = []
        karmasiklik = 1
        for dugum in ast.walk(agac):
            if isinstance(dugum, ast.FunctionDef):
                fonksiyonlar.append(dugum.name)
                for varsayilan in dugum.args.defaults:
                    if isinstance(varsayilan, (ast.List, ast.Dict, ast.Set)):
                        bulgular.append(
                            f"'{dugum.name}': değişken varsayılan parametre "
                            "(mutable default) hatası riski."
                        )
            elif isinstance(dugum, ast.AsyncFunctionDef):
                fonksiyonlar.append(dugum.name)
            elif isinstance(dugum, ast.ClassDef):
                siniflar.append(dugum.name)
            elif isinstance(dugum, ast.Import):
                aktarmalar.extend(a.name for a in dugum.names)
            elif isinstance(dugum, ast.ImportFrom):
                aktarmalar.append(dugum.module or "")
            elif isinstance(dugum, (ast.If, ast.For, ast.While, ast.ExceptHandler)):
                karmasiklik += 1
            elif isinstance(dugum, ast.ExceptHandler) and dugum.type is None:
                bulgular.append("Çıplak 'except:' kullanımı; hata türü belirtilmeli.")
        return KodAnalizi(fonksiyonlar, siniflar, aktarmalar, karmasiklik, bulgular)

    # ------------------------------------------------------------------ üretim
    def sablon_uret(self, sablon: str, **degiskenler: str) -> str:
        """Kod şablonundan kod üretir."""
        kalip = KOD_SABLONLARI.get(sablon)
        if kalip is None:
            raise ValueError(f"Bilinmeyen şablon: '{sablon}'")
        return kalip.format(
            ad=degiskenler.get("ad", "ornek"),
            parametreler=degiskenler.get("parametreler", ""),
            aciklama=degiskenler.get("aciklama", "Otomatik üretildi."),
            govde=degiskenler.get("govde", "pass"),
            koleksiyon=degiskenler.get("koleksiyon", "ogeler"),
        )

    def hata_ayikla(self, kod: str, hata_mesaji: str) -> list[str]:
        """Hata mesajına göre olası nedenleri sıralar."""
        oneriler: list[str] = []
        if "NameError" in hata_mesaji:
            oneriler.append("Tanımsız isim kullanılmış; değişken/fonksiyon tanımı denetlenmeli.")
        if "TypeError" in hata_mesaji:
            oneriler.append("Tür uyuşmazlığı; işlenenlerin türleri denetlenmeli.")
        if "IndexError" in hata_mesaji:
            oneriler.append("Liste sınırı aşılmış; uzunluk denetimi eklenmeli.")
        if "KeyError" in hata_mesaji:
            oneriler.append("Sözlükte olmayan anahtar; .get() kullanımı düşünülmeli.")
        if "SyntaxError" in hata_mesaji:
            oneriler.append("Sözdizimi hatası; parantez ve iki nokta işaretleri denetlenmeli.")
        if "IndentationError" in hata_mesaji:
            oneriler.append("Girinti tutarsız; boşluk/sekme karışımı denetlenmeli.")
        if not oneriler:
            analiz = self.analiz_et(kod)
            oneriler.extend(analiz.bulgular or ["Belirgin bir örüntü bulunamadı; adım adım izleme önerilir."])
        return oneriler

    # ------------------------------------------------------------------ motor
    def process(self, girdi: dict[str, Any], **kwargs: Any) -> EngineResult:
        islem = girdi.get("islem", "analiz")
        if islem == "sablon":
            try:
                kod = self.sablon_uret(
                    str(girdi.get("sablon", "fonksiyon")),
                    **{k: str(v) for k, v in girdi.items() if k not in {"islem", "sablon"}},
                )
            except ValueError as exc:
                return EngineResult.hata(str(exc))
            return EngineResult(data=kod, explanation="Şablondan kod üretildi.")
        if islem == "hata_ayikla":
            oneriler = self.hata_ayikla(
                str(girdi.get("kod", "")), str(girdi.get("hata", ""))
            )
            return EngineResult(data=oneriler,
                                explanation=f"{len(oneriler)} hata ayıklama önerisi.")
        analiz = self.analiz_et(str(girdi.get("kod", "")))
        ozet = (
            f"{len(analiz.fonksiyonlar)} fonksiyon, {len(analiz.siniflar)} sınıf, "
            f"karmaşıklık {analiz.karmasiklik}; {len(analiz.bulgular)} bulgu."
        )
        return EngineResult(
            data=analiz, ok=not any("hatası" in b for b in analiz.bulgular),
            explanation=ozet,
        )
