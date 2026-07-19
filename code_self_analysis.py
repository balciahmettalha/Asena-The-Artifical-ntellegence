"""Repository katmanı: veri erişiminin soyutlanması.

Bellek ve bilgi motorları SQL bilmez; tüm kalıcı erişim bu sınıflar
üzerinden geçer (Repository deseni).
"""

from __future__ import annotations

from typing import Any

from asena.database.connection import Database


class WordRepository:
    """Kelime belleği: yazım, kök, tür, anlam ve koordinat bilgisi."""

    def __init__(self, db: Database) -> None:
        self._db = db

    def bul(self, yazim: str) -> dict[str, Any] | None:
        satir = self._db.fetchone("SELECT * FROM kelimeler WHERE yazim=?", (yazim,))
        return dict(satir) if satir else None

    def ekle(self, yazim: str, kok: str | None = None, tur: str | None = None,
             anlam: str | None = None, onem: float = 1.0,
             koordinat: tuple[float, float, float] = (0.0, 0.0, 0.0)) -> int:
        imlec = self._db.execute(
            "INSERT INTO kelimeler(yazim, kok, tur, anlam, onem, anlam_x, anlam_y, anlam_z) "
            "VALUES(?,?,?,?,?,?,?,?) "
            "ON CONFLICT(yazim) DO UPDATE SET son_erisim=datetime('now'), "
            "erisim_sayisi=erisim_sayisi+1",
            (yazim, kok, tur, anlam, onem, *koordinat),
        )
        return int(imlec.lastrowid or 0)

    def erisim_kaydet(self, yazim: str) -> None:
        self._db.execute(
            "UPDATE kelimeler SET erisim_sayisi=erisim_sayisi+1, "
            "son_erisim=datetime('now') WHERE yazim=?",
            (yazim,),
        )

    def onem_guncelle(self, yazim: str, onem: float) -> None:
        self._db.execute("UPDATE kelimeler SET onem=? WHERE yazim=?", (onem, yazim))

    def tumu(self, limit: int = 10000) -> list[dict[str, Any]]:
        return [dict(s) for s in self._db.fetchall("SELECT * FROM kelimeler LIMIT ?", (limit,))]


class KnowledgeRepository:
    """Bilgi önermeleri ve sürüm geçmişi."""

    def __init__(self, db: Database) -> None:
        self._db = db

    def son_kimlik(self) -> str | None:
        satir = self._db.fetchone(
            "SELECT id FROM bilgiler ORDER BY rowid DESC LIMIT 1"
        )
        return str(satir["id"]) if satir else None

    def ekle(self, kimlik: str, ozne: str, yuklem: str, nesne: str | None,
             onerme: str, guven: float = 1.0, onem: float = 1.0,
             kaynak: str = "kullanici", gecerlilik: str | None = None) -> None:
        self._db.execute(
            "INSERT INTO bilgiler(id, ozne, yuklem, nesne, onerme, guven, onem, kaynak, gecerlilik) "
            "VALUES(?,?,?,?,?,?,?,?,?)",
            (kimlik, ozne, yuklem, nesne, onerme, guven, onem, kaynak, gecerlilik),
        )

    def bul(self, kimlik: str) -> dict[str, Any] | None:
        satir = self._db.fetchone("SELECT * FROM bilgiler WHERE id=?", (kimlik,))
        return dict(satir) if satir else None

    def ozne_ile(self, ozne: str, limit: int = 100) -> list[dict[str, Any]]:
        return [
            dict(s)
            for s in self._db.fetchall(
                "SELECT * FROM bilgiler WHERE ozne=? AND durum='aktif' LIMIT ?",
                (ozne, limit),
            )
        ]

    def ara(self, metin: str, limit: int = 50) -> list[dict[str, Any]]:
        return [
            dict(s)
            for s in self._db.fetchall(
                "SELECT * FROM bilgiler WHERE durum='aktif' AND "
                "(onerme LIKE ? OR ozne LIKE ? OR nesne LIKE ?) LIMIT ?",
                (f"%{metin}%", f"%{metin}%", f"%{metin}%", limit),
            )
        ]

    def arsivle(self, kimlik: str) -> None:
        self._db.execute(
            "UPDATE bilgiler SET durum='arsiv', guncelleme=datetime('now') WHERE id=?",
            (kimlik,),
        )

    def surum_artir(self, kimlik: str) -> None:
        self._db.execute(
            "UPDATE bilgiler SET surum=surum+1, guncelleme=datetime('now') WHERE id=?",
            (kimlik,),
        )

    def execute_guncelle(self, kimlik: str, yeni_onerme: str, yeni_guven: float) -> None:
        """Bilginin önermesini ve güvenini günceller."""
        self._db.execute(
            "UPDATE bilgiler SET onerme=?, guven=?, guncelleme=datetime('now') WHERE id=?",
            (yeni_onerme, yeni_guven, kimlik),
        )

    def gecerlilik_guncelle(self, kimlik: str, gecerlilik: str) -> None:
        """Bilgiye geçerlilik dönemi atar."""
        self._db.execute(
            "UPDATE bilgiler SET gecerlilik=?, guncelleme=datetime('now') WHERE id=?",
            (gecerlilik, kimlik),
        )

    def surum_kaydet(self, kimlik: str, surum_no: int, icerik: str, neden: str) -> None:
        self._db.execute(
            "INSERT OR IGNORE INTO bilgi_surumleri(bilgi_id, surum_no, icerik, degisim_nedeni) "
            "VALUES(?,?,?,?)",
            (kimlik, surum_no, icerik, neden),
        )

    def surumler(self, kimlik: str) -> list[dict[str, Any]]:
        return [
            dict(s)
            for s in self._db.fetchall(
                "SELECT * FROM bilgi_surumleri WHERE bilgi_id=? ORDER BY surum_no",
                (kimlik,),
            )
        ]

    def tumu(self, limit: int = 100000) -> list[dict[str, Any]]:
        return [
            dict(s)
            for s in self._db.fetchall(
                "SELECT * FROM bilgiler WHERE durum='aktif' LIMIT ?", (limit,)
            )
        ]

    def say(self) -> int:
        satir = self._db.fetchone("SELECT COUNT(*) AS n FROM bilgiler WHERE durum='aktif'")
        return int(satir["n"]) if satir else 0


