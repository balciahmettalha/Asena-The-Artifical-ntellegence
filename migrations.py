"""Bilişsel Çekirdek (Cognitive Core).

Tüm motorları, bellek katmanlarını ve olay veri yolunu tek yürütücü
çatı altında birleştirir. Uygulamanın tek giriş noktasıdır::

    cekirdek = CognitiveCore()
    yanit = cekirdek.dongu.calis("merhaba")

Bağımlılıklar DI konteynerine, motorlar EngineRegistry'ye kaydedilir;
başlatma sırası bağımlılık grafiğinden çözülür.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from asena.config import Settings, load_settings
from asena.core.consent import ConsentManager
from asena.core.di_container import DIContainer
from asena.core.event_bus import EventBus
from asena.core.predictive import PredictiveEngine
from asena.database import (
    ConversationRepository,
    Database,
    JournalRepository,
    KnowledgeRepository,
    MigrationRunner,
    RelationRepository,
    RuleRepository,
    WordRepository,
)
from asena.engine.base import EngineContext
from asena.engine.registry import EngineRegistry


class CognitiveCore:
    """ASENA'nın yürütücü çekirdeği."""

    def __init__(self, ayarlar: Settings | None = None,
                 veritabani: Database | None = None) -> None:
        self.ayarlar = ayarlar or load_settings()
        self.bus = EventBus()
        self.consent = ConsentManager()
        self.container = DIContainer()
        self.registry = EngineRegistry()

        # Kalıcı bellek
        if veritabani is not None:
            self.db = veritabani
        else:
            yol = str(self.ayarlar.get("veritabani.yol", ":memory:"))
            self.db = Database(yol)
        MigrationRunner(self.db).uygula()

        self._repositoryleri_kur()
        self._motorlari_kur()
        self._baglam_kur()
        self.predictive = self._predictive_kur()

        from asena.core.cognitive_cycle import CognitiveCycle

        self.dongu = CognitiveCycle(self)

    # ------------------------------------------------------------------ kurulum
    def _repositoryleri_kur(self) -> None:
        self.kelimeler = WordRepository(self.db)
        self.bilgiler = KnowledgeRepository(self.db)
        self.iliskiler = RelationRepository(self.db)
        self.kurallar = RuleRepository(self.db)
        self.konusmalar = ConversationRepository(self.db)
        self.gunluk = JournalRepository(self.db)
        for ad, repo in (
            ("word_repo", self.kelimeler), ("knowledge_repo", self.bilgiler),
            ("relation_repo", self.iliskiler), ("rule_repo", self.kurallar),
            ("conversation_repo", self.konusmalar), ("journal_repo", self.gunluk),
        ):
            self.container.register_instance(ad, repo)

    def _motorlari_kur(self) -> None:
        """Tüm motorları örnekler, paylaşılanları bağlar ve kaydeder."""
        from asena.engine.decision import (
            ConfidenceEngine, DecisionEngine, ErrorClassification,
            Metacognition, MultipleHypotheses, SelfEvaluation, SelfReflection,
        )
        from asena.engine.governance import (
            CodeSelfAnalysis, EnergyEngine, ExecutiveControl,
            InternalDiscussion, SelfArchitectureAnalysis, SentimentAnalysis,
        )
        from asena.engine.learning import (
            CuriosityEngine, ExperimentEngine, KnowledgeDensity,
            KnowledgeEconomy, LearningEngine, LearningJournal,
            LearningStrategy, PriorityEngine,
        )
        from asena.engine.planning import (
            GoalEngine, InternalSimulation, Planner, ProjectTracker,
            TimePerception, WorldSimulation,
        )
        from asena.knowledge import (
            AbstractionEngine, AnalogyEngine, ConceptEngine,
            ConceptGeneration, KnowledgeEvolution, KnowledgeFusion,
            KnowledgeGraph, KnowledgeProofEngine, KnowledgeVersioning,
            SemanticNetwork, UniversalIDGenerator, WorldModel,
        )
        from asena.logic import LogicEngine
        from asena.memory import (
            AttentionSystem, ForgettingEngine, KnowledgeCompression,
            LRUCache, MemoryCompression, MemoryEngine, Workspace,
        )
        from asena.modules import CodingExpert, MathExpert, PhysicsExpert
        from asena.plugins import PluginSystem, SelfExtension
        from asena.reason import (
            CausalChain, CauseEffectEngine, ContradictionEngine,
            ContradictionHunter, MultiReasoningEngine, ReasonEngine,
            TreeOfThought,
        )
        from asena.syntax import (
            ContextEngine, InternalLanguage, SyntaxEngine, TurkishLanguageEngine,
        )

        ayar = self.ayarlar
        calisma = Workspace(int(ayar.get("bellek.kisa_sureli_kapasite", 25)))
        cache = LRUCache(int(ayar.get("bellek.cache_boyutu", 1024)))
        graf = KnowledgeGraph(self.iliskiler)
        graf.yukle(self.iliskiler.tum_iliskiler())
        anlam = SemanticNetwork(graf)
        kavram = ConceptEngine(graf)
        dunya = WorldModel()
        kimlik = UniversalIDGenerator.mevcuttan_devam(self.bilgiler.son_kimlik())
        bellek = MemoryEngine(
            workspace=calisma, kelime_repo=self.kelimeler,
            bilgi_repo=self.bilgiler, iliski_repo=self.iliskiler,
            kural_repo=self.kurallar, konusma_repo=self.konusmalar,
            cache=cache, kimlik_ureteci=kimlik,
        )
        sozdizim = SyntaxEngine()
        mantik = LogicEngine()
        proje_dosyasi = Path(str(ayar.get("ogrenme.gunluk_dizini", "veri/gunluk"))) / "projeler.json"

        motorlar = [
            sozdizim,
            TurkishLanguageEngine(sozdizim),
            ContextEngine(),
            InternalLanguage(),
            graf,
            anlam,
            kavram,
            AbstractionEngine(kavram),
            AnalogyEngine(graf),
            ConceptGeneration(graf),
            dunya,
            KnowledgeProofEngine(self.db),
            KnowledgeFusion(),
            KnowledgeVersioning(self.bilgiler),
            KnowledgeEvolution(self.bilgiler),
            bellek,
            AttentionSystem(calisma, int(ayar.get("bellek.dikkat_kapasitesi", 25))),
            ForgettingEngine(calisma, float(ayar.get("bellek.unutma_esigi", 0.05))),
            MemoryCompression(kavram),
            KnowledgeCompression(kavram),
            mantik,
            ReasonEngine(mantik, int(ayar.get("cikarim.en_cok_adim", 8))),
            TreeOfThought(int(ayar.get("cikarim.en_cok_hipotez", 5))),
            MultiReasoningEngine(),
            CauseEffectEngine(dunya),
            CausalChain(dunya),
            ContradictionEngine(anlam.zit_mi),
            ContradictionHunter(anlam.zit_mi),
            DecisionEngine(),
            ConfidenceEngine(),
            MultipleHypotheses(int(ayar.get("cikarim.en_cok_hipotez", 5))),
            SelfEvaluation(),
            Metacognition(),
            SelfReflection(),
            ErrorClassification(),
            GoalEngine(),
            Planner(),
            ProjectTracker(proje_dosyasi),
            InternalSimulation(),
            WorldSimulation(dunya),
            TimePerception(),
            LearningEngine(),
            LearningStrategy(),
            LearningJournal(self.gunluk),
            CuriosityEngine(),
            ExperimentEngine(),
            PriorityEngine(),
            KnowledgeEconomy(float(ayar.get("ogrenme.onem_esigi", 2))),
            KnowledgeDensity(graf),
            ExecutiveControl(),
            EnergyEngine(),
            InternalDiscussion(),
            SelfArchitectureAnalysis(),
            CodeSelfAnalysis(),
            SentimentAnalysis(),
            MathExpert(),
            PhysicsExpert(),
            CodingExpert(),
            PluginSystem(),
            SelfExtension(),
        ]
        for motor in motorlar:
            self.registry.register(motor)
            self.container.register_instance(motor.name, motor)
        self.container.register_instance("engine_registry", self.registry)

    def _baglam_kur(self) -> None:
        baglam = EngineContext(
            container=self.container, bus=self.bus,
            consent=self.consent, config=self.ayarlar.sozluk(),
        )
        self.registry.initialize_all(baglam)

    def _predictive_kur(self) -> PredictiveEngine | None:
        if not self.ayarlar.get("performans.predictive_etkin", True):
            return None
        sozdizim = self.registry.get("syntax_engine")
        return PredictiveEngine(
            lambda metin: sozdizim.metin_cozumle(metin),
            havuz_boyutu=int(self.ayarlar.get("performans.is_parcacigi", 4)),
        )

    # ------------------------------------------------------------------ yaşam
    def motor(self, ad: str) -> Any:
        return self.registry.get(ad)

    def kapat(self) -> None:
        """Motorları kapatır ve veritabanını düzgün sonlandırır."""
        if self.predictive is not None:
            self.predictive.kapat()
        self.registry.shutdown_all()
        self.db.kapat()

    def __enter__(self) -> "CognitiveCore":
        return self

    def __exit__(self, *_: Any) -> None:
        self.kapat()
