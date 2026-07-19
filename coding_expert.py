"""Bilgi Grafiği (Knowledge Graph).

Bilgiler düğüm, ilişkiler yönlü ve ağırlıklı kenar olarak tutulur. Anlam
uzaklığı, iki düğüm arasındaki en kısa yolun toplam ağırlığıdır. Graf
bellek içi çalışır; kalıcılık istenirse kenarlar ``iliskiler`` tablosuna
yansıtılır ve başlangıçta geri yüklenir.
"""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from typing import Any, Iterable

from asena.engine.base import BaseEngine, EngineResult


@dataclass
class Dugum:
    """Graf düğümü: kelime, kavram veya bilgi."""

    ad: str
    tur: str = "kavram"                  # kelime | kavram | bilgi
    veri: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Kenar:
    kaynak: str
    hedef: str
    tur: str                             # ust_tur | ozellik | sebep | es | zit | ...
    agirlik: float = 1.0


class KnowledgeGraph(BaseEngine):
    """Yönlü, ağırlıklı ve çok türleri destekleyen bilgi grafiği."""

    name = "knowledge_graph"
    group = "knowledge"

    def __init__(self, iliski_repo: Any | None = None) -> None:
        super().__init__()
        self.dugumler: dict[str, Dugum] = {}
        self.giden: dict[str, list[Kenar]] = {}
        self.gelen: dict[str, list[Kenar]] = {}
        self._repo = iliski_repo

    # ------------------------------------------------------------------ düğüm
    def dugum_ekle(self, ad: str, tur: str = "kavram", **veri: Any) -> Dugum:
        dugum = self.dugumler.get(ad)
        if dugum is None:
            dugum = Dugum(ad=ad, tur=tur, veri=dict(veri))
            self.dugumler[ad] = dugum
        else:
            dugum.veri.update(veri)
        return dugum

    # ------------------------------------------------------------------ kenar
    def kenar_ekle(self, kaynak: str, hedef: str, tur: str,
                   agirlik: float = 1.0, *, iki_yonlu_es: bool = False,
                   kalici: bool = True) -> Kenar:
        """İki düğüm arasına ilişki kenarı ekler (tekrarsız)."""
        self.dugum_ekle(kaynak)
        self.dugum_ekle(hedef)
        mevcut = self.giden.setdefault(kaynak, [])
        for kenar in mevcut:
            if kenar.hedef == hedef and kenar.tur == tur:
                return kenar
        kenar = Kenar(kaynak, hedef, tur, agirlik)
        mevcut.append(kenar)
        self.gelen.setdefault(hedef, []).append(kenar)
        if iki_yonlu_es:
            self.kenar_ekle(hedef, kaynak, tur, agirlik, kalici=kalici)
        if kalici and self._repo is not None:
            self._repo.iliski_ekle(kaynak, hedef, tur, agirlik)
        if self._ctx is not None:
            self.ctx.bus.publish(_olay("bilgi.iliski_eklendi", kaynak, hedef, tur))
        return kenar

    def komsular(self, ad: str, tur: str | None = None,
                 yon: str = "giden") -> list[Kenar]:
        kenarlar = self.giden.get(ad, []) if yon == "giden" else self.gelen.get(ad, [])
        return [k for k in kenarlar if tur is None or k.tur == tur]

    def iliski_var_mi(self, kaynak: str, hedef: str, tur: str | None = None) -> bool:
        return any(
            k.hedef == hedef and (tur is None or k.tur == tur)
            for k in self.giden.get(kaynak, [])
        )

    # ------------------------------------------------------------------ uzaklık
    def anlam_uzakligi(self, kaynak: str, hedef: str) -> float | None:
        """İki düğüm arası en kısa ağırlıklı yol (Dijkstra); yoksa ``None``."""
        if kaynak not in self.dugumler or hedef not in self.dugumler:
            return None
        kuyruk: list[tuple[float, str]] = [(0.0, kaynak)]
        mesafe = {kaynak: 0.0}
        while kuyruk:
            d, u = heapq.heappop(kuyruk)
            if u == hedef:
                return d
            if d > mesafe.get(u, float("inf")):
                continue
            for kenar in self.giden.get(u, []):
                yeni = d + kenar.agirlik
                if yeni < mesafe.get(kenar.hedef, float("inf")):
                    mesafe[kenar.hedef] = yeni
                    heapq.heappush(kuyruk, (yeni, kenar.hedef))
        return None

    def anlam_uzakligi_yonsuz(self, kaynak: str, hedef: str) -> float | None:
        """Yön gözetmeyen en kısa ağırlıklı yol (benzerlik hesabı için)."""
        if kaynak not in self.dugumler or hedef not in self.dugumler:
            return None
        kuyruk: list[tuple[float, str]] = [(0.0, kaynak)]
        mesafe = {kaynak: 0.0}
        while kuyruk:
            d, u = heapq.heappop(kuyruk)
            if u == hedef:
                return d
            if d > mesafe.get(u, float("inf")):
                continue
            komsular = [(k.hedef, k.agirlik) for k in self.giden.get(u, [])]
            komsular += [(k.kaynak, k.agirlik) for k in self.gelen.get(u, [])]
            for v, agirlik in komsular:
                yeni = d + agirlik
                if yeni < mesafe.get(v, float("inf")):
                    mesafe[v] = yeni
                    heapq.heappush(kuyruk, (yeni, v))
        return None

    def yol(self, kaynak: str, hedef: str) -> list[str]:
        """İki düğüm arası bir yol (BFS); bulunamazsa boş liste."""
        if kaynak == hedef:
            return [kaynak]
        once: dict[str, str | None] = {kaynak: None}
        kuyruk = [kaynak]
        while kuyruk:
            u = kuyruk.pop(0)
            for kenar in self.giden.get(u, []):
                if kenar.hedef in once:
                    continue
                once[kenar.hedef] = u
                if kenar.hedef == hedef:
                    yol = [hedef]
                    while once[yol[-1]] is not None:
                        yol.append(once[yol[-1]])  # type: ignore[arg-type]
                    return list(reversed(yol))
                kuyruk.append(kenar.hedef)
        return []

    def yayilma(self, ad: str, derinlik: int = 2) -> set[str]:
        """Etkinleşme yayılımı: düğümden ``derinlik`` kadar uzaktaki düğümler."""
        gorulen = {ad}
        sinir = {ad}
        for _ in range(derinlik):
            yeni = set()
            for dugum in sinir:
                for kenar in self.giden.get(dugum, []):
                    yeni.add(kenar.hedef)
                for kenar in self.gelen.get(dugum, []):
                    yeni.add(kenar.kaynak)
            yeni -= gorulen
            gorulen |= yeni
            sinir = yeni
        return gorulen

    # ------------------------------------------------------------------ kalıcılık
    def yukle(self, kenarlar: Iterable[tuple[str, str, str, float]]) -> int:
        """Depodan kenarları grafa yükler; yüklenen sayısını döndürür."""
        n = 0
        for kaynak, hedef, tur, agirlik in kenarlar:
            self.kenar_ekle(kaynak, hedef, tur, agirlik, kalici=False)
            n += 1
        return n

    # ------------------------------------------------------------------ motor
    def process(self, girdi: dict[str, Any], **kwargs: Any) -> EngineResult:
        """Graf işlemleri: ``ekle`` | ``uzaklik`` | ``komsu`` | ``yayilma``."""
        islem = girdi.get("islem", "komsu")
        if islem == "ekle":
            kenar = self.kenar_ekle(
                girdi["kaynak"], girdi["hedef"], girdi.get("tur", "ilgili"),
                float(girdi.get("agirlik", 1.0)),
            )
            return EngineResult(data=kenar, explanation="İlişki eklendi.")
        if islem == "uzaklik":
            d = self.anlam_uzakligi(girdi["kaynak"], girdi["hedef"])
            return EngineResult(data=d, explanation="Anlam uzaklığı hesaplandı.")
        if islem == "yayilma":
            d = self.yayilma(girdi["ad"], int(girdi.get("derinlik", 2)))
            return EngineResult(data=sorted(d), explanation="Yayılım tamamlandı.")
        komsular = self.komsular(girdi["ad"], girdi.get("tur"))
        return EngineResult(data=komsular, explanation=f"{len(komsular)} komşu bulundu.")


def _olay(ad: str, kaynak: str, hedef: str, tur: str):
    from asena.core.event_bus import Event

    return Event(name=ad, payload={"kaynak": kaynak, "hedef": hedef, "tur": tur},
                 source="knowledge_graph")
