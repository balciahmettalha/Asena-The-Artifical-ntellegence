"""Motor taban sınıfı ve ortak veri yapıları.

Her motor tek bir sorumluluğa sahiptir (SRP) ve bu dosyadaki arayüz
üzerinden bağımsız olarak test edilebilir.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from asena.core.consent import ConsentManager
    from asena.core.di_container import DIContainer
    from asena.core.event_bus import EventBus


@dataclass
class EngineContext:
    """Motorlara enjekte edilen ortak çalışma bağlamı."""

    container: "DIContainer"
    bus: "EventBus"
    consent: "ConsentManager"
    config: dict[str, Any] = field(default_factory=dict)


@dataclass
class EngineResult:
    """Bir motor işleminin standart çıktısı.

    Attributes:
        ok: İşlemin başarılı olup olmadığı.
        data: Motora özgü sonuç verisi.
        confidence: 0.0–1.0 arası güven puanı.
        explanation: Sonucun Türkçe gerekçesi (çıkarım izlenebilirliği için).
        errors: Kurtarılabilir hata/uyarı iletileri.
        metadata: Ek tanı bilgileri.
    """

    ok: bool = True
    data: Any = None
    confidence: float = 1.0
    explanation: str = ""
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def hata(cls, mesaj: str) -> "EngineResult":
        """Başarısız sonuç üretir."""
        return cls(ok=False, confidence=0.0, errors=[mesaj], explanation=mesaj)


class BaseEngine(ABC):
    """Tüm bilişsel motorların uyguladığı temel arayüz."""

    #: Motorun benzersiz adı (DI ve olay kaydı için).
    name: str = "base"
    #: Motor grubu: syntax, knowledge, memory, logic, reason, decision,
    #: planning, learning, governance, module.
    group: str = "genel"
    #: Çalışmadan önce hazır olması gereken motor adları.
    dependencies: tuple[str, ...] = ()

    def __init__(self) -> None:
        self._ctx: EngineContext | None = None

    # ----------------------------------------------------------- yaşam döngüsü
    def bind(self, ctx: EngineContext) -> None:
        """Bağlamı enjekte eder (EngineRegistry tarafından çağrılır)."""
        self._ctx = ctx
        self.on_bind(ctx)

    def on_bind(self, ctx: EngineContext) -> None:  # noqa: B027 — bilinçli boş
        """Alt sınıflar için bağlanma sonrası hazırlık kancası."""

    def shutdown(self) -> None:  # noqa: B027 — bilinçli boş
        """Kapanış kancası: kaynakları serbest bırakır."""

    @property
    def ctx(self) -> EngineContext:
        if self._ctx is None:
            raise RuntimeError(f"Motor '{self.name}' henüz bağlanmadı (bind).")
        return self._ctx

    # ------------------------------------------------------------------ işlem
    @abstractmethod
    def process(self, girdi: Any, **kwargs: Any) -> EngineResult:
        """Motorun tek sorumluluğunu yerine getirir."""

    def health_check(self) -> bool:
        """Motorun çalışır durumda olup olmadığını bildirir."""
        return self._ctx is not None

    def __repr__(self) -> str:  # pragma: no cover — tanı amaçlı
        return f"<{type(self).__name__} name={self.name!r} group={self.group!r}>"
