"""Bilişsel motorların çekirdek iskeleti.

Tüm motorlar :class:`BaseEngine` arayüzünü uygular; kayıt ve yaşam döngüsü
:class:`EngineRegistry` üzerinden yürür.
"""

from asena.engine.base import BaseEngine, EngineContext, EngineResult
from asena.engine.registry import EngineRegistry

__all__ = ["BaseEngine", "EngineContext", "EngineRegistry", "EngineResult"]
