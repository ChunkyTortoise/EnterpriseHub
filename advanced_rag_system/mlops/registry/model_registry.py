"""
Enterprise Model Registry for RAG System
Demonstrates MLOps model lifecycle management and versioning
"""
import json
import logging
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, asdict
import hashlib

logger = logging.getLogger(__name__)


class ModelStage(Enum):
    """Model lifecycle stages for MLOps governance"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"


class ModelType(Enum):
    """Supported model types in RAG system"""
    EMBEDDING = "embedding"
    RETRIEVAL = "retrieval"
    GENERATION = "generation"
    RANKING = "ranking"
    CLASSIFICATION = "classification"


@dataclass
class ModelMetadata:
    """Model metadata for enterprise tracking"""
    name: str
    version: str
    model_type: ModelType
    stage: ModelStage
    created_at: datetime
    updated_at: datetime
    description: str
    tags: Dict[str, str]
    metrics: Dict[str, float]
    artifacts: Dict[str, str]
    dependencies: List[str]
    checksum: str
    author: str
    approval_required: bool = True
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        # Convert enums and datetime objects
        data['model_type'] = self.model_type.value
        data['stage'] = self.stage.value
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        if self.approved_at:
            data['approved_at'] = self.approved_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelMetadata':
        """Create from dictionary"""
        # Convert back from serialized format
        data['model_type'] = ModelType(data['model_type'])
        data['stage'] = ModelStage(data['stage'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        if data.get('approved_at'):
            data['approved_at'] = datetime.fromisoformat(data['approved_at'])
        return cls(**data)


class ModelRegistry:
    """
    Enterprise Model Registry for RAG System

    Provides model versioning, lifecycle management, and governance
    capabilities essential for production MLOps.

    Features:
    - Model versioning with semantic versioning
    - Stage-based deployment workflow
    - Model approval and governance
    - Artifact tracking and checksums
    - Dependency management
    - Audit trail and lineage
    """

    def __init__(self, registry_path: str = "model_registry"):
        """Initialize model registry"""
        self.registry_path = Path(registry_path)
        self.registry_path.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.registry_path / "metadata.json"
        self.models: Dict[str, List[ModelMetadata]] = {}
        self._load_registry()

    def _load_registry(self) -> None:
        """Load existing registry metadata"""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r') as f:
                    data = json.load(f)

                for model_name, versions in data.items():
                    self.models[model_name] = [
                        ModelMetadata.from_dict(version)
                        for version in versions
                    ]
            logger.info(f"Loaded {len(self.models)} models from registry")
        except Exception as e:
            logger.error(f"Error loading registry: {e}")
            self.models = {}

    def _save_registry(self) -> None:
        """Persist registry metadata"""
        try:
            data = {
                model_name: [version.to_dict() for version in versions]
                for model_name, versions in self.models.items()
            }

            with open(self.metadata_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            logger.info(f"Saved registry with {len(self.models)} models")
        except Exception as e:
            logger.error(f"Error saving registry: {e}")
            raise

    def _calculate_checksum(self, artifact_path: Union[str, Path]) -> str:
        """Calculate SHA256 checksum for artifact validation"""
        try:
            with open(artifact_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception as e:
            logger.warning(f"Could not calculate checksum for {artifact_path}: {e}")
            return ""

    def register_model(
        self,
        name: str,
        version: str,
        model_type: ModelType,
        description: str,
        artifacts: Dict[str, str],
        metrics: Dict[str, float],
        author: str,
        tags: Optional[Dict[str, str]] = None,
        dependencies: Optional[List[str]] = None,
        stage: ModelStage = ModelStage.DEVELOPMENT
    ) -> ModelMetadata:
        """
        Register a new model version

        Args:
            name: Model name
            version: Semantic version (e.g., "1.0.0")
            model_type: Type of model
            description: Model description
            artifacts: Paths to model artifacts
            metrics: Performance metrics
            author: Model author
            tags: Optional metadata tags
            dependencies: Model dependencies
            stage: Initial deployment stage

        Returns:
            ModelMetadata object
        """
        # Validate version doesn't already exist
        if name in self.models:
            existing_versions = [m.version for m in self.models[name]]
            if version in existing_versions:
                raise ValueError(f"Model {name} version {version} already exists")

        # Calculate checksums for artifacts
        checksums = {}
        for artifact_name, path in artifacts.items():
            if Path(path).exists():
                checksums[artifact_name] = self._calculate_checksum(path)

        # Create metadata
        now = datetime.utcnow()
        metadata = ModelMetadata(
            name=name,
            version=version,
            model_type=model_type,
            stage=stage,
            created_at=now,
            updated_at=now,
            description=description,
            tags=tags or {},
            metrics=metrics,
            artifacts=artifacts,
            dependencies=dependencies or [],
            checksum=json.dumps(checksums, sort_keys=True),
            author=author,
            approval_required=(stage != ModelStage.DEVELOPMENT)
        )

        # Add to registry
        if name not in self.models:
            self.models[name] = []
        self.models[name].append(metadata)

        # Sort versions by creation time
        self.models[name].sort(key=lambda m: m.created_at, reverse=True)

        self._save_registry()
        logger.info(f"Registered model {name}:{version} in {stage.value} stage")
        return metadata

    def promote_model(
        self,
        name: str,
        version: str,
        target_stage: ModelStage,
        approved_by: Optional[str] = None
    ) -> ModelMetadata:
        """
        Promote model to higher stage

        Args:
            name: Model name
            version: Model version
            target_stage: Target deployment stage
            approved_by: Approver for governance

        Returns:
            Updated ModelMetadata
        """
        model = self.get_model(name, version)
        if not model:
            raise ValueError(f"Model {name}:{version} not found")

        # Validate stage transition
        stage_order = [
            ModelStage.DEVELOPMENT,
            ModelStage.STAGING,
            ModelStage.PRODUCTION
        ]

        if target_stage in stage_order:
            current_idx = stage_order.index(model.stage) if model.stage in stage_order else -1
            target_idx = stage_order.index(target_stage)

            if target_idx <= current_idx and target_stage != model.stage:
                logger.warning(f"Backwards promotion from {model.stage.value} to {target_stage.value}")

        # Update model metadata
        model.stage = target_stage
        model.updated_at = datetime.utcnow()

        if target_stage == ModelStage.PRODUCTION and approved_by:
            model.approved_by = approved_by
            model.approved_at = datetime.utcnow()

        self._save_registry()
        logger.info(f"Promoted {name}:{version} to {target_stage.value}")
        return model

    def get_model(self, name: str, version: Optional[str] = None) -> Optional[ModelMetadata]:
        """Get specific model version or latest"""
        if name not in self.models:
            return None

        if version is None:
            # Return latest version
            return self.models[name][0] if self.models[name] else None

        # Find specific version
        for model in self.models[name]:
            if model.version == version:
                return model
        return None

    def get_models_by_stage(self, stage: ModelStage) -> List[ModelMetadata]:
        """Get all models in specific stage"""
        result = []
        for versions in self.models.values():
            for model in versions:
                if model.stage == stage:
                    result.append(model)
        return result

    def get_production_model(self, name: str) -> Optional[ModelMetadata]:
        """Get current production model version"""
        if name not in self.models:
            return None

        for model in self.models[name]:
            if model.stage == ModelStage.PRODUCTION:
                return model
        return None

    def list_models(self, model_type: Optional[ModelType] = None) -> Dict[str, List[ModelMetadata]]:
        """List all models, optionally filtered by type"""
        if model_type is None:
            return self.models.copy()

        filtered = {}
        for name, versions in self.models.items():
            type_versions = [v for v in versions if v.model_type == model_type]
            if type_versions:
                filtered[name] = type_versions
        return filtered

    def validate_artifacts(self, name: str, version: str) -> Dict[str, bool]:
        """Validate model artifacts exist and checksums match"""
        model = self.get_model(name, version)
        if not model:
            raise ValueError(f"Model {name}:{version} not found")

        validation_results = {}
        stored_checksums = json.loads(model.checksum) if model.checksum else {}

        for artifact_name, path in model.artifacts.items():
            artifact_path = Path(path)

            # Check existence
            if not artifact_path.exists():
                validation_results[artifact_name] = False
                logger.error(f"Artifact {artifact_name} not found at {path}")
                continue

            # Check checksum if available
            if artifact_name in stored_checksums:
                current_checksum = self._calculate_checksum(path)
                validation_results[artifact_name] = (
                    current_checksum == stored_checksums[artifact_name]
                )
                if not validation_results[artifact_name]:
                    logger.error(f"Checksum mismatch for {artifact_name}")
            else:
                validation_results[artifact_name] = True

        return validation_results

    def get_audit_trail(self, name: str) -> List[Dict[str, Any]]:
        """Get audit trail for model"""
        if name not in self.models:
            return []

        trail = []
        for model in self.models[name]:
            trail.append({
                "version": model.version,
                "stage": model.stage.value,
                "created_at": model.created_at.isoformat(),
                "updated_at": model.updated_at.isoformat(),
                "author": model.author,
                "approved_by": model.approved_by,
                "approved_at": model.approved_at.isoformat() if model.approved_at else None,
                "metrics": model.metrics,
                "description": model.description
            })

        return sorted(trail, key=lambda x: x["created_at"], reverse=True)

    def export_registry(self, export_path: str) -> None:
        """Export entire registry for backup/migration"""
        export_data = {
            "exported_at": datetime.utcnow().isoformat(),
            "models": {
                name: [version.to_dict() for version in versions]
                for name, versions in self.models.items()
            }
        }

        with open(export_path, 'w') as f:
            json.dump(export_data, f, indent=2)

        logger.info(f"Exported registry to {export_path}")


# Example usage for RAG system
def create_rag_model_registry() -> ModelRegistry:
    """Create model registry for RAG system"""
    registry = ModelRegistry("rag_model_registry")

    # Example: Register embedding model
    registry.register_model(
        name="text-embedding-3-large",
        version="1.0.0",
        model_type=ModelType.EMBEDDING,
        description="OpenAI text-embedding-3-large for RAG document embeddings",
        artifacts={
            "config": "configs/embedding_config.json",
            "benchmark_results": "benchmark_results/embedding_perf.json"
        },
        metrics={
            "embedding_latency_ms": 15.2,
            "throughput_docs_per_sec": 150.0,
            "cosine_similarity_avg": 0.847
        },
        author="ai-engineer",
        tags={
            "embedding_dim": "3072",
            "context_length": "8192",
            "use_case": "rag_retrieval"
        },
        dependencies=["openai>=1.6.0"]
    )

    return registry