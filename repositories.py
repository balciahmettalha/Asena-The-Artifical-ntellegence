"""Bilişsel Döngü (Cognitive Cycle).

Her kullanıcı girdisi şu döngüden geçer::

    Algıla → Anla → Hatırla → Akıl Yürüt → Hipotez → Simüle →
    Kontrol → Yanıtla → Öğren → Belleği Güncelle

Döngünün her adımı iz kaydına yazılır; böylece ASENA yanıtına nasıl
ulaştığını açıklayabilir.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from asena.syntax.internal_language import IcTemsil
from asena.syntax.morphology import tr_lower

if TYPE_CHECKING:
    from asena.core.cognitive_core import CognitiveCore


@dataclass
class Yanit:
    """Bilişsel döngünün ürettiği yanıt."""

    metin: str
    guven: float
    niyet: str
    iz: list[tuple[str, str]] = field(default_factory=list)
    kavramlar: list[str] = field(default_factory=list)


class CognitiveCycle:
    """Girdiden yanıta giden tam bilişsel hattı yönetir."""

    def __init__(self, cekirdek: "CognitiveCore") -> None:
        self.c = cekirdek

    # ------------------------------------------------------------------ döngü
    def calis(self, metin: str) -> Yanit:
        """Tam bilişsel döngüyü çalıştırır."""
        iz: list[tuple[str, str]] = []

        # 1. Algıla — predictive ön-işlem varsa kullan
        cumleler = None
        if self.c.predictive is not None:
            cumleler = self.c.predictive.hazir_sonuc(metin)
            if cumleler is not None:
                iz.append(("algıla", "Ön-işlenmiş çözümleme kullanıldı (predictive)."))
        if cumleler is None:
            cumleler = self.c.motor("syntax_engine").metin_cozumle(metin)
            iz.append(("algıla", f"{len(cumleler)} cümle çözümlendi."))

        # 2. Anla — iç temsil diline çevir
        temsil: IcTemsil = self.c.motor("internal_language").cevir(metin, cumleler)
        iz.append(("anla", f"Niyet: {temsil.niyet}; kavramlar: {temsil.kavramlar}"))

        # 3. Hatırla — bilinmeyen kökleri belleğe işle, bilinenleri çağır
        self._bilinmeyenleri_isle(cumleler)
        iliskili = self._iliskili_bilgiler(temsil)
        iz.append(("hatırla", f"{len(iliskili)} ilişkili bilgi çağrıldı."))

        # 4–8. Niyete göre akıl yürüt → hipotez → simüle → kontrol → yanıtla
        metin_yanit, guven = self._niyete_gore_yanitla(temsil, iliskili, iz)

        # 9. Öz değerlendirme
        degerlendirme = self.c.motor("self_evaluation").degerlendir(
            metin, metin_yanit, guven, temsil.kavramlar,
        )
        guven = degerlendirme.puan
        if degerlendirme.notlar:
            iz.append(("kontrol", "; ".join(degerlendirme.notlar)))
        esik = float(self.c.ayarlar.get("cikarim.guven_esigi", 0.4))
        if guven < esik and "emin değilim" not in metin_yanit:
            metin_yanit += "\n(Not: Bu yanıttan tam emin değilim; daha fazla bilgiyle güçlendirebilirim.)"

        # 10. Öğren ve belleği güncelle
        self._ogren(temsil)
        iz.append(("öğren", "Bellek güncellendi."))
        self.c.bus.publish(_olay("dongu.tamamlandi", temsil.niyet, guven))

        return Yanit(metin=metin_yanit, guven=guven, niyet=temsil.niyet,
                     iz=iz, kavramlar=temsil.kavramlar)

    # ------------------------------------------------------------------ yardımcılar
    def _bilinmeyenleri_isle(self, cumleler: list[Any]) -> None:
        bellek = self.c.motor("memory_engine")
        for cumle in cumleler:
            for coz in cumle.cozumlemeler:
                if not coz.kok_bilinen and coz.kok and len(coz.kok) > 2:
                    bellek.bilinmeyen_kaydet(coz.kok)

    def _iliskili_bilgiler(self, temsil: IcTemsil) -> list[str]:
        bellek = self.c.motor("memory_engine")
        bulunan: list[str] = []
        for kavram in temsil.kavramlar[:5]:
            for kayit in bellek.bilgi_ara(kavram, limit=3):
                bulunan.append(str(kayit["onerme"]))
        return bulunan[:10]

    def _ogren(self, temsil: IcTemsil) -> None:
        """Bildirimleri bilgi olarak öğrenir.

        - ``x = y`` atamaları: değişken değeri olarak kaydedilir.
        - ``X Y-dir`` önermeleri: bellek önermesi + graf üst-tür kenarı.
        """
        if temsil.niyet != "bildirim":
            return
        bellek = self.c.motor("memory_engine")
        atama = temsil.parametreler.get("atama")
        if atama:
            degisken, deger = atama
            ogrenme = self.c.motor("learning_engine")
            ogrenme.kelime_ogren(degisken, kok=degisken, anlam=str(deger))
            bellek.bilgi_kaydet(degisken, "değeri", nesne=str(deger),
                                kaynak="kullanici")
            return
        graf = self.c.motor("knowledge_graph")
        sozluk = self.c.motor("turkish_language")
        for uclu in temsil.ucluler:
            if not uclu.ozne or uclu.ozne == "?" or not uclu.yuklem:
                continue
            hedef = uclu.nesne or uclu.yuklem
            # Yüklem ad köküyse üst-tür ilişkisi olarak öğren.
            if sozluk.tur_tespit(hedef) == "isim" and uclu.ozne != hedef:
                graf.kenar_ekle(tr_lower(uclu.ozne), tr_lower(hedef), "ust_tur")
                bellek.bilgi_kaydet(tr_lower(uclu.ozne), "bir " + tr_lower(hedef),
                                    kaynak="kullanici")

    # ------------------------------------------------------------------ niyetler
    def _niyete_gore_yanitla(self, temsil: IcTemsil, iliskili: list[str],
                             iz: list[tuple[str, str]]) -> tuple[str, float]:
        niyet = temsil.niyet
        if niyet == "selamlasma":
            duygu = self.c.motor("sentiment_analysis").cozumle(temsil.ham_metin)
            iz.append(("akıl yürüt", f"Duygu çözümlendi: {duygu.duygu}"))
            selam = "Merhaba! Ben ASENA. Size nasıl yardımcı olabilirim?"
            if duygu.duygu == "mutlu":
                selam = "Merhaba! Enerjiniz çok güzel; size nasıl yardımcı olabilirim?"
            elif duygu.duygu == "uzgun":
                selam = "Merhaba. Buradayım; elimden gelen desteği sunarım."
            return (selam, 0.95)

        if niyet == "hesaplama":
            sonuc = self.c.motor("math_expert").process(temsil.ham_metin)
            iz.append(("akıl yürüt", "Matematik uzmanı devreye alındı."))
            return (sonuc.explanation, sonuc.confidence)

        if niyet == "tanim_sorusu":
            return self._tanim_yanitla(temsil, iliskili, iz)

        if niyet == "neden_sorusu":
            return self._neden_yanitla(temsil, iz)

        if niyet == "emir":
            hedef = self.c.motor("goal_engine").hedef_olustur(temsil.ham_metin)
            iz.append(("akıl yürüt", f"Hedef planlandı: {len(hedef.adimlar)} adım."))
            adimlar = "\n".join(f"  {i + 1}. {a}" for i, a in enumerate(hedef.adimlar))
            return (f"Hedefi planladım:\n{adimlar}", 0.7)

        if niyet == "bildirim":
            if temsil.parametreler.get("atama"):
                d, v = temsil.parametreler["atama"]
                iz.append(("öğren", f"'{d}' için değer kaydedildi."))
                return (f"Anladım; '{d}' için '{v}' değerini kaydettim.", 0.9)
            return ("Anladım, not aldım.", 0.6)

        # soru (genel)
        return self._soru_yanitla(temsil, iliskili, iz)

    def _tanim_yanitla(self, temsil: IcTemsil, iliskili: list[str],
                       iz: list[tuple[str, str]]) -> tuple[str, float]:
        konu = next(
            (k for k in temsil.kavramlar if k not in {"ne", "nedir", "kimdir"}),
            None,
        )
        if konu is None and temsil.ucluler:
            konu = temsil.ucluler[0].ozne
        if konu is None or konu == "?":
            return ("Neyi tanımlamamı istediğinizi anlayamadım.", 0.2)
        iz.append(("akıl yürüt", f"Tanım konusu: {konu}"))
        anlam_ag = self.c.motor("semantic_network")
        cumleler = anlam_ag.acikla(konu)
        zincir = self.c.motor("concept_engine").zincir(konu)
        bolumler: list[str] = []
        if len(zincir) > 1:
            bolumler.append(f"Kavram zinciri: {' → '.join(zincir)}.")
        if cumleler:
            bolumler.extend(cumleler[:4])
        if iliskili:
            bolumler.append("Bellekteki ilgili bilgiler: " + "; ".join(iliskili[:3]))
        if not bolumler:
            analoji = self.c.motor("analogy_engine").acikla_ile(konu)
            iz.append(("hipotez", "Doğrudan bilgi yok; benzetim denendi."))
            return (
                f"'{konu}' hakkında doğrudan bilgim yok. {analoji}",
                0.35,
            )
        return ("\n".join(bolumler), 0.8)

    def _neden_yanitla(self, temsil: IcTemsil,
                       iz: list[tuple[str, str]]) -> tuple[str, float]:
        olgu = next(
            (k for k in temsil.kavramlar
             if k not in {"neden", "niçin", "yağmak"}),
            None,
        )
        if olgu is None and temsil.ucluler:
            olgu = temsil.ucluler[0].ozne
        if olgu is None:
            return ("Nedenini merak ettiğiniz olguyu anlayamadım.", 0.2)
        iz.append(("akıl yürüt", f"Nedensellik zinciri kuruluyor: {olgu}"))
        aciklama = self.c.motor("causal_chain").acikla(olgu)
        zincir = self.c.motor("causal_chain").neden_zinciri(olgu)
        guven = 0.8 if len(zincir) > 1 else 0.35
        return (aciklama, guven)

    def _soru_yanitla(self, temsil: IcTemsil, iliskili: list[str],
                      iz: list[tuple[str, str]]) -> tuple[str, float]:
        bellek = self.c.motor("memory_engine")
        onermeler = [
            f"{k['ozne']} {k['nesne'] or ''} {k['yuklem']}".replace("  ", " ").strip()
            for k in bellek.bilgiler.tumu() if bellek.bilgiler is not None
        ]
        kurallar = [
            f"{k['kosul']} => {k['sonuc']}" for k in bellek.kurallar_tumu()
        ]
        iz_ = self.c.motor("reason_engine").dusun(
            temsil.ham_metin, onermeler, kurallar, iliskili,
        )
        iz.extend(("akıl yürüt", f"{ad}: {detay}") for ad, detay in iz_.adimlar)
        if iz_.sonuc:
            return (f"Akıl yürütme sonucum: {iz_.sonuc}", iz_.guven)
        if iliskili:
            return ("Elimde şu bilgiler var: " + "; ".join(iliskili[:3]), 0.5)
        hipotez = self.c.motor("multiple_hypotheses").uret(
            temsil.ham_metin,
            {"varsayim": [f"'{temsil.ham_metin}' için daha fazla bilgi gerekli"]},
        )
        iz.append(("hipotez", f"{len(hipotez)} hipotez üretildi."))
        return (
            "Bu soruyu yanıtlamak için bilgi tabanımda yeterli veri yok. "
            "Bana bu konuyu öğretebilir veya eğitim modunda metin verebilirsiniz.",
            0.3,
        )


def _olay(ad: str, niyet: str, guven: float):
    from asena.core.event_bus import Event

    return Event(name=ad, payload={"niyet": niyet, "guven": guven},
                 source="cognitive_cycle")
