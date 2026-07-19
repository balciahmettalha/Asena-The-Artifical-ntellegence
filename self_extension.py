"""Dünya Modeli (World Model).

Dünyanın nasıl işlediğine dair iç model: fiziksel neden-sonuç örüntüleri,
insan davranış kalıpları ve mekânsal ilişkiler. Kurallar (koşul → sonuç)
zincirleridir; sebep-sonuç ve dünya simülasyonu motorları bu modeli
kullanır.
"""

from __future__ import annotations

from typing import Any

from asena.engine.base import BaseEngine, EngineResult

# (koşul, sonuç, açıklama)
DUNYA_KURALLARI: list[tuple[str, str, str]] = [
    ("yağmur", "yer ıslanır", "Yağmur yere düşünce yüzeyi ıslatır."),
    ("yer ıslanır", "kayganlaşır", "Islak yüzeyler sürtünmeyi azaltır."),
    ("kayganlaşır", "düşme riski artar", "Sürtünme azalınca denge zorlaşır."),
    ("yağmur", "şemsiye gerekir", "Yağmurda ıslanmamak için şemsiye kullanılır."),
    ("güneş", "ısınır", "Güneş ışınları enerji taşır."),
    ("ısınır", "buharlaşır", "Isınan su buharlaşır."),
    ("su donar", "buz olur", "Su 0°C altında katılaşır."),
    ("ateş", "yakar", "Ateş yanıcı maddeleri tutuşturur."),
    ("yer çekimi", "nesneler düşer", "Kütleler birbirini çeker."),
    ("nesneler düşer", "elma düştü", "Daldan kopan elma yere düşer."),
    ("elma düştü", "yer çekimi", "Düşmenin sebebi yer çekimidir."),
    ("elektrik", "manyetik alan", "Akan yük manyetik alan oluşturur."),
    ("manyetizma", "elektrik akımı", "Değişen manyetik alan akım indükler."),
    ("çalışmak", "başarı", "Düzenli emek beceriyi artırır."),
    ("uyku", "dinlenme", "Uyku bedeni ve zihni onarır."),
    ("öğrenmek", "bilgi artar", "Yeni veri bilgi ağını büyütür."),
]

# İnsan davranış örüntüleri: (durum, olası davranış)
DAVRANIS_ORUNTULERI: list[tuple[str, str]] = [
    ("acıkan insan", "yemek arar"),
    ("yorulan insan", "dinlenmek ister"),
    ("korkan insan", "kaçar veya donakalır"),
    ("merak eden insan", "soru sorar"),
]

# Mekânsal ilişkiler: (iç mekân, beklenen nesneler)
MEKAN_ILISKILERI: dict[str, list[str]] = {
    "mutfak": ["bardak", "tabak", "ocak"],
    "okul": ["kitap", "kalem", "öğretmen", "öğrenci"],
    "ev": ["kapı", "pencere", "masa"],
}


class WorldModel(BaseEngine):
    """Neden-sonuç ve örüntü bilgisini tutan iç dünya modeli."""

    name = "world_model"
    group = "knowledge"

    def __init__(self) -> None:
        super().__init__()
        self._zincir: dict[str, list[tuple[str, str]]] = {}
        for kosul, sonuc, aciklama in DUNYA_KURALLARI:
            self._zincir.setdefault(kosul, []).append((sonuc, aciklama))

    def kural_ekle(self, kosul: str, sonuc: str, aciklama: str = "") -> None:
        """Modele yeni neden-sonuç kuralı ekler (öğrenme ile büyür)."""
        self._zincir.setdefault(kosul, []).append((sonuc, aciklama))

    def sonuclar(self, olay: str, derinlik: int = 4) -> list[str]:
        """Bir olayın olası sonuçlarını zincirleme yayar (BFS)."""
        sonuclar: list[str] = []
        gorulen = {olay}
        sinir = [olay]
        for _ in range(derinlik):
            yeni: list[str] = []
            for durum in sinir:
                for sonuc, _aciklama in self._zincir.get(durum, []):
                    if sonuc not in gorulen:
                        gorulen.add(sonuc)
                        sonuclar.append(sonuc)
                        yeni.append(sonuc)
            sinir = yeni
        return sonuclar

    def sebep_bul(self, sonuc: str) -> list[str]:
        """Bir sonucu doğuran bilinen koşulları döndürür."""
        return [
            kosul for kosul, liste in self._zincir.items()
            if any(s == sonuc for s, _ in liste)
        ]

    def davranis_ongor(self, durum: str) -> list[str]:
        return [d for d_durum, d in DAVRANIS_ORUNTULERI if d_durum == durum]

    def mekanda_ne_var(self, mekan: str) -> list[str]:
        return list(MEKAN_ILISKILERI.get(mekan, []))

    def process(self, girdi: dict[str, Any], **kwargs: Any) -> EngineResult:
        islem = girdi.get("islem", "sonuclar")
        if islem == "sebep":
            veri = self.sebep_bul(str(girdi.get("sonuc", "")))
            return EngineResult(data=veri, explanation=f"{len(veri)} sebep bulundu.")
        veri = self.sonuclar(str(girdi.get("olay", "")))
        return EngineResult(data=veri, explanation=f"{len(veri)} olası sonuç.")
