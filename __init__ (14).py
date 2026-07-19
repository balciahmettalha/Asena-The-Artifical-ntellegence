"""Anlam Ağı (Semantic Network).

Her kelimenin binlerce ilişkisini tutma hedefinin çekirdeğidir. Tohum
ilişkilerle başlar; eğitim ve sohbetle büyür. İlişkiler bilgi grafiğinde
saklanır; bu motor anlama ve açıklama kolaylığı sağlar.
"""

from __future__ import annotations

from typing import Any

from asena.engine.base import BaseEngine, EngineResult
from asena.knowledge.knowledge_graph import KnowledgeGraph

# Tohum ilişkiler: (kaynak, hedef, tür, ağırlık)
TOHUM_ILISKILER: list[tuple[str, str, str, float]] = [
    ("su", "sıvı", "ozellik", 0.9), ("su", "içmek", "eylem", 0.8),
    ("su", "renksiz", "ozellik", 0.7), ("su", "h2o", "formul", 1.0),
    ("su", "donmak", "donusum", 0.6), ("su", "buharlaşmak", "donusum", 0.6),
    ("su", "yaşam", "gereksinim", 1.0), ("su", "yağmur", "bicim", 0.7),
    ("kedi", "hayvan", "ust_tur", 1.0), ("kedi", "miyavlamak", "ses", 0.9),
    ("kedi", "evcil", "ozellik", 0.8), ("kedi", "etçil", "beslenme", 0.7),
    ("köpek", "hayvan", "ust_tur", 1.0), ("köpek", "havlamak", "ses", 0.9),
    ("köpek", "sadık", "ozellik", 0.8),
    ("aslan", "kedigiller", "ust_tur", 1.0), ("kaplan", "kedigiller", "ust_tur", 1.0),
    ("kedigiller", "hayvan", "ust_tur", 1.0), ("hayvan", "canlı", "ust_tur", 1.0),
    ("kuş", "hayvan", "ust_tur", 1.0), ("kuş", "uçmak", "yetenek", 0.8),
    ("balık", "hayvan", "ust_tur", 1.0), ("balık", "yüzmek", "yetenek", 0.9),
    ("balık", "su", "yaşam_alanı", 0.9),
    ("elma", "meyve", "ust_tur", 1.0), ("armut", "meyve", "ust_tur", 1.0),
    ("meyve", "bitki", "ust_tur", 0.9), ("bitki", "canlı", "ust_tur", 1.0),
    ("ağaç", "bitki", "ust_tur", 1.0),
    ("insan", "canlı", "ust_tur", 1.0), ("insan", "düşünmek", "yetenek", 1.0),
    ("insan", "konuşmak", "yetenek", 0.9), ("insan", "beyin", "organ", 0.9),
    ("yağmur", "ıslaklık", "sonuc", 0.9), ("yağmur", "bulut", "kaynak", 0.8),
    ("güneş", "yıldız", "ust_tur", 1.0), ("güneş", "ısı", "kaynak", 0.9),
    ("güneş", "ışık", "kaynak", 0.9),
    ("ay", "uydu", "ust_tur", 1.0), ("dünya", "gezegen", "ust_tur", 1.0),
    ("gezegen", "gök_cismi", "ust_tur", 0.9),
    ("beyin", "düşünmek", "islev", 0.9), ("beyin", "organ", "ust_tur", 1.0),
    ("bilgisayar", "hesaplamak", "islev", 0.9), ("bilgisayar", "kod", "calistirir", 0.8),
    ("elektrik", "enerji", "ust_tur", 0.9), ("manyetizma", "kuvvet", "ust_tur", 0.8),
    ("sıcak", "soğuk", "zit", 1.0), ("büyük", "küçük", "zit", 1.0),
    ("hızlı", "yavaş", "zit", 1.0), ("iyi", "kötü", "zit", 1.0),
    ("güzel", "çirkin", "zit", 1.0), ("uzun", "kısa", "zit", 1.0),
    ("şemsiye", "yağmur", "korunma", 0.9),
    ("kitap", "bilgi", "tasir", 0.8), ("okul", "öğrenmek", "amac", 0.9),
    ("ekmek", "un", "yapim", 0.8), ("ekmek", "yemek", "eylem", 0.8),
]

# İlişki türü → Türkçe cümle kalıbı (ek kodları ünlü uyumuyla üretilir)
CUMLE_KALIPLARI: dict[str, str] = {
    "ozellik": "{k} {h}{DIR}", "ust_tur": "{k} bir {h}{DIR}",
    "eylem": "{k}, {h} eyleminin nesnesidir",
    "formul": "{k}{NIN} formülü {h}{DIR}",
    "donusum": "{k} için {h} bir dönüşümdür",
    "gereksinim": "{k}, {h} için gereklidir",
    "bicim": "{k}, {h} biçiminde görülür",
    "ses": "{k} şu sesi çıkarır: {h}",
    "beslenme": "{k}, {h} olarak beslenir",
    "yetenek": "{k}, {h} yeteneğine sahiptir",
    "yaşam_alanı": "{k}, {h}{DA} yaşar",
    "sonuc": "{k}, {h} oluşturur",
    "kaynak": "{k}, {h} kaynağıdır",
    "zit": "{k}, {h}{NIN} zıddıdır",
    "islev": "{k}{NIN} işlevi {h}{DIR}",
    "tasir": "{k}, {h} taşır",
    "amac": "{k}{NIN} amacı {h}{DIR}",
    "yapim": "{k}, {h}{DAN} yapılır",
    "organ": "{k}{NIN} {h}{YI} vardır",
    "korunma": "{k}, {h}{DAN} korur",
    "calistirir": "{k}, {h} çalıştırır",
    "bilesen": "{k} kavramının bileşeni: {h}",
}

