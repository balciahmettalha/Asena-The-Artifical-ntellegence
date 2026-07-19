"""Yürütücü Denetim (Executive Control).

Prefrontal korteks benzeri: tüm sistemi yönetir; hangi motorun ne zaman
devreye gireceğine karar verir. Niyet → motor eşleşmesi tabanlıdır;
bilinmeyen niyetlerde varsayılan hattı kullanır.
"""

from __future__ import annotations

from typing import Any

from asena.engine.base import BaseEngine, EngineResult

# Niyet başına motor hattı (sıralı)
NIYET_HATTI: dict[str, list[str]] = {
    "selamlasma": ["sentiment_analysis"],
    "hesaplama": ["math_expert"],
    "tanim_sorusu": ["semantic_network", "concept_engine", "multiple_hypotheses"],
    "neden_sorusu": ["causal_chain", "cause_effect", "reason_engine"],
    "soru": ["reason_engine", "multiple_hypotheses", "decision_engine"],
    "emir": ["goal_engine", "planner"],
    "bildirim": ["contradiction_engine", "learning_engine"],
}


class ExecutiveControl(BaseEngine):
    """Motor devreye alma kararlarını veren yürütücü motor."""

    name = "executive_control"
    group = "governance"

    def hat_belirle(self, niyet: str) -> list[str]:
        """Niyete göre devreye alınacak motor hattını döndürür."""
        return list(NIYET_HATTI.get(niyet, ["reason_engine"]))

    def devreye_al(self, motor_adi: str, girdi: Any) -> EngineResult:
        """Belirtilen motoru kayıt defterinden bulup çalıştırır."""
        kayit = self.ctx.container.resolve("engine_registry")
        motor = kayit.get(motor_adi)
        if not motor.health_check():
            return EngineResult.hata(f"Motor hazır değil: {motor_adi}")
        return motor.process(girdi)

    def hatt_calistir(self, niyet: str, girdi: Any) -> dict[str, EngineResult]:
        """Niyet hattındaki tüm motorları sırayla çalıştırır."""
        sonuclar: dict[str, EngineResult] = {}
        for motor_adi in self.hat_belirle(niyet):
            try:
                sonuclar[motor_adi] = self.devreye_al(motor_adi, girdi)
            except Exception as exc:  # noqa: BLE001 — hat devam eder
                sonuclar[motor_adi] = EngineResult.hata(
                    f"{motor_adi} çalıştırılamadı: {exc}"
                )
        return sonuclar

    def process(self, girdi: dict[str, Any], **kwargs: Any) -> EngineResult:
        niyet = str(girdi.get("niyet", "soru"))
        hat = self.hat_belirle(niyet)
        return EngineResult(
            data=hat, explanation=f"'{niyet}' için hat: {' → '.join(hat)}"
        )
