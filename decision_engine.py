"""ASENA genelinde kullanılan özel hata türleri.

Tek bir kök hata (AsenaError) üzerinden türetilir; böylece üst katmanlar
sistemin kendi hatalarını harici hatalardan güvenle ayırt edebilir.
"""

from __future__ import annotations


class AsenaError(Exception):
    """ASENA bileşenlerinin fırlattığı tüm hataların kök sınıfı."""


class ConfigurationError(AsenaError):
    """Yapılandırma dosyası eksik, bozuk veya geçersiz olduğunda."""


class EngineError(AsenaError):
    """Bir motorun çalışması sırasında oluşan kurtarılabilir hata."""


class ConsentRequiredError(AsenaError):
    """Kullanıcı onayı gerektiren bir eylem izinsiz denendiğinde.

    ASENA'nın güven ilkesinin kod karşılığıdır: internet erişimi, dosya
    yazımı, kod çalıştırma ve sistem çağrısı gibi harici eylemler açık
    onay olmadan asla başlatılmaz.
    """


class KnowledgeContradictionError(AsenaError):
    """Bilgi tabanında çözümlenemeyen bir çelişki saptandığında."""


class ResolutionError(AsenaError):
    """DI konteynerinde istenen bağımlılık bulunamadığında."""
