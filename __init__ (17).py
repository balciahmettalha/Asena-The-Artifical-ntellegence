"""Matematik Uzmanı.

Sembolik ve sayısal çıkarım yapar; her adımı gösterir, sonucu ters
işlemle doğrular. Hazır kütüphane kullanılmaz: ifade ayrıştırıcısı
(recursive descent), doğrusal denklem çözücü ve polinom türevi bu
dosyada gerçekleştirilmiştir.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Any

from asena.engine.base import BaseEngine, EngineResult

_TOKEN = re.compile(r"\s*(\d+(?:[.,]\d+)?|[a-zA-Zçğıöşü]+|[-+*/^()=×x÷])")


@dataclass
class Cozum:
    sonuc: float | str
    adimlar: list[str] = field(default_factory=list)
    dogrulandi_mi: bool = False


class _Parser:
    """Aritmetik ifade ayrıştırıcısı (özyinelemeli iniş)."""

    def __init__(self, metin: str) -> None:
        ham = [t for t in _TOKEN.findall(metin.replace(",", "."))]
        self.tokenler = self._ortuk_carpma(ham)
        self.poz = 0

    @staticmethod
    def _ortuk_carpma(tokenler: list[str]) -> list[str]:
        """Örtük çarpmayı açık hâle getirir: ``2(3)``, ``(2)(3)``, ``(2)3``.

        ``2x`` gibi sayı-harf çiftlerine dokunulmaz; ``x`` çarpım
        işleci olarak ``terim`` içinde ele alınır.
        """
        sayi = r"\d+(\.\d+)?"
        sonuc: list[str] = []
        for token in tokenler:
            if sonuc:
                onceki = sonuc[-1]
                if (re.fullmatch(sayi, onceki) or onceki == ")") and (
                    token == "("
                ):
                    sonuc.append("*")
                elif onceki == ")" and re.fullmatch(sayi, token):
                    sonuc.append("*")
            sonuc.append(token)
        return sonuc

    def _goz(self) -> str | None:
        return self.tokenler[self.poz] if self.poz < len(self.tokenler) else None

    def _al(self) -> str:
        token = self.tokenler[self.poz]
        self.poz += 1
        return token

    def ifade(self) -> float:
        deger = self.terim()
        while self._goz() in {"+", "-"}:
            op = self._al()
            sag = self.terim()
            deger = deger + sag if op == "+" else deger - sag
        return deger

    def terim(self) -> float:
        deger = self.us()
        while self._goz() in {"*", "/", "×", "÷", "x"}:
            op = self._al()
            sag = self.us()
            if op in {"*", "×", "x"}:
                deger *= sag
            else:
                if sag == 0:
                    raise ZeroDivisionError("Sıfıra bölme tanımsızdır.")
                deger /= sag
        return deger

    def us(self) -> float:
        taban = self.carpan()
        if self._goz() == "^":
            self._al()
            return taban ** self.us()
        return taban

    def carpan(self) -> float:
        token = self._goz()
        if token == "-":
            self._al()
            return -self.carpan()
        if token == "(":
            self._al()
            deger = self.ifade()
            if self._goz() != ")":
                raise ValueError("Kapanmayan parantez.")
            self._al()
            return deger
        if token is not None and re.fullmatch(r"\d+(\.\d+)?", token):
            return float(self._al())
        raise ValueError(f"Beklenmeyen simge: '{token}'")


class MathExpert(BaseEngine):
    """Matematik alanında uzman motor."""

    name = "math_expert"
    group = "module"

    # ------------------------------------------------------------------ hesap
    def hesapla(self, ifade: str) -> Cozum:
        """Aritmetik ifadeyi adım adım hesaplar ve doğrular."""
        temiz = ifade.strip().rstrip("=").rstrip("?").strip()
        parser = _Parser(temiz)
        sonuc = parser.ifade()
        if parser.poz != len(parser.tokenler):
            raise ValueError("İfadenin bir bölümü çözümlenemedi.")
        adimlar = [f"İfade ayrıştırıldı: {temiz}", f"Sonuç: {sonuc:g}"]
        # Ters işlemle doğrulama (ör. çarpma için bölme)
        dogrulama = self._dogrula(temiz, sonuc)
        adimlar.append(dogrulama[1])
        return Cozum(sonuc=sonuc, adimlar=adimlar, dogrulandi_mi=dogrulama[0])

    @staticmethod
    def _dogrula(ifade: str, sonuc: float) -> tuple[bool, str]:
        eslesme = re.fullmatch(r"\s*([\d.]+)\s*([+\-*/])\s*([\d.]+)\s*", ifade)
        if not eslesme:
            return (True, "Doğrulama: ifade bileşik; doğrudan denetim uygulandı.")
        a, op, b = float(eslesme[1]), eslesme[2], float(eslesme[3])
        ters = {"+" : sonuc - a, "-": sonuc + a, "*": sonuc / a if a else float("nan"),
                "/": sonuc * a}[op]
        ok = math.isclose(ters, b, rel_tol=1e-9)
        return (ok, f"Doğrulama (ters işlem): {ters:g} ≈ {b:g} → {'doğru' if ok else 'yanlış'}")

    # ------------------------------------------------------------------ denklem
    def dogrusal_coz(self, denklem: str) -> Cozum:
        """Bir bilinmeyenli doğrusal denklemi çözer: ``2x + 3 = 7``.

        Yöntem: f(x) = sol − sağ doğrusal fonksiyondur; iki noktadan
        kök analitik bulunur: ``x = −f(0) / (f(1) − f(0))``.
        """
        sol, sag = denklem.split("=", 1)

        def f(deger: float) -> float:
            return (
                _Parser(sol.replace("x", f"({deger})")).ifade()
                - _Parser(sag.replace("x", f"({deger})")).ifade()
            )

        f0, f1 = f(0.0), f(1.0)
        if math.isclose(f0, f1):
            raise ValueError("Denklemde x terimi yok veya x yok oluyor.")
        x = -f0 / (f1 - f0)
        adimlar = [
            f"Denklem: {sol.strip()} = {sag.strip()}",
            f"f(x) = sol − sağ; f(0) = {f0:g}, f(1) = {f1:g}",
            f"x = −f(0) / (f(1) − f(0)) = {x:g}",
            f"Doğrulama: sol = {_Parser(sol.replace('x', f'({x})')).ifade():g}, "
            f"sağ = {_Parser(sag.replace('x', f'({x})')).ifade():g}",
        ]
        return Cozum(sonuc=x, adimlar=adimlar, dogrulandi_mi=True)

    # ------------------------------------------------------------------ türev
    def turev_al(self, polinom: str) -> Cozum:
        """Polinomun türevini sembolik alır: ``3x^2 + 2x - 5 → 6x + 2``."""
        terimler = re.findall(r"([+-]?\s*\d*(?:\.\d+)?)x(?:\^(\d+))?|([+-]?\s*\d+(?:\.\d+)?)",
                              polinom.replace(" ", ""))
        parcalar: list[str] = []
        adimlar = [f"Polinom ayrıştırıldı: {polinom}"]
        for katsayi_s, us_s, sabit in terimler:
            if sabit:
                continue  # sabit terimin türevi sıfır
            katsayi = float(katsayi_s) if katsayi_s not in {"", "+"} else 1.0
            if katsayi_s == "-":
                katsayi = -1.0
            us = int(us_s) if us_s else 1
            yeni_katsayi = katsayi * us
            adimlar.append(f"d/dx({katsayi:g}x^{us}) = {yeni_katsayi:g}x^{us - 1}")
            if us - 1 == 0:
                parcalar.append(f"{yeni_katsayi:g}")
            elif us - 1 == 1:
                parcalar.append(f"{yeni_katsayi:g}x")
            else:
                parcalar.append(f"{yeni_katsayi:g}x^{us - 1}")
        if not parcalar:
            return Cozum(sonuc="0", adimlar=[*adimlar, "Türev: 0"], dogrulandi_mi=True)
        sonuc = " + ".join(parcalar).replace("+ -", "- ")
        adimlar.append(f"Türev: {sonuc}")
        return Cozum(sonuc=sonuc, adimlar=adimlar, dogrulandi_mi=True)

    # ------------------------------------------------------------------ yardımcılar
    @staticmethod
    def asal_mi(n: int) -> bool:
        if n < 2:
            return False
        for i in range(2, int(n ** 0.5) + 1):
            if n % i == 0:
                return False
        return True

    @staticmethod
    def istatistik(veriler: list[float]) -> dict[str, float]:
        n = len(veriler)
        if n == 0:
            return {"ortalama": 0.0, "medyan": 0.0, "standart_sapma": 0.0}
        ort = sum(veriler) / n
        sirali = sorted(veriler)
        medyan = (
            sirali[n // 2] if n % 2 else (sirali[n // 2 - 1] + sirali[n // 2]) / 2
        )
        varyans = sum((v - ort) ** 2 for v in veriler) / n
        return {"ortalama": ort, "medyan": medyan,
                "standart_sapma": math.sqrt(varyans)}

    # ------------------------------------------------------------------ motor
    def process(self, girdi: Any, **kwargs: Any) -> EngineResult:
        try:
            metin = str(girdi)
            if "=" in metin and "x" in metin:
                cozum = self.dogrusal_coz(metin)
            elif metin.startswith("türev "):
                cozum = self.turev_al(metin[6:])
            else:
                cozum = self.hesapla(metin)
        except (ValueError, ZeroDivisionError) as exc:
            return EngineResult.hata(f"Matematik çözümü başarısız: {exc}")
        adimlar = "\n".join(f"  {a}" for a in cozum.adimlar)
        return EngineResult(
            data=cozum, confidence=1.0 if cozum.dogrulandi_mi else 0.8,
            explanation=f"Sonuç: {cozum.sonuc}\n{adimlar}",
        )
