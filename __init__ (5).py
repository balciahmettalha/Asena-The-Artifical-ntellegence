"""Bağımlılık enjeksiyonu konteyneri (Dependency Injection).

Motorlar birbirine doğrudan erişmez; ihtiyaç duydukları işbirlikçileri
konteyner üzerinden, açık arayüz adlarıyla çözer. Bu, bağımlılıkların
tersine çevrilmesi (DIP) ilkesinin uygulanmasıdır.
"""

from __future__ import annotations

import threading
from typing import Any, Callable

from asena.core.exceptions import ResolutionError

Factory = Callable[["DIContainer"], Any]


class DIContainer:
    """Tekil (singleton) ve fabrika kayıtlarını yöneten basit konteyner."""

    def __init__(self) -> None:
        self._instances: dict[str, Any] = {}
        self._factories: dict[str, Factory] = {}
        self._singletons: dict[str, Any] = {}
        self._lock = threading.RLock()

    def register_instance(self, name: str, instance: Any) -> None:
        """Hazır bir örneği isimle kaydeder."""
        with self._lock:
            self._instances[name] = instance

    def register_factory(self, name: str, factory: Factory, *, singleton: bool = True) -> None:
        """Tembel üretim için fabrika kaydeder.

        ``singleton=True`` ise ilk çözümlemede üretilen örnek saklanır.
        """
        with self._lock:
            self._factories[name] = factory
            if not singleton:
                self._singletons.pop(name, None)

    def has(self, name: str) -> bool:
        with self._lock:
            return name in self._instances or name in self._factories

    def resolve(self, name: str) -> Any:
        """İsimle kayıtlı bağımlılığı çözer; yoksa ResolutionError fırlatır."""
        with self._lock:
            if name in self._instances:
                return self._instances[name]
            if name in self._singletons:
                return self._singletons[name]
            if name in self._factories:
                ornek = self._factories[name](self)
                self._singletons[name] = ornek
                return ornek
        raise ResolutionError(f"Bağımlılık bulunamadı: '{name}'")

    def names(self) -> list[str]:
        """Kayıtlı tüm bağımlılık adlarını döndürür."""
        with self._lock:
            return sorted(set(self._instances) | set(self._factories))

    def clear(self) -> None:
        """Tüm kayıtları temizler (testler için)."""
        with self._lock:
            self._instances.clear()
            self._factories.clear()
            self._singletons.clear()
