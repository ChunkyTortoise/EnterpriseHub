"""
Brand Asset Service - Image Processing and CDN Integration
Handles brand asset upload, processing, optimization, and CDN distribution
for white-label deployments in the $500K ARR platform.
"""

import asyncio
import hashlib
import mimetypes
import os
import secrets
import tempfile
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, IO
from dataclasses import dataclass, asdict
from enum import Enum
import json
import uuid
from pathlib import Path

import aiofiles
import aiohttp
import asyncpg
from PIL import Image, ImageOps
import boto3
from botocore.exceptions import ClientError

from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.cache_service import CacheService

logger = get_logger(__name__)


class AssetType(Enum):
    """Brand asset types."""
    LOGO = "logo"
    FAVICON = "favicon"
    BANNER = "banner"
    BACKGROUND = "background"
    FONT = "font"
    CSS = "css"
    IMAGE = "image"
    DOCUMENT = "document"


class StorageProvider(Enum):
    """Asset storage providers."""
    S3 = "s3"
    GCS = "gcs"
    AZURE = "azure"
    LOCAL = "local"


class ProcessingStatus(Enum):
    """Asset processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AssetVariant:
    """Asset variant (different sizes/formats)."""
    variant_type: str  # thumbnail, medium, large, webp, avif
    width: Optional[int] = None
    height: Optional[int] = None
    file_size: Optional[int] = None
    storage_path: str = ""
    storage_url: str = ""
    cdn_url: str = ""


@dataclass
class BrandAsset:
    """Complete brand asset configuration."""
    asset_id: str
    agency_id: str
    client_id: Optional[str]

    # Asset details
    asset_type: AssetType
    asset_name: str
    file_name: str
    file_extension: str
    mime_type: str

    # Storage
    storage_provider: StorageProvider
    storage_bucket: Optional[str]
    storage_path: str
    storage_url: str

    # CDN Distribution
    cdn_url: Optional[str] = None
    cdn_cache_control: str = "max-age=31536000"  # 1 year cache

    # File metadata
    file_size_bytes: int = 0
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    file_hash: Optional[str] = None

    # Processing
    processing_status: ProcessingStatus = ProcessingStatus.PENDING
    processed_variants: Dict[str, AssetVariant] = None
    processing_error: Optional[str] = None

    # Usage
    is_active: bool = True
    usage_context: Optional[str] = None  # header, footer, email, etc.
    display_order: int = 0

    # Optimization
    optimized_size_bytes: Optional[int] = None
    optimization_ratio: Optional[float] = None
    webp_variant_url: Optional[str] = None
    avif_variant_url: Optional[str] = None

    # Metadata
    asset_metadata: Dict[str, Any] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if self.processed_variants is None:
            self.processed_variants = {}
        if self.asset_metadata is None:
            self.asset_metadata = {}


@dataclass
class AssetUploadRequest:
    """Asset upload request."""
    agency_id: str
    asset_type: AssetType
    asset_name: str
    file_content: bytes
    file_name: str
    client_id: Optional[str] = None
    usage_context: Optional[str] = None
    auto_process: bool = True


class BrandAssetService:
    """
    Service for managing brand assets, image processing, and CDN distribution
    in the white-label platform.
    """

    def __init__(self, db_pool: asyncpg.Pool, cache_service: CacheService):
        """Initialize brand asset service."""
        self.db_pool = db_pool
        self.cache = cache_service

        # Storage configuration
        self.storage_provider = StorageProvider(settings.get("ASSET_STORAGE_PROVIDER", "s3"))
        self.s3_bucket = settings.get("S3_ASSETS_BUCKET")
        self.s3_region = settings.get("AWS_REGION", "us-east-1")
        self.cdn_base_url = settings.get("CDN_BASE_URL")

        # Initialize storage clients
        self.s3_client = None
        if self.storage_provider == StorageProvider.S3:
            self.s3_client = boto3.client(
                's3',
                region_name=self.s3_region,
                aws_access_key_id=settings.get("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=settings.get("AWS_SECRET_ACCESS_KEY")
            )

        # Image processing configuration
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        self.supported_image_types = {'.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp'}
        self.variant_sizes = {
            'thumbnail': (150, 150),
            'small': (300, 300),
            'medium': (600, 600),
            'large': (1200, 1200)
        }

        # Create local temp directory for processing
        self.temp_dir = Path(tempfile.gettempdir()) / "brand_assets"
        self.temp_dir.mkdir(exist_ok=True)

        logger.info(f"Brand asset service initialized with {self.storage_provider.value} storage")

    async def upload_asset(self, request: AssetUploadRequest) -> BrandAsset:
        """Upload and process brand asset."""

        try:
            # Validate upload request
            await self._validate_upload_request(request)

            # Generate asset ID and metadata
            asset_id = f"asset_{int(time.time())}_{secrets.token_hex(8)}"
            file_hash = hashlib.sha256(request.file_content).hexdigest()

            # Check for duplicate assets
            duplicate = await self._check_duplicate_asset(file_hash, request.agency_id)
            if duplicate:
                logger.info(f"Duplicate asset detected for {request.file_name}, returning existing asset")
                return duplicate

            # Determine file metadata
            file_extension = Path(request.file_name).suffix.lower()
            mime_type = mimetypes.guess_type(request.file_name)[0] or 'application/octet-stream'

            # Create asset record
            asset = BrandAsset(
                asset_id=asset_id,
                agency_id=request.agency_id,
                client_id=request.client_id,
                asset_type=request.asset_type,
                asset_name=request.asset_name,
                file_name=request.file_name,
                file_extension=file_extension,
                mime_type=mime_type,
                storage_provider=self.storage_provider,
                storage_bucket=self.s3_bucket,
                storage_path="",  # Will be set during upload
                storage_url="",  # Will be set during upload
                file_size_bytes=len(request.file_content),
                file_hash=file_hash,
                usage_context=request.usage_context,
                created_at=datetime.utcnow()
            )

            # Upload to storage
            await self._upload_to_storage(asset, request.file_content)

            # Save to database
            await self._save_asset_to_db(asset)

            # Process asset if requested
            if request.auto_process and self._is_processable_image(asset):
                await self._queue_asset_processing(asset_id)

            logger.info(f"Asset uploaded successfully: {asset_id}")
            return asset

        except Exception as e:
            logger.error(f"Failed to upload asset {request.file_name}: {e}")
            raise

    async def get_asset(self, asset_id: str) -> Optional[BrandAsset]:
        """Get brand asset by ID."""

        # Check cache first
        cache_key = f"brand_asset:{asset_id}"
        cached = await self.cache.get(cache_key)
        if cached:
            return BrandAsset(**json.loads(cached))

        try:
            async with self.db_pool.acquire() as conn:
                query = """
                    SELECT *
                    FROM brand_assets
                    WHERE asset_id = $1
                """
                row = await conn.fetchrow(query, asset_id)

                if not row:
                    return None

                asset = self._row_to_brand_asset(row)

                # Cache for 30 minutes
                await self.cache.set(cache_key, json.dumps(asdict(asset)), ttl=1800)

                return asset

        except Exception as e:
            logger.error(f"Failed to get asset {asset_id}: {e}")
            return None

    async def list_agency_assets(
        self,
        agency_id: str,
        asset_type: Optional[AssetType] = None,
        client_id: Optional[str] = None,
        is_active: bool = True
    ) -> List[BrandAsset]:
        """List assets for an agency."""

        try:
            async with self.db_pool.acquire() as conn:
                conditions = ["agency_id = $1", "is_active = $2"]
                params = [agency_id, is_active]

                if asset_type:
                    conditions.append(f"asset_type = ${len(params) + 1}")
                    params.append(asset_type.value)

                if client_id is not None:
                    conditions.append(f"client_id = ${len(params) + 1}")
                    params.append(client_id)

                query = f"""
                    SELECT *
                    FROM brand_assets
                    WHERE {' AND '.join(conditions)}
                    ORDER BY display_order, created_at DESC
                """

                rows = await conn.fetch(query, *params)
                return [self._row_to_brand_asset(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to list agency assets for {agency_id}: {e}")
            return []

    async def process_asset(self, asset_id: str, force: bool = False) -> bool:
        """Process asset (generate variants, optimize)."""

        try:
            asset = await self.get_asset(asset_id)
            if not asset:
                raise ValueError(f"Asset {asset_id} not found")

            if not self._is_processable_image(asset):
                logger.info(f"Asset {asset_id} is not processable (not an image)")
                return True

            if asset.processing_status == ProcessingStatus.PROCESSING and not force:
                logger.info(f"Asset {asset_id} is already being processed")
                return False

            # Update status to processing
            await self._update_asset_status(asset_id, ProcessingStatus.PROCESSING)

            # Download asset for processing
            temp_file = await self._download_asset_for_processing(asset)
            if not temp_file:
                await self._update_asset_status(asset_id, ProcessingStatus.FAILED, "Failed to download asset")
                return False

            try:
                # Process image variants
                variants = await self._generate_image_variants(asset, temp_file)

                # Upload variants to storage
                for variant_name, variant in variants.items():
                    await self._upload_variant_to_storage(asset, variant_name, variant)

                # Generate modern format variants (WebP, AVIF)
                modern_variants = await self._generate_modern_formats(asset, temp_file)
                for format_name, variant in modern_variants.items():
                    await self._upload_variant_to_storage(asset, format_name, variant)

                # Update asset with processing results
                asset.processed_variants = {**variants, **modern_variants}
                asset.processing_status = ProcessingStatus.COMPLETED
                asset.optimization_ratio = self._calculate_optimization_ratio(asset)

                # Update database
                await self._update_asset_processing_results(asset)

                logger.info(f"Asset processing completed for {asset_id}")
                return True

            finally:
                # Clean up temp file
                if temp_file.exists():
                    temp_file.unlink()

        except Exception as e:
            logger.error(f"Failed to process asset {asset_id}: {e}")
            await self._update_asset_status(asset_id, ProcessingStatus.FAILED, str(e))
            return False

    async def delete_asset(self, asset_id: str, permanent: bool = False) -> bool:
        """Delete asset (soft delete by default)."""

        try:
            asset = await self.get_asset(asset_id)
            if not asset:
                return False

            if permanent:
                # Delete from storage
                await self._delete_from_storage(asset)

                # Delete variants
                for variant in asset.processed_variants.values():
                    await self._delete_variant_from_storage(variant)

                # Delete from database
                async with self.db_pool.acquire() as conn:
                    await conn.execute("DELETE FROM brand_assets WHERE asset_id = $1", asset_id)

                logger.info(f"Permanently deleted asset {asset_id}")
            else:
                # Soft delete
                async with self.db_pool.acquire() as conn:
                    await conn.execute(
                        "UPDATE brand_assets SET is_active = false, updated_at = $1 WHERE asset_id = $2",
                        datetime.utcnow(), asset_id
                    )

                logger.info(f"Soft deleted asset {asset_id}")

            # Clear cache
            await self.cache.delete(f"brand_asset:{asset_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete asset {asset_id}: {e}")
            return False

    async def optimize_storage_costs(self, agency_id: str) -> Dict[str, Any]:
        """Analyze and optimize storage costs for agency."""

        try:
            # Get all assets for agency
            assets = await self.list_agency_assets(agency_id)

            optimization_results = {
                "total_assets": len(assets),
                "total_storage_bytes": 0,
                "potential_savings_bytes": 0,
                "recommendations": []
            }

            for asset in assets:
                optimization_results["total_storage_bytes"] += asset.file_size_bytes

                # Check for optimization opportunities
                if asset.processing_status == ProcessingStatus.COMPLETED:
                    if asset.optimized_size_bytes and asset.optimized_size_bytes < asset.file_size_bytes:
                        savings = asset.file_size_bytes - asset.optimized_size_bytes
                        optimization_results["potential_savings_bytes"] += savings

                # Check for unused assets
                if not await self._is_asset_in_use(asset):
                    optimization_results["recommendations"].append({
                        "type": "unused_asset",
                        "asset_id": asset.asset_id,
                        "asset_name": asset.asset_name,
                        "size_bytes": asset.file_size_bytes
                    })

                # Check for duplicate assets
                duplicates = await self._find_duplicate_assets(asset)
                if duplicates:
                    optimization_results["recommendations"].append({
                        "type": "duplicate_assets",
                        "asset_id": asset.asset_id,
                        "duplicates": [d.asset_id for d in duplicates],
                        "potential_savings": sum(d.file_size_bytes for d in duplicates)
                    })

            optimization_results["storage_cost_estimate"] = self._calculate_storage_cost(
                optimization_results["total_storage_bytes"]
            )

            return optimization_results

        except Exception as e:
            logger.error(f"Failed to optimize storage costs for agency {agency_id}: {e}")
            return {"error": str(e)}

    # Private helper methods

    async def _validate_upload_request(self, request: AssetUploadRequest) -> None:
        """Validate asset upload request."""
        if len(request.file_content) > self.max_file_size:
            raise ValueError(f"File size exceeds maximum allowed size of {self.max_file_size} bytes")

        if not request.file_name:
            raise ValueError("File name is required")

        # Check if agency exists
        async with self.db_pool.acquire() as conn:
            agency_exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM agencies WHERE agency_id = $1)",
                request.agency_id
            )
            if not agency_exists:
                raise ValueError(f"Agency {request.agency_id} not found")

    async def _check_duplicate_asset(self, file_hash: str, agency_id: str) -> Optional[BrandAsset]:
        """Check for duplicate asset by file hash."""
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM brand_assets WHERE file_hash = $1 AND agency_id = $2 AND is_active = true",
                    file_hash, agency_id
                )
                return self._row_to_brand_asset(row) if row else None
        except Exception:
            return None

    async def _upload_to_storage(self, asset: BrandAsset, content: bytes) -> None:
        """Upload asset to configured storage provider."""
        if self.storage_provider == StorageProvider.S3:
            await self._upload_to_s3(asset, content)
        elif self.storage_provider == StorageProvider.LOCAL:
            await self._upload_to_local(asset, content)
        else:
            raise ValueError(f"Storage provider {self.storage_provider} not implemented")

    async def _upload_to_s3(self, asset: BrandAsset, content: bytes) -> None:
        """Upload asset to S3."""
        if not self.s3_client or not self.s3_bucket:
            raise ValueError("S3 client or bucket not configured")

        # Generate storage path
        storage_path = f"agencies/{asset.agency_id}"
        if asset.client_id:
            storage_path += f"/clients/{asset.client_id}"
        storage_path += f"/{asset.asset_type.value}/{asset.asset_id}{asset.file_extension}"

        try:
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=storage_path,
                Body=content,
                ContentType=asset.mime_type,
                CacheControl=asset.cdn_cache_control,
                Metadata={
                    'asset-id': asset.asset_id,
                    'agency-id': asset.agency_id,
                    'asset-type': asset.asset_type.value
                }
            )

            # Set storage URLs
            asset.storage_path = storage_path
            asset.storage_url = f"https://{self.s3_bucket}.s3.{self.s3_region}.amazonaws.com/{storage_path}"

            if self.cdn_base_url:
                asset.cdn_url = f"{self.cdn_base_url}/{storage_path}"

        except Exception as e:
            logger.error(f"Failed to upload asset {asset.asset_id} to S3: {e}")
            raise

    async def _upload_to_local(self, asset: BrandAsset, content: bytes) -> None:
        """Upload asset to local storage."""
        # Create directory structure
        storage_dir = Path("data/brand_assets") / asset.agency_id
        if asset.client_id:
            storage_dir = storage_dir / "clients" / asset.client_id
        storage_dir = storage_dir / asset.asset_type.value
        storage_dir.mkdir(parents=True, exist_ok=True)

        # Save file
        file_path = storage_dir / f"{asset.asset_id}{asset.file_extension}"
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)

        # Set storage URLs
        asset.storage_path = str(file_path)
        asset.storage_url = f"file://{file_path.absolute()}"

    def _is_processable_image(self, asset: BrandAsset) -> bool:
        """Check if asset is a processable image."""
        return asset.file_extension in self.supported_image_types

    async def _queue_asset_processing(self, asset_id: str) -> None:
        """Queue asset for background processing."""
        # In a production system, this would queue the task in Redis/Celery
        # For now, we'll process immediately in a background task
        asyncio.create_task(self.process_asset(asset_id))

    async def _download_asset_for_processing(self, asset: BrandAsset) -> Optional[Path]:
        """Download asset to temp file for processing."""
        try:
            temp_file = self.temp_dir / f"{asset.asset_id}{asset.file_extension}"

            if self.storage_provider == StorageProvider.S3:
                # Download from S3
                response = self.s3_client.get_object(Bucket=self.s3_bucket, Key=asset.storage_path)
                content = response['Body'].read()
            elif self.storage_provider == StorageProvider.LOCAL:
                # Read from local file
                async with aiofiles.open(asset.storage_path, 'rb') as f:
                    content = await f.read()
            else:
                return None

            # Save to temp file
            async with aiofiles.open(temp_file, 'wb') as f:
                await f.write(content)

            return temp_file

        except Exception as e:
            logger.error(f"Failed to download asset {asset.asset_id} for processing: {e}")
            return None

    async def _generate_image_variants(self, asset: BrandAsset, source_file: Path) -> Dict[str, AssetVariant]:
        """Generate different sized variants of the image."""
        variants = {}

        try:
            # Open image
            with Image.open(source_file) as img:
                # Store original dimensions
                original_width, original_height = img.size

                # Update asset with image metadata
                asset.image_width = original_width
                asset.image_height = original_height

                # Generate variants
                for variant_name, (max_width, max_height) in self.variant_sizes.items():
                    # Skip if original is smaller
                    if original_width <= max_width and original_height <= max_height:
                        continue

                    # Resize maintaining aspect ratio
                    img_copy = img.copy()
                    img_copy.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

                    # Optimize
                    if img_copy.mode in ('RGBA', 'P'):
                        img_copy = img_copy.convert('RGB')

                    # Save variant
                    variant_file = self.temp_dir / f"{asset.asset_id}_{variant_name}{asset.file_extension}"
                    img_copy.save(variant_file, optimize=True, quality=85)

                    # Create variant record
                    variant = AssetVariant(
                        variant_type=variant_name,
                        width=img_copy.width,
                        height=img_copy.height,
                        file_size=variant_file.stat().st_size
                    )

                    variants[variant_name] = variant

                return variants

        except Exception as e:
            logger.error(f"Failed to generate image variants for {asset.asset_id}: {e}")
            return {}

    async def _generate_modern_formats(self, asset: BrandAsset, source_file: Path) -> Dict[str, AssetVariant]:
        """Generate modern format variants (WebP, AVIF)."""
        variants = {}

        try:
            with Image.open(source_file) as img:
                # Generate WebP
                webp_file = self.temp_dir / f"{asset.asset_id}.webp"
                img.save(webp_file, "WebP", optimize=True, quality=85)

                variants["webp"] = AssetVariant(
                    variant_type="webp",
                    width=img.width,
                    height=img.height,
                    file_size=webp_file.stat().st_size
                )

                # Generate AVIF (if supported)
                try:
                    avif_file = self.temp_dir / f"{asset.asset_id}.avif"
                    img.save(avif_file, "AVIF", quality=85)

                    variants["avif"] = AssetVariant(
                        variant_type="avif",
                        width=img.width,
                        height=img.height,
                        file_size=avif_file.stat().st_size
                    )
                except Exception:
                    # AVIF support might not be available
                    pass

                return variants

        except Exception as e:
            logger.error(f"Failed to generate modern formats for {asset.asset_id}: {e}")
            return {}

    async def _upload_variant_to_storage(self, asset: BrandAsset, variant_name: str, variant: AssetVariant) -> None:
        """Upload variant to storage."""
        variant_file = self.temp_dir / f"{asset.asset_id}_{variant_name}.{variant.variant_type}"

        # Read variant file
        async with aiofiles.open(variant_file, 'rb') as f:
            content = await f.read()

        # Upload based on storage provider
        if self.storage_provider == StorageProvider.S3:
            storage_path = f"{asset.storage_path.rsplit('.', 1)[0]}_{variant_name}.{variant.variant_type}"
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=storage_path,
                Body=content,
                ContentType=f"image/{variant.variant_type}",
                CacheControl=asset.cdn_cache_control
            )

            variant.storage_path = storage_path
            variant.storage_url = f"https://{self.s3_bucket}.s3.{self.s3_region}.amazonaws.com/{storage_path}"
            if self.cdn_base_url:
                variant.cdn_url = f"{self.cdn_base_url}/{storage_path}"

        # Clean up temp file
        if variant_file.exists():
            variant_file.unlink()

    async def _update_asset_status(self, asset_id: str, status: ProcessingStatus, error_message: Optional[str] = None) -> None:
        """Update asset processing status."""
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE brand_assets
                SET processing_status = $1, processing_error = $2, updated_at = $3
                WHERE asset_id = $4
                """,
                status.value, error_message, datetime.utcnow(), asset_id
            )

        # Clear cache
        await self.cache.delete(f"brand_asset:{asset_id}")

    async def _update_asset_processing_results(self, asset: BrandAsset) -> None:
        """Update asset with processing results."""
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE brand_assets
                SET processing_status = $1, processed_variants = $2, optimization_ratio = $3,
                    image_width = $4, image_height = $5, optimized_size_bytes = $6,
                    updated_at = $7
                WHERE asset_id = $8
                """,
                asset.processing_status.value,
                json.dumps({k: asdict(v) for k, v in asset.processed_variants.items()}),
                asset.optimization_ratio,
                asset.image_width,
                asset.image_height,
                asset.optimized_size_bytes,
                datetime.utcnow(),
                asset.asset_id
            )

        # Clear cache
        await self.cache.delete(f"brand_asset:{asset.asset_id}")

    def _calculate_optimization_ratio(self, asset: BrandAsset) -> float:
        """Calculate optimization ratio for processed asset."""
        if not asset.processed_variants:
            return 0.0

        total_variant_size = sum(v.file_size for v in asset.processed_variants.values() if v.file_size)
        if total_variant_size == 0:
            return 0.0

        return round(1.0 - (total_variant_size / asset.file_size_bytes), 4)

    async def _save_asset_to_db(self, asset: BrandAsset) -> None:
        """Save brand asset to database."""
        async with self.db_pool.acquire() as conn:
            query = """
                INSERT INTO brand_assets (
                    asset_id, agency_id, client_id, asset_type, asset_name,
                    file_name, file_extension, mime_type, storage_provider,
                    storage_bucket, storage_path, storage_url, cdn_url,
                    cdn_cache_control, file_size_bytes, image_width, image_height,
                    file_hash, processing_status, is_active, usage_context,
                    display_order, asset_metadata, created_at, updated_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14,
                    $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25
                )
            """
            await conn.execute(
                query,
                asset.asset_id, asset.agency_id, asset.client_id,
                asset.asset_type.value, asset.asset_name, asset.file_name,
                asset.file_extension, asset.mime_type, asset.storage_provider.value,
                asset.storage_bucket, asset.storage_path, asset.storage_url,
                asset.cdn_url, asset.cdn_cache_control, asset.file_size_bytes,
                asset.image_width, asset.image_height, asset.file_hash,
                asset.processing_status.value, asset.is_active,
                asset.usage_context, asset.display_order,
                json.dumps(asset.asset_metadata), asset.created_at,
                datetime.utcnow()
            )

    def _row_to_brand_asset(self, row) -> BrandAsset:
        """Convert database row to BrandAsset."""
        processed_variants = {}
        if row["processed_variants"]:
            variants_data = json.loads(row["processed_variants"])
            for name, data in variants_data.items():
                processed_variants[name] = AssetVariant(**data)

        return BrandAsset(
            asset_id=row["asset_id"],
            agency_id=row["agency_id"],
            client_id=row["client_id"],
            asset_type=AssetType(row["asset_type"]),
            asset_name=row["asset_name"],
            file_name=row["file_name"],
            file_extension=row["file_extension"],
            mime_type=row["mime_type"],
            storage_provider=StorageProvider(row["storage_provider"]),
            storage_bucket=row["storage_bucket"],
            storage_path=row["storage_path"],
            storage_url=row["storage_url"],
            cdn_url=row["cdn_url"],
            cdn_cache_control=row["cdn_cache_control"],
            file_size_bytes=row["file_size_bytes"],
            image_width=row["image_width"],
            image_height=row["image_height"],
            file_hash=row["file_hash"],
            processing_status=ProcessingStatus(row["processing_status"]),
            processed_variants=processed_variants,
            processing_error=row["processing_error"],
            is_active=row["is_active"],
            usage_context=row["usage_context"],
            display_order=row["display_order"],
            optimized_size_bytes=row["optimized_size_bytes"],
            optimization_ratio=row["optimization_ratio"],
            webp_variant_url=row["webp_variant_url"],
            avif_variant_url=row["avif_variant_url"],
            asset_metadata=json.loads(row["asset_metadata"]) if row["asset_metadata"] else {},
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )

    async def _delete_from_storage(self, asset: BrandAsset) -> None:
        """Delete asset from storage."""
        if self.storage_provider == StorageProvider.S3:
            try:
                self.s3_client.delete_object(Bucket=self.s3_bucket, Key=asset.storage_path)
            except Exception as e:
                logger.warning(f"Failed to delete asset {asset.asset_id} from S3: {e}")

    async def _delete_variant_from_storage(self, variant: AssetVariant) -> None:
        """Delete variant from storage."""
        if self.storage_provider == StorageProvider.S3:
            try:
                self.s3_client.delete_object(Bucket=self.s3_bucket, Key=variant.storage_path)
            except Exception as e:
                logger.warning(f"Failed to delete variant from S3: {e}")

    async def _is_asset_in_use(self, asset: BrandAsset) -> bool:
        """Check if asset is currently being used."""
        # Check brand configurations
        async with self.db_pool.acquire() as conn:
            in_use = await conn.fetchval(
                """
                SELECT EXISTS(
                    SELECT 1 FROM brand_configurations
                    WHERE (primary_logo_asset_id = $1 OR secondary_logo_asset_id = $1 OR favicon_asset_id = $1)
                    AND is_active = true
                )
                """,
                asset.asset_id
            )
            return bool(in_use)

    async def _find_duplicate_assets(self, asset: BrandAsset) -> List[BrandAsset]:
        """Find duplicate assets with same file hash."""
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM brand_assets
                WHERE file_hash = $1 AND asset_id != $2 AND is_active = true
                """,
                asset.file_hash, asset.asset_id
            )
            return [self._row_to_brand_asset(row) for row in rows]

    def _calculate_storage_cost(self, total_bytes: int) -> Dict[str, float]:
        """Calculate estimated storage costs."""
        # AWS S3 pricing estimates (simplified)
        s3_cost_per_gb = 0.023  # $0.023 per GB per month for Standard storage
        total_gb = total_bytes / (1024 ** 3)

        return {
            "total_gb": round(total_gb, 2),
            "monthly_cost_usd": round(total_gb * s3_cost_per_gb, 2),
            "annual_cost_usd": round(total_gb * s3_cost_per_gb * 12, 2)
        }


# Factory function for service initialization
def get_brand_asset_service(db_pool: asyncpg.Pool, cache_service: CacheService) -> BrandAssetService:
    """Get configured brand asset service instance."""
    return BrandAssetService(db_pool, cache_service)