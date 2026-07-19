"""Şema migration altyapısı.

Migration'lar sıralı adımlar hâlinde tanımlanır; ``meta`` tablosundaki
``sema_surumu`` anahtarı hangi adımların uygulandığını izler. Yeni sürümler
listeye eklenir — geriye dönük uyumluluk korunur.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from asena.database.connection import Database

_SEMA_DOSYASI = Path(__file__).with_name("schema.sql")


def _v1_temel_sema(db: Database) -> None:
    db.executescript(_SEMA_DOSYASI.read_text(encoding="utf-8"))


# (sürüm_no, açıklama, uygulayıcı) — yenileri sona eklenir.
MIGRATIONS: list[tuple[int, str, Callable[[Database], None]]] = [
    (1, "temel şema", _v1_temel_sema),
]


class MigrationRunner:
    """Bekleyen migration'ları sırayla uygular."""

    def __init__(self, db: Database) -> None:
        self._db = db

    def mevcut_surum(self) -> int:
        tablo = self._db.fetchone(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='meta'"
        )
        if tablo is None:
            return 0
        satir = self._db.fetchone(
            "SELECT deger FROM meta WHERE anahtar='sema_surumu'"
        )
        return int(satir["deger"]) if satir else 0

    def bekleyenler(self) -> list[tuple[int, str, Callable[[Database], None]]]:
        surum = self.mevcut_surum()
        return [m for m in MIGRATIONS if m[0] > surum]

    def uygula(self) -> int:
        """Bekleyen tüm migration'ları uygular; yeni sürümü döndürür."""
        surum = self.mevcut_surum()
        for no, _aciklama, uygulayici in self.bekleyenler():
            with self._db.transaction():
                uygulayici(self._db)
                self._db.execute(
                    "INSERT INTO meta(anahtar, deger) VALUES('sema_surumu', ?) "
                    "ON CONFLICT(anahtar) DO UPDATE SET deger=excluded.deger",
                    (str(no),),
                )
            surum = no
        return surum
