"""CLIP embedding provider for multi-modal support.

This module provides CLIP-based embeddings for both images and text,
enabling cross-modal search capabilities where images and text can be
embedded into the same latent space.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, List, Optional, Union

from src.core.exceptions import EmbeddingError
from src.embeddings.base import EmbeddingConfig, EmbeddingProvider

if TYPE_CHECKING:
    from PIL import Image


@dataclass
class CLIPEmbeddingConfig(EmbeddingConfig):
    """Configuration for CLIP embedding provider.

    Attributes:
        model: Name of the CLIP model (default: openai/clip-vit-base-patch32)
        dimensions: Vector dimensionality (512 for CLIP base)
        batch_size: Maximum batch size for requests
        max_retries: Maximum retry attempts
        timeout_seconds: Request timeout
        normalize: Whether to normalize embeddings
        device: Device to run model on (cpu/cuda)
        trust_remote_code: Whether to trust remote code for model loading
    """

    model: str = "openai/clip-vit-base-patch32"
    dimensions: int = 512
    batch_size: int = 32
    device: str = "auto"
    trust_remote_code: bool = False


class CLIPEmbeddingProvider(EmbeddingProvider):
    """CLIP embedding provider for multi-modal embeddings.

    This provider uses OpenAI's CLIP model to generate embeddings for both
    images and text in the same latent space, enabling cross-modal search
    capabilities like text-to-image and image-to-text retrieval.

    Features:
    - Image embedding using CLIP vision encoder
    - Text embedding using CLIP text encoder
    - Batch processing for both modalities
    - Automatic device selection (CPU/CUDA)
    - Support for various image formats (PNG, JPEG, etc.)

    Example:
        ```python
        config = CLIPEmbeddingConfig(model="openai/clip-vit-base-patch32")
        provider = CLIPEmbeddingProvider(config)
        await provider.initialize()

        # Embed images
        image_embeddings = await provider.embed_images(
            ["image1.png", "image2.jpg"]
        )

        # Embed texts
        text_embeddings = await provider.embed_texts(
            ["a photo of a cat", "a picture of a dog"]
        )

        # Cross-modal query
        query_embedding = await provider.embed_query("a red car")
        await provider.close()
        ```
    """

    def __init__(
        self,
        config: Optional[CLIPEmbeddingConfig] = None,
        device: Optional[str] = None,
    ) -> None:
        """Initialize the CLIP embedding provider.

        Args:
            config: CLIP embedding configuration
            device: Override device (cpu/cuda/mps), defaults to auto
        """
        self.clip_config = config or CLIPEmbeddingConfig()
        super().__init__(self.clip_config)

        self._device_override = device
        self._device: Optional[str] = None
        self._model: Optional[Any] = None
        self._processor: Optional[Any] = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the CLIP model and processor.

        Loads the CLIP model and processor from Hugging Face.
        This method should be called before any embedding operations.

        Raises:
            EmbeddingError: If model loading fails
        """
        if self._initialized:
            return

        try:
            import torch
            from transformers import CLIPModel, CLIPProcessor

            # Determine device
            if self._device_override:
                self._device = self._device_override
            elif self.clip_config.device == "auto":
                if torch.cuda.is_available():
                    self._device = "cuda"
                elif torch.backends.mps.is_available():
                    self._device = "mps"
                else:
                    self._device = "cpu"
            else:
                self._device = self.clip_config.device

            # Load model and processor
            self._processor = CLIPProcessor.from_pretrained(
                self.clip_config.model,
                trust_remote_code=self.clip_config.trust_remote_code,
            )
            self._model = CLIPModel.from_pretrained(
                self.clip_config.model,
                trust_remote_code=self.clip_config.trust_remote_code,
            )
            self._model.to(self._device)
            self._model.eval()

            self._initialized = True

        except ImportError as e:
            raise EmbeddingError(
                message="Failed to import required dependencies for CLIP",
                details={"error": str(e)},
                provider="clip",
                error_code="IMPORT_ERROR",
            )
        except Exception as e:
            raise EmbeddingError(
                message=f"Failed to load CLIP model: {str(e)}",
                details={"model": self.clip_config.model},
                provider="clip",
                error_code="MODEL_LOAD_ERROR",
            )

    async def close(self) -> None:
        """Release CLIP model resources."""
        if self._model is not None:
            import torch

            # Move model to CPU and delete
            self._model.to("cpu")
            del self._model
            self._model = None

            # Clear CUDA cache if available
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

        self._processor = None
        self._initialized = False

    async def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts.

        This is the standard EmbeddingProvider interface method.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors

        Raises:
            EmbeddingError: If embedding generation fails
        """
        return await self.embed_texts(texts)

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate CLIP embeddings for text inputs.

        Args:
            texts: List of text strings to embed

        Returns:
            List of 512-dimensional embedding vectors

        Raises:
            EmbeddingError: If embedding generation fails
        """
        self._ensure_initialized()
        self._validate_input(texts)

        if not texts:
            return []

        try:
            import torch

            embeddings: List[List[float]] = []

            # Process in batches
            for i in range(0, len(texts), self.clip_config.batch_size):
                batch = texts[i : i + self.clip_config.batch_size]

                # Tokenize and prepare inputs
                inputs = self._processor(
                    text=batch,
                    return_tensors="pt",
                    padding=True,
                    truncation=True,
                )
                inputs = {k: v.to(self._device) for k, v in inputs.items()}

                # Generate embeddings
                with torch.no_grad():
                    text_features = self._model.get_text_features(**inputs)

                # Normalize if configured
                if self.clip_config.normalize:
                    text_features = torch.nn.functional.normalize(text_features, p=2, dim=1)

                # Convert to list
                batch_embeddings = text_features.cpu().numpy().tolist()
                embeddings.extend(batch_embeddings)

            return embeddings

        except Exception as e:
            raise EmbeddingError(
                message=f"Failed to embed texts: {str(e)}",
                details={"text_count": len(texts)},
                provider="clip",
                error_code="TEXT_EMBEDDING_ERROR",
            )

    async def embed_images(self, image_paths: List[str]) -> List[List[float]]:
        """Generate CLIP embeddings for image inputs.

        Args:
            image_paths: List of paths to image files

        Returns:
            List of 512-dimensional embedding vectors

        Raises:
            EmbeddingError: If image loading or embedding fails
        """
        self._ensure_initialized()

        if not image_paths:
            return []

        # Validate image paths
        for i, path in enumerate(image_paths):
            if not os.path.exists(path):
                raise EmbeddingError(
                    message=f"Image file not found at index {i}: {path}",
                    details={"index": i, "path": path},
                    provider="clip",
                    error_code="IMAGE_NOT_FOUND",
                )

        try:
            import torch
            from PIL import Image

            embeddings: List[List[float]] = []

            # Process in batches
            for i in range(0, len(image_paths), self.clip_config.batch_size):
                batch_paths = image_paths[i : i + self.clip_config.batch_size]

                # Load images
                images = []
                for path in batch_paths:
                    try:
                        img = Image.open(path).convert("RGB")
                        images.append(img)
                    except Exception as e:
                        raise EmbeddingError(
                            message=f"Failed to load image: {path}",
                            details={"path": path, "error": str(e)},
                            provider="clip",
                            error_code="IMAGE_LOAD_ERROR",
                        )

                # Process images
                inputs = self._processor(
                    images=images,
                    return_tensors="pt",
                )
                inputs = {k: v.to(self._device) for k, v in inputs.items()}

                # Generate embeddings
                with torch.no_grad():
                    image_features = self._model.get_image_features(**inputs)

                # Normalize if configured
                if self.clip_config.normalize:
                    image_features = torch.nn.functional.normalize(image_features, p=2, dim=1)

                # Convert to list
                batch_embeddings = image_features.cpu().numpy().tolist()
                embeddings.extend(batch_embeddings)

                # Close images to free memory
                for img in images:
                    img.close()

            return embeddings

        except EmbeddingError:
            raise
        except Exception as e:
            raise EmbeddingError(
                message=f"Failed to embed images: {str(e)}",
                details={"image_count": len(image_paths)},
                provider="clip",
                error_code="IMAGE_EMBEDDING_ERROR",
            )

    async def embed_query(self, text: str) -> List[float]:
        """Generate embedding for a single text query.

        Args:
            text: Query text to embed

        Returns:
            Single 512-dimensional embedding vector
        """
        embeddings = await self.embed_texts([text])
        return embeddings[0]

    async def embed_image_query(self, image_path: str) -> List[float]:
        """Generate embedding for a single image query.

        This enables image-to-text search by embedding a query image
        that can be compared against text embeddings.

        Args:
            image_path: Path to the query image

        Returns:
            Single 512-dimensional embedding vector
        """
        embeddings = await self.embed_images([image_path])
        return embeddings[0]

    async def embed_image_batch(self, images: List[Union[str, "Image.Image"]]) -> List[List[float]]:
        """Generate embeddings for a batch of images (paths or PIL Images).

        Args:
            images: List of image paths or PIL Image objects

        Returns:
            List of 512-dimensional embedding vectors
        """
        self._ensure_initialized()

        if not images:
            return []

        try:
            import torch
            from PIL import Image

            embeddings: List[List[float]] = []
            pil_images: List[Image.Image] = []
            need_cleanup: List[int] = []  # Indices of images we loaded

            # Convert paths to PIL Images
            for i, img_input in enumerate(images):
                if isinstance(img_input, str):
                    if not os.path.exists(img_input):
                        raise EmbeddingError(
                            message=f"Image file not found: {img_input}",
                            details={"index": i, "path": img_input},
                            provider="clip",
                            error_code="IMAGE_NOT_FOUND",
                        )
                    try:
                        img = Image.open(img_input).convert("RGB")
                        pil_images.append(img)
                        need_cleanup.append(len(pil_images) - 1)
                    except Exception as e:
                        raise EmbeddingError(
                            message=f"Failed to load image: {img_input}",
                            details={"path": img_input, "error": str(e)},
                            provider="clip",
                            error_code="IMAGE_LOAD_ERROR",
                        )
                else:
                    pil_images.append(img_input)

            # Process in batches
            for i in range(0, len(pil_images), self.clip_config.batch_size):
                batch = pil_images[i : i + self.clip_config.batch_size]

                inputs = self._processor(
                    images=batch,
                    return_tensors="pt",
                )
                inputs = {k: v.to(self._device) for k, v in inputs.items()}

                with torch.no_grad():
                    image_features = self._model.get_image_features(**inputs)

                if self.clip_config.normalize:
                    image_features = torch.nn.functional.normalize(image_features, p=2, dim=1)

                batch_embeddings = image_features.cpu().numpy().tolist()
                embeddings.extend(batch_embeddings)

            # Cleanup loaded images
            for idx in need_cleanup:
                pil_images[idx].close()

            return embeddings

        except EmbeddingError:
            raise
        except Exception as e:
            raise EmbeddingError(
                message=f"Failed to embed image batch: {str(e)}",
                details={"image_count": len(images)},
                provider="clip",
                error_code="IMAGE_EMBEDDING_ERROR",
            )

    async def health_check(self) -> bool:
        """Check if the CLIP model is loaded and functional.

        Returns:
            True if the model is healthy and can generate embeddings
        """
        try:
            if not self._initialized or self._model is None or self._processor is None:
                return False

            # Test with a simple text embedding
            test_text = "health check"
            inputs = self._processor(
                text=[test_text],
                return_tensors="pt",
                padding=True,
                truncation=True,
            )
            inputs = {k: v.to(self._device) for k, v in inputs.items()}

            import torch

            with torch.no_grad():
                _ = self._model.get_text_features(**inputs)

            return True

        except Exception:
            return False

    def get_model_info(self) -> dict[str, Any]:
        """Get information about the CLIP model.

        Returns:
            Dictionary with model information including device
        """
        info = super().get_model_info()
        info.update(
            {
                "device": self._device,
                "supports_images": True,
                "supports_text": True,
                "embedding_space": "shared",
            }
        )
        return info

    def _ensure_initialized(self) -> None:
        """Ensure the provider is initialized.

        Raises:
            EmbeddingError: If not initialized
        """
        if not self._initialized or self._model is None or self._processor is None:
            raise EmbeddingError(
                message="CLIP provider not initialized. Call initialize() first.",
                error_code="NOT_INITIALIZED",
                provider="clip",
            )

    def _validate_input(self, texts: List[str]) -> None:
        """Validate input texts before embedding.

        Args:
            texts: List of texts to validate

        Raises:
            EmbeddingError: If input is invalid
        """
        if not texts:
            raise EmbeddingError(
                message="Empty text list provided",
                error_code="EMPTY_INPUT",
                provider="clip",
            )

        if len(texts) > self.clip_config.batch_size:
            raise EmbeddingError(
                message=f"Batch size {len(texts)} exceeds maximum {self.clip_config.batch_size}",
                error_code="BATCH_TOO_LARGE",
                provider="clip",
                details={"batch_size": len(texts), "max_batch_size": self.clip_config.batch_size},
            )

        for i, text in enumerate(texts):
            if not text or not text.strip():
                raise EmbeddingError(
                    message=f"Empty text at index {i}",
                    error_code="EMPTY_TEXT",
                    provider="clip",
                    details={"index": i},
                )