class RuleRepository:
    """Çıkarım kuralları (koşul → sonuç)."""

    def __init__(self, db: Database) -> None:
        self._db = db

    def ekle(self, kosul: str, sonuc: str, guven: float = 1.0) -> int:
        imlec = self._db.execute(
            "INSERT INTO kurallar(kosul, sonuc, guven) VALUES(?,?,?)",
            (kosul, sonuc, guven),
        )
        return int(imlec.lastrowid or 0)

    def tumu(self) -> list[dict[str, Any]]:
        return [dict(s) for s in self._db.fetchall("SELECT * FROM kurallar")]


class ConversationRepository:
    """Konuşma ve mesaj kaydı."""

    def __init__(self, db: Database) -> None:
        self._db = db

    def konusma_ac(self, mod: str = "sohbet") -> int:
        imlec = self._db.execute("INSERT INTO konusmalar(mod) VALUES(?)", (mod,))
        return int(imlec.lastrowid or 0)

    def konusma_kapat(self, konusma_id: int) -> None:
        self._db.execute(
            "UPDATE konusmalar SET bitis=datetime('now') WHERE id=?", (konusma_id,)
        )

    def mesaj_ekle(self, konusma_id: int, rol: str, icerik: str) -> int:
        imlec = self._db.execute(
            "INSERT INTO mesajlar(konusma_id, rol, icerik) VALUES(?,?,?)",
            (konusma_id, rol, icerik),
        )
        return int(imlec.lastrowid or 0)

    def son_mesajlar(self, konusma_id: int, limit: int = 20) -> list[dict[str, Any]]:
        satirlar = self._db.fetchall(
            "SELECT * FROM mesajlar WHERE konusma_id=? ORDER BY id DESC LIMIT ?",
            (konusma_id, limit),
        )
        return [dict(s) for s in reversed(satirlar)]


class RelationRepository:
    """Bilgi grafiği kenarlarının kalıcı karşılığı."""

    def __init__(self, db: Database) -> None:
        self._db = db

    def iliski_ekle(self, kaynak: str, hedef: str, tur: str,
                    agirlik: float = 1.0) -> None:
        self._db.execute(
            "INSERT INTO iliskiler(kaynak, hedef, tur, agirlik) VALUES(?,?,?,?) "
            "ON CONFLICT(kaynak, hedef, tur) DO UPDATE SET agirlik=excluded.agirlik",
            (kaynak, hedef, tur, agirlik),
        )

    def tum_iliskiler(self, limit: int = 100000) -> list[tuple[str, str, str, float]]:
        return [
            (str(s["kaynak"]), str(s["hedef"]), str(s["tur"]), float(s["agirlik"]))
            for s in self._db.fetchall("SELECT * FROM iliskiler LIMIT ?", (limit,))
        ]

    def komsular(self, ad: str) -> list[dict[str, Any]]:
        return [
            dict(s)
            for s in self._db.fetchall(
                "SELECT * FROM iliskiler WHERE kaynak=? OR hedef=?", (ad, ad)
            )
        ]


class JournalRepository:
    """Günlük öğrenme raporu kayıtları."""

    def __init__(self, db: Database) -> None:
        self._db = db

    def gunluk_artir(self, tarih: str, alan: str, miktar: int = 1,
                     notlar: str | None = None) -> None:
        if alan not in {"yeni_kelime", "yeni_iliski", "yeni_kural", "yeni_kavram"}:
            raise ValueError(f"Geçersiz günlük alanı: {alan}")
        self._db.execute(
            f"INSERT INTO ogrenme_gunlugu(tarih, {alan}, notlar) VALUES(?,?,?) "
            f"ON CONFLICT(tarih) DO UPDATE SET {alan}={alan}+excluded.{alan}, "
            f"notlar=COALESCE(excluded.notlar, notlar)",
            (tarih, miktar, notlar),
        )

    def gunluk(self, tarih: str) -> dict[str, Any] | None:
        satir = self._db.fetchone(
            "SELECT * FROM ogrenme_gunlugu WHERE tarih=?", (tarih,)
        )
        return dict(satir) if satir else None

    def son_gunler(self, limit: int = 30) -> list[dict[str, Any]]:
        return [
            dict(s)
            for s in self._db.fetchall(
                "SELECT * FROM ogrenme_gunlugu ORDER BY tarih DESC LIMIT ?", (limit,)
            )
        ]
