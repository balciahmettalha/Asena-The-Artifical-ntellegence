"""Bilgi Kanıt Motoru (Knowledge Proof Engine).

Her bilginin arkasında bir kanıt zinciri durur:
``bilgi → kanıt → kaynak → deney → sonuç``. Kanıtlar veritabanında
``kanitlar`` tablosunda, veritabanı yoksa bellek içinde tutulur.
"""

from __future__ import annotations

from typing import Any

from asena.engine.base import BaseEngine, EngineResult


class KnowledgeProofEngine(BaseEngine):
    """Bilgi-kanıt zincirlerini yöneten motor."""

    name = "knowledge_proof"
    group = "knowledge"

    def __init__(self, db: Any | None = None) -> None:
        super().__init__()
        self._db = db
        self._bellek: dict[str, list[dict[str, Any]]] = {}

    # ------------------------------------------------------------------ ekle
    def kanit_ekle(self, bilgi_id: str, kanit: str, kaynak: str = "",
                   sira: int | None = None) -> None:
        """Bilgiye kanıt zinciri halkası ekler."""
        if self._db is not None:
            mevcut = self.zincir(bilgi_id)
            self._db.execute(
                "INSERT INTO kanitlar(bilgi_id, kanit_metni, kaynak, zincir_sirasi) "
                "VALUES(?,?,?,?)",
                (bilgi_id, kanit, kaynak, len(mevcut) if sira is None else sira),
            )
        else:
            self._bellek.setdefault(bilgi_id, []).append(
                {"kanit_metni": kanit, "kaynak": kaynak,
                 "zincir_sirasi": len(self._bellek[bilgi_id]) if sira is None else sira}
            )

    # ------------------------------------------------------------------ sorgu
    def zincir(self, bilgi_id: str) -> list[dict[str, Any]]:
        """Bilginin kanıt zincirini sıralı döndürür."""
        if self._db is not None:
            return [
                dict(s)
                for s in self._db.fetchall(
                    "SELECT * FROM kanitlar WHERE bilgi_id=? ORDER BY zincir_sirasi",
                    (bilgi_id,),
                )
            ]
        return sorted(
            self._bellek.get(bilgi_id, []), key=lambda k: k["zincir_sirasi"]
        )

    def kanit_sayisi(self, bilgi_id: str) -> int:
        return len(self.zincir(bilgi_id))

    def zincir_metni(self, bilgi_id: str) -> str:
        """Kanıt zincirini okunabilir biçimde özetler."""
        halkalar = self.zincir(bilgi_id)
        if not halkalar:
            return "Bu bilgi için henüz kanıt kaydı yok."
        adimlar = [
            f"{i + 1}. {h['kanit_metni']}"
            + (f" (kaynak: {h['kaynak']})" if h.get("kaynak") else "")
            for i, h in enumerate(halkalar)
        ]
        return "Kanıt zinciri:\n" + "\n".join(adimlar)

    def process(self, girdi: dict[str, Any], **kwargs: Any) -> EngineResult:
        if girdi.get("islem") == "ekle":
            self.kanit_ekle(
                str(girdi["bilgi_id"]), str(girdi["kanit"]),
                str(girdi.get("kaynak", "")),
            )
            return EngineResult(data=girdi["bilgi_id"], explanation="Kanıt eklendi.")
        metin = self.zincir_metni(str(girdi.get("bilgi_id", "")))
        return EngineResult(data=metin, explanation=metin)
