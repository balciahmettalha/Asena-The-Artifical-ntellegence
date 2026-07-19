"""Merkezi olay veri yolu (Event Bus).

Modüller arası asenkron iletişimin tek kanalıdır. Kritik yollar senkron
çağrılarla (DI üzerinden) çalışır; öğrenme, indeksleme ve günlükleme gibi
uzun süren işler olay olarak yayınlanır ve ana döngüyü bloklamaz.

Tasarım deseni: Observer. "*" aboneliği tüm olayları dinler.
"""

from __future__ import annotations

import asyncio
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, DefaultDict

Handler = Callable[["Event"], Any]


@dataclass(frozen=True)
class Event:
    """Yayınlanan tek bir olay.

    Attributes:
        name: Nokta ile ayrılmış olay adı, örn. ``"bilgi.eklendi"``.
        payload: Olaya ait serbest biçimli veri.
        timestamp: Unix zaman damgası (saniye).
        source: Olayı üreten modül adı.
    """

    name: str
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    source: str = ""


class EventBus:
    """İş parçacığı güvenli, senkron + asenkron olay dağıtıcısı."""

    def __init__(self) -> None:
        self._handlers: DefaultDict[str, list[Handler]] = defaultdict(list)
        self._lock = threading.RLock()
        self._async_queue: asyncio.Queue[Event] | None = None
        self._history: list[Event] = []
        self._history_limit = 1000

    # ------------------------------------------------------------------ abone
    def subscribe(self, event_name: str, handler: Handler) -> None:
        """Bir olay adına (veya "*" jokerine) işleyici kaydeder."""
        with self._lock:
            if handler not in self._handlers[event_name]:
                self._handlers[event_name].append(handler)

    def unsubscribe(self, event_name: str, handler: Handler) -> None:
        """İşleyiciyi kaldırır; yoksa sessizce geçer."""
        with self._lock:
            if handler in self._handlers.get(event_name, []):
                self._handlers[event_name].remove(handler)

    # ------------------------------------------------------------------ yayın
    def publish(self, event: Event) -> None:
        """Olayı senkron olarak ilgili tüm işleyicilere dağıtır.

        Bir işleyicinin hatası diğerlerini etkilemez; hata ``hata.isleyici``
        olayı olarak yeniden yayınlanır.
        """
        with self._lock:
            self._history.append(event)
            if len(self._history) > self._history_limit:
                self._history = self._history[-self._history_limit :]
            handlers = list(self._handlers.get(event.name, ())) + list(
                self._handlers.get("*", ())
            )
        for handler in handlers:
            try:
                handler(event)
            except Exception as exc:  # noqa: BLE001 — bus asla çökmemeli
                if event.name != "hata.isleyici":
                    self.publish(
                        Event(
                            name="hata.isleyici",
                            payload={"hata": repr(exc), "olay": event.name},
                            source="event_bus",
                        )
                    )

    async def publish_async(self, event: Event) -> None:
        """Olayı asenkron kuyruğa bırakır; ana döngü bloklanmaz."""
        if self._async_queue is None:
            self._async_queue = asyncio.Queue()
        await self._async_queue.put(event)

    async def drain_async(self) -> int:
        """Kuyruktaki tüm olayları işler; işlenen sayısını döndürür."""
        if self._async_queue is None:
            return 0
        islenen = 0
        while not self._async_queue.empty():
            event = await self._async_queue.get()
            self.publish(event)
            islenen += 1
        return islenen

    # ------------------------------------------------------------------ sorgu
    def history(self, event_name: str | None = None, limit: int = 50) -> list[Event]:
        """Geçmiş olayları döndürür (metakognisyon ve günlükleme için)."""
        with self._lock:
            if event_name is None:
                kayitlar = self._history
            else:
                kayitlar = [e for e in self._history if e.name == event_name]
            return list(kayitlar[-limit:])
