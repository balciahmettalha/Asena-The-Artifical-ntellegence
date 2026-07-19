"""İç Simülasyon (Internal Simulation).

Cevabı vermeden önce zihninde simüle eder: "kod çalışır mı? → dene →
hata varsa düzelt → gönder". Kod için sözdizimi denetimi (ast), matematik
için ters işlemle doğrulama yapılır. Kullanıcı onayı olmadan hiçbir kod
gerçekten çalıştırılmaz; yalnızca statik analiz uygulanır.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import Any

from asena.engine.base import BaseEngine, EngineResult


@dataclass
class SimulasyonSonucu:
    gecti_mi: bool
    bulgular: list[str] = field(default_factory=list)
    duzeltilmis: str | None = None


class InternalSimulation(BaseEngine):
    """Çıktıları göndermeden önce içeride deneyen motor."""

    name = "internal_simulation"
    group = "planning"

    def kod_simule_et(self, kod: str) -> SimulasyonSonucu:
        """Kodu çalıştırmadan sözdizimi ve yapı açısından denetler."""
        bulgular: list[str] = []
        try:
            agac = ast.parse(kod)
        except SyntaxError as exc:
            return SimulasyonSonucu(
                gecti_mi=False,
                bulgular=[f"Sözdizimi hatası (satır {exc.lineno}): {exc.msg}"],
            )
        if not agac.body:
            bulgular.append("Kod boş; çalıştırılacak ifade yok.")
        for dugum in ast.walk(agac):
            if isinstance(dugum, (ast.Import, ast.ImportFrom)):
                bulgular.append(
                    "İçe aktarma var: çalıştırmadan önce güvenlik onayı gerekir."
                )
        return SimulasyonSonucu(
            gecti_mi=True,
            bulgular=bulgular or ["Sözdizimi geçerli; simülasyon başarılı."],
        )

    def matematik_dogrula(self, islem: str, beklenen: float,
                          hesaplayici: Any) -> SimulasyonSonucu:
        """Matematik sonucunu bağımsız hesapla doğrular."""
        try:
            sonuc = float(hesaplayici(islem))
        except Exception as exc:  # noqa: BLE001
            return SimulasyonSonucu(gecti_mi=False,
                                    bulgular=[f"Hesaplama hatası: {exc}"])
        if abs(sonuc - beklenen) < 1e-9:
            return SimulasyonSonucu(gecti_mi=True,
                                    bulgular=["Sonuç doğrulandı."])
        return SimulasyonSonucu(
            gecti_mi=False,
            bulgular=[f"Uyumsuzluk: hesaplanan {sonuc}, beklenen {beklenen}"],
            duzeltilmis=str(sonuc),
        )

    def process(self, girdi: dict[str, Any], **kwargs: Any) -> EngineResult:
        if "kod" in girdi:
            sonuc = self.kod_simule_et(str(girdi["kod"]))
        else:
            return EngineResult.hata("Simüle edilecek içerik bulunamadı.")
        return EngineResult(
            ok=sonuc.gecti_mi, data=sonuc,
            explanation="; ".join(sonuc.bulgular),
        )
