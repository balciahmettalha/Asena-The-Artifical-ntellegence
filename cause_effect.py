"""Mantık Motoru (Logic Engine).

Birinci dereceden mantığın pragmatik bir alt kümesini uygular: önermeler
``(özne, yüklem, nesne)`` üçlüsüdür; kurallar ``koşul(lar) → sonuç``
biçimindedir ve ``?x`` değişkenleriyle şablonlaşır. Modus ponens (ileri
zincirleme) ve modus tollens (geri çıkarım) desteklenir.

Kural metin biçimi::

    "?x insandır => ?x ölümlüdür"
    "?x kuştur; ?x kanatlıdır => ?x uçabilir"
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from asena.engine.base import BaseEngine, EngineResult

DEGISKEN_ON_EK = "?"


@dataclass(frozen=True)
class Onerme:
    """Atomik önerme: ``(özne, yüklem, nesne)`` + olumsuzluk işareti."""

    ozne: str
    yuklem: str
    nesne: str | None = None
    olumsuz: bool = False

    def __str__(self) -> str:
        parcalar = [self.ozne, self.nesne or "", self.yuklem]
        metin = " ".join(p for p in parcalar if p)
        return f"¬{metin}" if self.olumsuz else metin

    @classmethod
    def coz(cls, metin: str) -> "Onerme":
        """Metinden önerme ayrıştırır: ``¬özne [nesne] yüklem``."""
        olumsuz = metin.strip().startswith("¬")
        if olumsuz:
            metin = metin.strip()[1:]
        parcalar = metin.strip().split()
        if len(parcalar) == 1:
            return cls(parcalar[0], "vardır")
        if len(parcalar) == 2:
            return cls(parcalar[0], parcalar[1], olumsuz=olumsuz)
        return cls(parcalar[0], parcalar[-1], " ".join(parcalar[1:-1]),
                   olumsuz=olumsuz)


@dataclass(frozen=True)
class Kural:
    """Çıkarım kuralı: koşul önermeleri → sonuç önermesi."""

    kosullar: tuple[Onerme, ...]
    sonuc: Onerme
    guven: float = 1.0

    @classmethod
    def coz(cls, metin: str, guven: float = 1.0) -> "Kural":
        """``"koşul1;koşul2 => sonuc"`` biçimini ayrıştırır."""
        sol, sag = metin.split("=>", 1)
        kosullar = tuple(
            Onerme.coz(p) for p in sol.split(";") if p.strip()
        )
        return cls(kosullar=kosullar, sonuc=Onerme.coz(sag), guven=guven)


def _eslestir(kalip: Onerme, onerme: Onerme,
              baglama: dict[str, str]) -> dict[str, str] | None:
    """Şablon ile önermeyi birleştirir (unification)."""
    if kalip.yuklem != onerme.yuklem or kalip.olumsuz != onerme.olumsuz:
        return None
    yeni = dict(baglama)
    for k_deger, o_deger in ((kalip.ozne, onerme.ozne), (kalip.nesne, onerme.nesne)):
        if k_deger is None:
            continue
        if k_deger.startswith(DEGISKEN_ON_EK):
            if o_deger is None:
                return None
            if k_deger in yeni and yeni[k_deger] != o_deger:
                return None
            yeni[k_deger] = o_deger
        elif k_deger != o_deger:
            return None
    return yeni


def _uygula(kalip: Onerme, baglama: dict[str, str]) -> Onerme:
    """Şablondaki değişkenleri bağlamayla somutlaştırır."""

    def coz(deger: str | None) -> str | None:
        if deger is not None and deger.startswith(DEGISKEN_ON_EK):
            return baglama.get(deger, deger)
        return deger

    return Onerme(coz(kalip.ozne) or "", kalip.yuklem, coz(kalip.nesne),
                  kalip.olumsuz)


class LogicEngine(BaseEngine):
    """Sembolik çıkarım yapan mantık motoru."""

    name = "logic_engine"
    group = "logic"

    # ------------------------------------------------------------- modus ponens
    def modus_ponens(self, onermeler: Iterable[Onerme],
                     kurallar: Iterable[Kural],
                     tur_siniri: int = 10) -> list[Onerme]:
        """İleri zincirleme: yeni önermeler tükenene kadar türetir.

        Returns:
            Bilinenler + türetilenlerin tam listesi.
        """
        taban = list(onermeler)
        kume = set(taban)
        for _ in range(tur_siniri):
            yeni_uretildi = False
            for kural in kurallar:
                for sonuc, guven in self._kural_uygula(kural, taban):
                    if sonuc not in kume:
                        kume.add(sonuc)
                        taban.append(sonuc)
                        yeni_uretildi = True
            if not yeni_uretildi:
                break
        return taban

    def _kural_uygula(self, kural: Kural,
                      taban: list[Onerme]) -> list[tuple[Onerme, float]]:
        """Tek kuralı tabana uygular; (yeni önerme, güven) listesi verir."""
        sonuclar: list[tuple[Onerme, float]] = []
        baglamalar: list[dict[str, str]] = [{}]
        for kosul in kural.kosullar:
            yeni_baglamalar: list[dict[str, str]] = []
            for baglama in baglamalar:
                for onerme in taban:
                    eslesme = _eslestir(kosul, onerme, baglama)
                    if eslesme is not None:
                        yeni_baglamalar.append(eslesme)
            baglamalar = yeni_baglamalar
        for baglama in baglamalar:
            sonuclar.append((_uygula(kural.sonuc, baglama), kural.guven))
        return sonuclar

    # ------------------------------------------------------------- modus tollens
    def modus_tollens(self, onermeler: Iterable[Onerme],
                      kurallar: Iterable[Kural]) -> list[Onerme]:
        """Geri çıkarım: ``koşul → sonuc`` ve ``¬sonuc`` ise ``¬koşul``.

        Yalnızca değişkensiz (somut) kurallarda uygulanır.
        """
        taban = list(onermeler)
        olumsuzlar = {o for o in taban if o.olumsuz}
        yeni: list[Onerme] = []
        for kural in kurallar:
            sonucun_olumsuzu = Onerme(
                kural.sonuc.ozne, kural.sonuc.yuklem,
                kural.sonuc.nesne, olumsuz=True,
            )
            if sonucun_olumsuzu not in olumsuzlar:
                continue
            for kosul in kural.kosullar:
                if not kosul.ozne.startswith(DEGISKEN_ON_EK):
                    aday = Onerme(kosul.ozne, kosul.yuklem, kosul.nesne,
                                  olumsuz=True)
                    if aday not in taban and aday not in yeni:
                        yeni.append(aday)
        return yeni

    # ------------------------------------------------------------------ tutarlılık
    def tutarli_mi(self, onerme: Onerme, taban: Iterable[Onerme]) -> bool:
        """Önerme tabanla açıkça çelişiyor mu? (olumlu/olumsuz çifti)"""
        zit = Onerme(onerme.ozne, onerme.yuklem, onerme.nesne,
                     olumsuz=not onerme.olumsuz)
        return zit not in set(taban)

    def process(self, girdi: dict[str, Any], **kwargs: Any) -> EngineResult:
        onermeler = [Onerme.coz(m) for m in girdi.get("onermeler", [])]
        kurallar = [Kural.coz(m) for m in girdi.get("kurallar", [])]
        islem = girdi.get("islem", "ponens")
        if islem == "tollens":
            sonuc = self.modus_tollens(onermeler, kurallar)
        else:
            onceki = len(onermeler)
            tumu = self.modus_ponens(onermeler, kurallar)
            sonuc = tumu[onceki:]
        metinler = [str(o) for o in sonuc]
        return EngineResult(
            data=metinler,
            explanation=f"{len(metinler)} yeni önerme türetildi: {metinler}",
        )
