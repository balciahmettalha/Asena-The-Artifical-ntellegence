"""Öngörülü düşünme (Predictive Thinking).

Kullanıcı yazmaya başladığı anda — henüz enter'a basılmadan — sistemin
düşünmeye başlamasını sağlar. Kısmi girdi arka planda sözdizimsel olarak
ön-işlenir; enter'a basıldığında bilişsel döngü hazır ara sonuçlarla çok
daha hızlı ilerler.

CLI gibi karakter karakter girdi alamayan ortamlarda ``on_partial`` kancası
dışarıdan beslenir; mekanizma arayüzden bağımsızdır.
"""

from __future__ import annotations

import threading
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any, Callable


class PredictiveEngine:
    """Kısmi girdiyi arka planda ön-işleyen motor."""

    def __init__(self, on_isle: Callable[[str], Any], havuz_boyutu: int = 2) -> None:
        """
        Args:
            on_isle: Kısmi metne uygulanacak hafif ön-işlem (örn. tokenize +
                kök analizi). Ağır çıkarım burada yapılmaz.
            havuz_boyutu: Arka plan iş parçacığı sayısı.
        """
        self._on_isle = on_isle
        self._havuz = ThreadPoolExecutor(
            max_workers=havuz_boyutu, thread_name_prefix="asena-predictive"
        )
        self._kilit = threading.RLock()
        self._son_metin = ""
        self._son_sonuc: Future[Any] | None = None

    def on_partial(self, kismi_metin: str) -> None:
        """Kullanıcının yazmakta olduğu kısmi metni kuyruğa alır.

        Yalnızca en güncel kısmi metin işlenir; eski ön-işlem sonuçları
        geçersiz sayılır.
        """
        with self._kilit:
            self._son_metin = kismi_metin
            self._son_sonuc = self._havuz.submit(self._on_isle, kismi_metin)

    def hazir_sonuc(self, tam_metin: str, zaman_asimi: float = 0.05) -> Any | None:
        """Tam metin için hazır ön-işlem sonucunu döndürür.

        Arka plandaki ön-işlem tam metnin bir öneki ise ve süresinde
        bittiyse sonucu verir; aksi hâlde ``None`` döner ve çağıran işlemi
        kendisi yapar. Asla uzun süre beklemez.
        """
        with self._kilit:
            gelecek = self._son_sonuc
            kismi = self._son_metin
        if gelecek is None or not tam_metin.startswith(kismi) or not kismi:
            return None
        try:
            return gelecek.result(timeout=zaman_asimi)
        except Exception:  # noqa: BLE001 — ön-işlem opsiyoneldir
            return None

    def kapat(self) -> None:
        self._havuz.shutdown(wait=False, cancel_futures=True)
