"""Motor kayıt ve yaşam döngüsü yöneticisi.

Bağımlılık sırasını topolojik olarak çözer; böylece bir motor ancak
ihtiyaç duyduğu motorlar bağlandıktan sonra başlatılır. Factory deseni
ile motor örnekleri üretilir.
"""

from __future__ import annotations

from asena.core.exceptions import EngineError
from asena.engine.base import BaseEngine, EngineContext


class EngineRegistry:
    """Motorları kaydeder, sıralar ve bağlar."""

    def __init__(self) -> None:
        self._motorlar: dict[str, BaseEngine] = {}
        self._bagli: list[str] = []

    def register(self, motor: BaseEngine) -> BaseEngine:
        """Motoru kaydeder; zincirleme kullanım için motoru döndürür."""
        if motor.name in self._motorlar:
            raise EngineError(f"Motor zaten kayıtlı: '{motor.name}'")
        self._motorlar[motor.name] = motor
        return motor

    def get(self, name: str) -> BaseEngine:
        try:
            return self._motorlar[name]
        except KeyError as exc:
            raise EngineError(f"Motor bulunamadı: '{name}'") from exc

    def by_group(self, group: str) -> list[BaseEngine]:
        return [m for m in self._motorlar.values() if m.group == group]

    def _siralama(self) -> list[BaseEngine]:
        """Bağımlılıklara göre topolojik sıralama üretir."""
        sirali: list[BaseEngine] = []
        gecici: set[str] = set()
        kalici: set[str] = set()

        def ziyaret(motor: BaseEngine) -> None:
            if motor.name in kalici:
                return
            if motor.name in gecici:
                raise EngineError(f"Döngüsel motor bağımlılığı: '{motor.name}'")
            gecici.add(motor.name)
            for bagimlilik in motor.dependencies:
                if bagimlilik in self._motorlar:
                    ziyaret(self._motorlar[bagimlilik])
            gecici.discard(motor.name)
            kalici.add(motor.name)
            sirali.append(motor)

        for motor in self._motorlar.values():
            ziyaret(motor)
        return sirali

    def initialize_all(self, ctx: EngineContext) -> None:
        """Tüm motorları bağımlılık sırasıyla bağlar."""
        for motor in self._siralama():
            if motor.name not in self._bagli:
                motor.bind(ctx)
                self._bagli.append(motor.name)

    def shutdown_all(self) -> None:
        """Bağlanmış motorları ters sırada kapatır."""
        for name in reversed(self._bagli):
            self._motorlar[name].shutdown()
        self._bagli.clear()

    def names(self) -> list[str]:
        return sorted(self._motorlar)

    def __len__(self) -> int:
        return len(self._motorlar)
