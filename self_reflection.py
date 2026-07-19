"""SQLite bağlantı yöneticisi.

İş parçacığı güvenli erişim sağlar; WAL kipi ile okuma/yazma eşzamanlılığı
artırılır. Bellek katmanı bu sınıfı repository'ler üzerinden kullanır;
doğrudan SQL yazmak yalnızca bu paket içinde yapılır (Repository deseni).
"""

from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable, Iterator


class Database:
    """SQLite veritabanı bağlantısı ve yardımcı sorgu metotları."""

    def __init__(self, yol: str | Path = ":memory:") -> None:
        self._yol = str(yol)
        if self._yol != ":memory:":
            Path(self._yol).parent.mkdir(parents=True, exist_ok=True)
        self._kilit = threading.RLock()
        self._baglanti = sqlite3.connect(
            self._yol, check_same_thread=False, isolation_level=None
        )
        self._baglanti.row_factory = sqlite3.Row
        with self._kilit:
            if self._yol != ":memory:":
                self._baglanti.execute("PRAGMA journal_mode=WAL")
            self._baglanti.execute("PRAGMA foreign_keys=ON")
            self._baglanti.execute("PRAGMA synchronous=NORMAL")

    @property
    def yol(self) -> str:
        return self._yol

    # ------------------------------------------------------------------ sorgu
    def execute(self, sql: str, params: Iterable[Any] = ()) -> sqlite3.Cursor:
        """Tek ifade çalıştırır (autocommit)."""
        with self._kilit:
            return self._baglanti.execute(sql, tuple(params))

    def executemany(self, sql: str, params: Iterable[Iterable[Any]]) -> None:
        with self._kilit:
            self._baglanti.executemany(sql, [tuple(p) for p in params])

    def executescript(self, script: str) -> None:
        with self._kilit:
            self._baglanti.executescript(script)

    def fetchone(self, sql: str, params: Iterable[Any] = ()) -> sqlite3.Row | None:
        with self._kilit:
            return self._baglanti.execute(sql, tuple(params)).fetchone()

    def fetchall(self, sql: str, params: Iterable[Any] = ()) -> list[sqlite3.Row]:
        with self._kilit:
            return list(self._baglanti.execute(sql, tuple(params)).fetchall())

    @contextmanager
    def transaction(self) -> Iterator[None]:
        """Açık işlem bağlamı: hata durumunda geri alır.

        ``executescript`` gibi örtük COMMIT yapan çağrılara karşı dayanıklıdır.
        """
        with self._kilit:
            kendi_acti = not self._baglanti.in_transaction
            if kendi_acti:
                self._baglanti.execute("BEGIN")
            try:
                yield
            except Exception:
                if self._baglanti.in_transaction:
                    self._baglanti.execute("ROLLBACK")
                raise
            else:
                if kendi_acti and self._baglanti.in_transaction:
                    self._baglanti.execute("COMMIT")

    def kapat(self) -> None:
        with self._kilit:
            self._baglanti.close()

    def __enter__(self) -> "Database":
        return self

    def __exit__(self, *_: Any) -> None:
        self.kapat()