_SERTLER = set("çfhpsştk")


def _son_unlu(kelime: str) -> str:
    for harf in reversed(kelime):
        if harf in "aeıioöuü":
            return harf
    return "a"


def ek_uret(hedef: str, kod: str) -> str:
    """Hedef kelimeye ünlü uyumlu ek üretir (DIR, DA, DAN, NIN, YI)."""
    unlu = _son_unlu(hedef)
    dortlu = {"a": "ı", "e": "i", "o": "u", "ö": "ü",
              "ı": "ı", "i": "i", "u": "u", "ü": "ü"}[unlu]
    ikili = "a" if unlu in "aıou" else "e"
    sert = bool(hedef) and hedef[-1] in _SERTLER
    if kod == "DIR":
        return ("t" if sert else "d") + dortlu + "r"
    if kod == "DA":
        return ("t" if sert else "d") + ikili
    if kod == "DAN":
        return ("t" if sert else "d") + ikili + "n"
    if kod == "NIN":
        return "n" + dortlu + "n"
    if kod == "YI":
        return dortlu
    return kod.lower()


class SemanticNetwork(BaseEngine):
    """Kelime ilişkilerini yöneten ve açıklayan motor."""

    name = "semantic_network"
    group = "knowledge"
    dependencies = ("knowledge_graph",)

    def __init__(self, graf: KnowledgeGraph | None = None) -> None:
        super().__init__()
        self.graf = graf or KnowledgeGraph()
        for kaynak, hedef, tur, agirlik in TOHUM_ILISKILER:
            self.graf.kenar_ekle(kaynak, hedef, tur, agirlik, kalici=False)
        # Zıtlıklar iki yönlüdür
        for kaynak, hedef, tur, _ in TOHUM_ILISKILER:
            if tur == "zit":
                self.graf.kenar_ekle(hedef, kaynak, tur, 1.0, kalici=False)

    # ------------------------------------------------------------------ sorgu
    def iliskiler(self, kelime: str) -> list[dict[str, Any]]:
        """Kelimenin tüm giden ilişkilerini döndürür."""
        return [
            {"hedef": k.hedef, "tur": k.tur, "agirlik": k.agirlik}
            for k in self.graf.komsular(kelime)
        ]

    def iliski_ekle(self, kaynak: str, hedef: str, tur: str,
                    agirlik: float = 1.0) -> None:
        self.graf.kenar_ekle(kaynak, hedef, tur, agirlik)

    def zit_mi(self, a: str, b: str) -> bool:
        return self.graf.iliski_var_mi(a, b, "zit")

    def benzerlik(self, a: str, b: str) -> float:
        """İki kelimenin anlam benzerliği: uzaklık tabanlı 0–1 skor."""
        d = self.graf.anlam_uzakligi_yonsuz(a, b)
        if d is None:
            return 0.0
        return 1.0 / (1.0 + d)

    @staticmethod
    def _cumle_kur(kalip: str, kaynak: str, hedef: str) -> str:
        """Kalıptaki ek kodlarını ünlü uyumuyla çözüp cümle kurar."""
        metin = kalip
        for kod in ("DIR", "DAN", "NIN", "DA", "YI"):
            metin = metin.replace("{" + kod + "}", ek_uret(hedef, kod))
        return metin.format(k=kaynak.capitalize(), h=hedef) + "."

    def acikla(self, kelime: str, en_cok: int = 5) -> list[str]:
        """Kelimeyi ilişkilerinden Türkçe cümleler üreterek açıklar."""
        cumleler: list[str] = []
        for k in sorted(
            self.graf.komsular(kelime), key=lambda x: -x.agirlik
        )[:en_cok]:
            kalip = CUMLE_KALIPLARI.get(k.tur, "{k} ↔ {h}")
            cumleler.append(self._cumle_kur(kalip, kelime, k.hedef))
        return cumleler

    # ------------------------------------------------------------------ motor
    def process(self, girdi: dict[str, Any], **kwargs: Any) -> EngineResult:
        """``{"islem": "acikla"|"iliskiler"|"benzerlik", ...}`` yönlendirmesi."""
        islem = girdi.get("islem", "iliskiler")
        if islem == "acikla":
            cumleler = self.acikla(str(girdi.get("kelime", "")))
            return EngineResult(data=cumleler, explanation="Açıklama üretildi.")
        if islem == "benzerlik":
            skor = self.benzerlik(str(girdi.get("a", "")), str(girdi.get("b", "")))
            return EngineResult(data=skor, confidence=skor,
                                explanation="Benzerlik hesaplandı.")
        iliskiler = self.iliskiler(str(girdi.get("kelime", "")))
        return EngineResult(data=iliskiler, explanation=f"{len(iliskiler)} ilişki.")
