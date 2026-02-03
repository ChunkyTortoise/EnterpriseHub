"""
Tests for Brand Asset Service
Validates image processing, CDN integration, and asset management functionality
for the white-label platform.
"""

import pytest
import pytest_asyncio
import asyncio
import tempfile
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from pathlib import Path
import json
import hashlib

import asyncpg
from PIL import Image
from ghl_real_estate_ai.services.brand_asset_service import (
    BrandAssetService,
    BrandAsset,
    AssetType,
    StorageProvider,
    ProcessingStatus,
    AssetUploadRequest,
    AssetVariant
)
from ghl_real_estate_ai.services.cache_service import CacheService


@pytest_asyncio.fixture
async def mock_db_pool():
    """Mock database pool."""
    pool = AsyncMock(spec=asyncpg.Pool)
    return pool


@pytest_asyncio.fixture
async def mock_cache_service():
    """Mock cache service."""
    cache = AsyncMock(spec=CacheService)
    cache.get.return_value = None  # Default to cache miss
    cache.set = AsyncMock()
    cache.delete = AsyncMock()
    return cache


@pytest_asyncio.fixture
async def brand_asset_service(mock_db_pool, mock_cache_service):
    """Create brand asset service instance."""
    service = BrandAssetService(mock_db_pool, mock_cache_service)
    # Mock S3 client
    service.s3_client = MagicMock()
    return service


@pytest.fixture
def sample_image_bytes():
    """Generate sample image bytes for testing."""
    # Create a simple test image
    img = Image.new('RGB', (100, 100), color='red')
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        img.save(tmp.name, 'PNG')
        with open(tmp.name, 'rb') as f:
            return f.read()


@pytest.fixture
def sample_upload_request(sample_image_bytes):
    """Sample asset upload request."""
    return AssetUploadRequest(
        agency_id="agency_001",
        asset_type=AssetType.LOGO,
        asset_name="Company Logo",
        file_content=sample_image_bytes,
        file_name="logo.png",
        client_id="client_001",
        usage_context="header",
        auto_process=True
    )


@pytest.fixture
def sample_brand_asset():
    """Sample brand asset for testing."""
    return BrandAsset(
        asset_id="asset_test_123",
        agency_id="agency_001",
        client_id="client_001",
        asset_type=AssetType.LOGO,
        asset_name="Company Logo",
        file_name="logo.png",
        file_extension=".png",
        mime_type="image/png",
        storage_provider=StorageProvider.S3,
        storage_bucket="test-bucket",
        storage_path="agencies/agency_001/clients/client_001/logo/asset_test_123.png",
        storage_url="https://test-bucket.s3.amazonaws.com/agencies/agency_001/clients/client_001/logo/asset_test_123.png",
        file_size_bytes=1024,
        file_hash="abc123def456",
        usage_context="header",
        created_at=datetime.utcnow()
    )


class TestBrandAssetService:
    """Test suite for brand asset service."""

    async def test_upload_asset_success(self, brand_asset_service, sample_upload_request, mock_db_pool):
        """Test successful asset upload."""
        # Mock database responses
        conn_mock = AsyncMock()
        mock_db_pool.acquire.return_value.__aenter__.return_value = conn_mock
        conn_mock.fetchval.return_value = True  # Agency exists
        conn_mock.fetchrow.return_value = None  # No duplicate asset
        conn_mock.execute = AsyncMock()

        with patch.object(brand_asset_service, '_upload_to_storage') as mock_upload:
            with patch.object(brand_asset_service, '_queue_asset_processing') as mock_process:

                result = await brand_asset_service.upload_asset(sample_upload_request)

                assert result.agency_id == "agency_001"
                assert result.client_id == "client_001"
                assert result.asset_type == AssetType.LOGO
                assert result.asset_name == "Company Logo"
                assert result.file_name == "logo.png"
                assert result.file_extension == ".png"
                assert result.mime_type == "image/png"
                assert result.file_size_bytes == len(sample_upload_request.file_content)
                assert result.asset_id.startswith("asset_")

                mock_upload.assert_called_once()
                mock_process.assert_called_once_with(result.asset_id)

    async def test_upload_asset_duplicate_detection(self, brand_asset_service, sample_upload_request, sample_brand_asset, mock_db_pool):
        """Test duplicate asset detection during upload."""
        # Mock database responses
        conn_mock = AsyncMock()
        mock_db_pool.acquire.return_value.__aenter__.return_value = conn_mock
        conn_mock.fetchval.return_value = True  # Agency exists

        with patch.object(brand_asset_service, '_check_duplicate_asset', return_value=sample_brand_asset):

            result = await brand_asset_service.upload_asset(sample_upload_request)

            assert result.asset_id == sample_brand_asset.asset_id
            # Should return existing asset instead of creating new one

    async def test_upload_asset_validation_failure(self, brand_asset_service, sample_upload_request, mock_db_pool):
        """Test asset upload validation failure."""
        # Mock agency not found
        conn_mock = AsyncMock()
        mock_db_pool.acquire.return_value.__aenter__.return_value = conn_mock
        conn_mock.fetchval.return_value = False  # Agency doesn't exist

        with pytest.raises(ValueError, match="Agency .* not found"):
            await brand_asset_service.upload_asset(sample_upload_request)

    async def test_upload_asset_file_too_large(self, brand_asset_service, sample_upload_request, mock_db_pool):
        """Test asset upload with file too large."""
        # Create oversized file content
        sample_upload_request.file_content = b'x' * (51 * 1024 * 1024)  # 51MB

        # Mock agency exists
        conn_mock = AsyncMock()
        mock_db_pool.acquire.return_value.__aenter__.return_value = conn_mock
        conn_mock.fetchval.return_value = True

        with pytest.raises(ValueError, match="File size exceeds maximum allowed size"):
            await brand_asset_service.upload_asset(sample_upload_request)

    async def test_get_asset_from_cache(self, brand_asset_service, mock_cache_service, sample_brand_asset):
        """Test getting asset from cache."""
        # Setup cache hit
        mock_cache_service.get.return_value = json.dumps({
            "asset_id": "asset_test_123",
            "agency_id": "agency_001",
            "client_id": "client_001",
            "asset_type": "logo",
            "asset_name": "Company Logo",
            "file_name": "logo.png",
            "file_extension": ".png",
            "mime_type": "image/png",
            "storage_provider": "s3",
            "storage_bucket": "test-bucket",
            "storage_path": "test/path",
            "storage_url": "https://example.com/test.png",
            "cdn_url": None,
            "cdn_cache_control": "max-age=31536000",
            "file_size_bytes": 1024,
            "image_width": None,
            "image_height": None,
            "file_hash": "abc123",
            "processing_status": "pending",
            "processed_variants": {},
            "processing_error": None,
            "is_active": True,
            "usage_context": "header",
            "display_order": 0,
            "optimized_size_bytes": None,
            "optimization_ratio": None,
            "webp_variant_url": None,
            "avif_variant_url": None,
            "asset_metadata": {},
            "created_at": "2024-01-01T00:00:00",
            "updated_at": None
        })

        result = await brand_asset_service.get_asset("asset_test_123")

        assert result is not None
        assert result.asset_id == "asset_test_123"
        assert result.agency_id == "agency_001"
        mock_cache_service.get.assert_called_once_with("brand_asset:asset_test_123")

    async def test_get_asset_from_db(self, brand_asset_service, mock_db_pool, mock_cache_service):
        """Test getting asset from database when cache miss."""
        # Setup cache miss
        mock_cache_service.get.return_value = None

        # Mock database response
        conn_mock = AsyncMock()
        mock_db_pool.acquire.return_value.__aenter__.return_value = conn_mock

        db_row = {
            "asset_id": "asset_test_123",
            "agency_id": "agency_001",
            "client_id": "client_001",
            "asset_type": "logo",
            "asset_name": "Company Logo",
            "file_name": "logo.png",
            "file_extension": ".png",
            "mime_type": "image/png",
            "storage_provider": "s3",
            "storage_bucket": "test-bucket",
            "storage_path": "test/path",
            "storage_url": "https://example.com/test.png",
            "cdn_url": None,
            "cdn_cache_control": "max-age=31536000",
            "file_size_bytes": 1024,
            "image_width": 100,
            "image_height": 100,
            "file_hash": "abc123",
            "processing_status": "completed",
            "processed_variants": "{}",
            "processing_error": None,
            "is_active": True,
            "usage_context": "header",
            "display_order": 0,
            "optimized_size_bytes": 800,
            "optimization_ratio": 0.2,
            "webp_variant_url": None,
            "avif_variant_url": None,
            "asset_metadata": "{}",
            "created_at": datetime.utcnow(),
            "updated_at": None
        }

        conn_mock.fetchrow.return_value = db_row

        result = await brand_asset_service.get_asset("asset_test_123")

        assert result is not None
        assert result.asset_id == "asset_test_123"
        assert result.processing_status == ProcessingStatus.COMPLETED
        assert result.image_width == 100
        assert result.image_height == 100

        # Verify cache was set
        mock_cache_service.set.assert_called_once()

    async def test_list_agency_assets(self, brand_asset_service, mock_db_pool):
        """Test listing assets for an agency."""
        conn_mock = AsyncMock()
        mock_db_pool.acquire.return_value.__aenter__.return_value = conn_mock

        # Mock database response with multiple assets
        db_rows = [
            {
                "asset_id": "asset_001",
                "agency_id": "agency_001",
                "client_id": None,
                "asset_type": "logo",
                "asset_name": "Agency Logo",
                "file_name": "agency-logo.png",
                "file_extension": ".png",
                "mime_type": "image/png",
                "storage_provider": "s3",
                "storage_bucket": "test-bucket",
                "storage_path": "test/path1",
                "storage_url": "https://example.com/logo1.png",
                "cdn_url": None,
                "cdn_cache_control": "max-age=31536000",
                "file_size_bytes": 2048,
                "image_width": 200,
                "image_height": 200,
                "file_hash": "hash1",
                "processing_status": "completed",
                "processed_variants": "{}",
                "processing_error": None,
                "is_active": True,
                "usage_context": "header",
                "display_order": 0,
                "optimized_size_bytes": None,
                "optimization_ratio": None,
                "webp_variant_url": None,
                "avif_variant_url": None,
                "asset_metadata": "{}",
                "created_at": datetime.utcnow(),
                "updated_at": None
            },
            {
                "asset_id": "asset_002",
                "agency_id": "agency_001",
                "client_id": "client_001",
                "asset_type": "favicon",
                "asset_name": "Client Favicon",
                "file_name": "favicon.ico",
                "file_extension": ".ico",
                "mime_type": "image/x-icon",
                "storage_provider": "s3",
                "storage_bucket": "test-bucket",
                "storage_path": "test/path2",
                "storage_url": "https://example.com/favicon.ico",
                "cdn_url": None,
                "cdn_cache_control": "max-age=31536000",
                "file_size_bytes": 512,
                "image_width": 32,
                "image_height": 32,
                "file_hash": "hash2",
                "processing_status": "completed",
                "processed_variants": "{}",
                "processing_error": None,
                "is_active": True,
                "usage_context": "header",
                "display_order": 1,
                "optimized_size_bytes": None,
                "optimization_ratio": None,
                "webp_variant_url": None,
                "avif_variant_url": None,
                "asset_metadata": "{}",
                "created_at": datetime.utcnow(),
                "updated_at": None
            }
        ]

        conn_mock.fetch.return_value = db_rows

        result = await brand_asset_service.list_agency_assets("agency_001")

        assert len(result) == 2
        assert result[0].asset_type == AssetType.LOGO
        assert result[1].asset_type == AssetType.FAVICON
        assert all(asset.agency_id == "agency_001" for asset in result)

    async def test_list_agency_assets_with_filters(self, brand_asset_service, mock_db_pool):
        """Test listing agency assets with filters."""
        conn_mock = AsyncMock()
        mock_db_pool.acquire.return_value.__aenter__.return_value = conn_mock
        conn_mock.fetch.return_value = []

        await brand_asset_service.list_agency_assets(
            "agency_001",
            asset_type=AssetType.LOGO,
            client_id="client_001",
            is_active=True
        )

        # Verify correct query parameters were used
        call_args = conn_mock.fetch.call_args
        assert "agency_id = $1" in call_args[0][0]
        assert "is_active = $2" in call_args[0][0]
        assert "asset_type = $3" in call_args[0][0]
        assert "client_id = $4" in call_args[0][0]

    async def test_process_asset_image_success(self, brand_asset_service, sample_brand_asset):
        """Test successful image asset processing."""
        sample_brand_asset.file_extension = ".png"
        sample_brand_asset.processing_status = ProcessingStatus.PENDING

        with patch.object(brand_asset_service, 'get_asset', return_value=sample_brand_asset):
            with patch.object(brand_asset_service, '_update_asset_status') as mock_update_status:
                with patch.object(brand_asset_service, '_download_asset_for_processing') as mock_download:
                    with patch.object(brand_asset_service, '_generate_image_variants') as mock_variants:
                        with patch.object(brand_asset_service, '_generate_modern_formats') as mock_modern:
                            with patch.object(brand_asset_service, '_upload_variant_to_storage') as mock_upload_variant:
                                with patch.object(brand_asset_service, '_update_asset_processing_results') as mock_update_results:

                                    # Mock temp file
                                    temp_file = MagicMock()
                                    temp_file.exists.return_value = True
                                    temp_file.unlink = MagicMock()
                                    mock_download.return_value = temp_file

                                    # Mock variant generation
                                    mock_variants.return_value = {
                                        "thumbnail": AssetVariant("thumbnail", 150, 150, 5000)
                                    }
                                    mock_modern.return_value = {
                                        "webp": AssetVariant("webp", 100, 100, 3000)
                                    }

                                    result = await brand_asset_service.process_asset("asset_test_123")

                                    assert result is True
                                    mock_update_status.assert_called_with("asset_test_123", ProcessingStatus.PROCESSING)
                                    mock_variants.assert_called_once()
                                    mock_modern.assert_called_once()
                                    mock_update_results.assert_called_once()

    async def test_process_asset_not_processable(self, brand_asset_service, sample_brand_asset):
        """Test processing non-image asset."""
        # Set as non-image asset
        sample_brand_asset.file_extension = ".pdf"

        with patch.object(brand_asset_service, 'get_asset', return_value=sample_brand_asset):

            result = await brand_asset_service.process_asset("asset_test_123")

            assert result is True  # Should return True but do nothing

    async def test_process_asset_already_processing(self, brand_asset_service, sample_brand_asset):
        """Test processing asset that's already being processed."""
        sample_brand_asset.processing_status = ProcessingStatus.PROCESSING

        with patch.object(brand_asset_service, 'get_asset', return_value=sample_brand_asset):

            result = await brand_asset_service.process_asset("asset_test_123", force=False)

            assert result is False

    async def test_process_asset_download_failure(self, brand_asset_service, sample_brand_asset):
        """Test asset processing when download fails."""
        sample_brand_asset.file_extension = ".png"

        with patch.object(brand_asset_service, 'get_asset', return_value=sample_brand_asset):
            with patch.object(brand_asset_service, '_update_asset_status') as mock_update_status:
                with patch.object(brand_asset_service, '_download_asset_for_processing', return_value=None):

                    result = await brand_asset_service.process_asset("asset_test_123")

                    assert result is False
                    mock_update_status.assert_any_call("asset_test_123", ProcessingStatus.PROCESSING)
                    mock_update_status.assert_any_call("asset_test_123", ProcessingStatus.FAILED, "Failed to download asset")

    async def test_delete_asset_soft_delete(self, brand_asset_service, sample_brand_asset, mock_db_pool):
        """Test soft delete of asset."""
        conn_mock = AsyncMock()
        mock_db_pool.acquire.return_value.__aenter__.return_value = conn_mock
        conn_mock.execute = AsyncMock()

        with patch.object(brand_asset_service, 'get_asset', return_value=sample_brand_asset):

            result = await brand_asset_service.delete_asset("asset_test_123", permanent=False)

            assert result is True
            # Verify soft delete query
            call_args = conn_mock.execute.call_args
            assert "UPDATE brand_assets SET is_active = false" in call_args[0][0]

    async def test_delete_asset_permanent_delete(self, brand_asset_service, sample_brand_asset, mock_db_pool):
        """Test permanent delete of asset."""
        conn_mock = AsyncMock()
        mock_db_pool.acquire.return_value.__aenter__.return_value = conn_mock
        conn_mock.execute = AsyncMock()

        with patch.object(brand_asset_service, 'get_asset', return_value=sample_brand_asset):
            with patch.object(brand_asset_service, '_delete_from_storage') as mock_delete_storage:
                with patch.object(brand_asset_service, '_delete_variant_from_storage') as mock_delete_variants:

                    result = await brand_asset_service.delete_asset("asset_test_123", permanent=True)

                    assert result is True
                    mock_delete_storage.assert_called_once_with(sample_brand_asset)
                    # Verify permanent delete query
                    call_args = conn_mock.execute.call_args
                    assert "DELETE FROM brand_assets WHERE asset_id = $1" in call_args[0][0]

    async def test_upload_to_s3(self, brand_asset_service, sample_brand_asset):
        """Test uploading asset to S3."""
        content = b"test content"

        # Mock successful S3 upload
        brand_asset_service.s3_client.put_object = MagicMock()

        await brand_asset_service._upload_to_s3(sample_brand_asset, content)

        # Verify S3 upload was called with correct parameters
        brand_asset_service.s3_client.put_object.assert_called_once()
        call_kwargs = brand_asset_service.s3_client.put_object.call_args.kwargs

        assert call_kwargs['Body'] == content
        assert call_kwargs['ContentType'] == sample_brand_asset.mime_type
        assert sample_brand_asset.storage_path != ""
        assert sample_brand_asset.storage_url != ""

    async def test_upload_to_local(self, brand_asset_service, sample_brand_asset):
        """Test uploading asset to local storage."""
        content = b"test content"
        brand_asset_service.storage_provider = StorageProvider.LOCAL

        with patch('aiofiles.open', mock_open()) as mock_file:
            mock_file.return_value.__aenter__.return_value.write = AsyncMock()

            await brand_asset_service._upload_to_local(sample_brand_asset, content)

            assert sample_brand_asset.storage_path != ""
            assert sample_brand_asset.storage_url.startswith("file://")

    async def test_generate_image_variants(self, brand_asset_service, sample_brand_asset):
        """Test image variant generation."""
        # Create a test image file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            img = Image.new('RGB', (800, 600), color='blue')
            img.save(tmp.name, 'PNG')
            temp_file = Path(tmp.name)

        try:
            with patch('tempfile.NamedTemporaryFile') as mock_temp:
                # Mock variant file creation
                variant_files = []
                for variant_name in brand_asset_service.variant_sizes.keys():
                    mock_file = MagicMock()
                    mock_file.stat.return_value.st_size = 1000
                    variant_files.append(mock_file)

                mock_temp.side_effect = [MagicMock(name=f"variant_{i}") for i in range(len(variant_files))]

                with patch.object(brand_asset_service.temp_dir, '__truediv__', return_value=temp_file):
                    with patch.object(temp_file, 'stat') as mock_stat:
                        mock_stat.return_value.st_size = 1000

                        variants = await brand_asset_service._generate_image_variants(sample_brand_asset, temp_file)

                        assert len(variants) > 0
                        # Should generate variants for sizes smaller than original
                        assert 'thumbnail' in variants or 'small' in variants

        finally:
            # Clean up temp file
            if temp_file.exists():
                temp_file.unlink()

    async def test_optimize_storage_costs(self, brand_asset_service, mock_db_pool):
        """Test storage cost optimization analysis."""
        # Mock assets with different characteristics
        sample_assets = [
            BrandAsset(
                asset_id="asset_001",
                agency_id="agency_001",
                client_id=None,
                asset_type=AssetType.LOGO,
                asset_name="Large Logo",
                file_name="logo.png",
                file_extension=".png",
                mime_type="image/png",
                storage_provider=StorageProvider.S3,
                storage_path="test/path1",
                storage_url="https://example.com/logo1.png",
                file_size_bytes=10 * 1024 * 1024,  # 10MB
                processing_status=ProcessingStatus.COMPLETED,
                optimized_size_bytes=5 * 1024 * 1024  # 5MB after optimization
            ),
            BrandAsset(
                asset_id="asset_002",
                agency_id="agency_001",
                client_id="client_001",
                asset_type=AssetType.BANNER,
                asset_name="Banner Image",
                file_name="banner.jpg",
                file_extension=".jpg",
                mime_type="image/jpeg",
                storage_provider=StorageProvider.S3,
                storage_path="test/path2",
                storage_url="https://example.com/banner.jpg",
                file_size_bytes=2 * 1024 * 1024  # 2MB
            )
        ]

        with patch.object(brand_asset_service, 'list_agency_assets', return_value=sample_assets):
            with patch.object(brand_asset_service, '_is_asset_in_use', return_value=False):  # Unused asset
                with patch.object(brand_asset_service, '_find_duplicate_assets', return_value=[]):

                    result = await brand_asset_service.optimize_storage_costs("agency_001")

                    assert result["total_assets"] == 2
                    assert result["total_storage_bytes"] == 12 * 1024 * 1024  # 12MB total
                    assert result["potential_savings_bytes"] == 5 * 1024 * 1024  # 5MB potential savings
                    assert "storage_cost_estimate" in result
                    assert len(result["recommendations"]) > 0

    async def test_check_duplicate_asset(self, brand_asset_service, sample_brand_asset, mock_db_pool):
        """Test duplicate asset detection."""
        conn_mock = AsyncMock()
        mock_db_pool.acquire.return_value.__aenter__.return_value = conn_mock

        # Mock database response for duplicate
        db_row = {
            "asset_id": "existing_asset_123",
            "agency_id": "agency_001",
            "client_id": "client_001",
            "asset_type": "logo",
            "asset_name": "Existing Logo",
            "file_name": "existing_logo.png",
            "file_extension": ".png",
            "mime_type": "image/png",
            "storage_provider": "s3",
            "storage_bucket": "test-bucket",
            "storage_path": "test/path",
            "storage_url": "https://example.com/existing.png",
            "cdn_url": None,
            "cdn_cache_control": "max-age=31536000",
            "file_size_bytes": 1024,
            "image_width": 100,
            "image_height": 100,
            "file_hash": "duplicate_hash",
            "processing_status": "completed",
            "processed_variants": "{}",
            "processing_error": None,
            "is_active": True,
            "usage_context": "header",
            "display_order": 0,
            "optimized_size_bytes": None,
            "optimization_ratio": None,
            "webp_variant_url": None,
            "avif_variant_url": None,
            "asset_metadata": "{}",
            "created_at": datetime.utcnow(),
            "updated_at": None
        }

        conn_mock.fetchrow.return_value = db_row

        result = await brand_asset_service._check_duplicate_asset("duplicate_hash", "agency_001")

        assert result is not None
        assert result.asset_id == "existing_asset_123"
        assert result.file_hash == "duplicate_hash"

    async def test_calculate_optimization_ratio(self, brand_asset_service):
        """Test optimization ratio calculation."""
        asset = BrandAsset(
            asset_id="test",
            agency_id="agency_001",
            client_id=None,
            asset_type=AssetType.LOGO,
            asset_name="Test",
            file_name="test.png",
            file_extension=".png",
            mime_type="image/png",
            storage_provider=StorageProvider.S3,
            storage_path="test",
            storage_url="test",
            file_size_bytes=10000  # 10KB original
        )

        # Add variants with smaller sizes
        asset.processed_variants = {
            "thumbnail": AssetVariant("thumbnail", 150, 150, 2000),  # 2KB
            "webp": AssetVariant("webp", 100, 100, 1000)  # 1KB
        }

        ratio = brand_asset_service._calculate_optimization_ratio(asset)

        # Total variant size: 3KB, original: 10KB
        # Ratio should be 1 - (3KB / 10KB) = 0.7
        assert ratio == 0.7

    async def test_calculate_storage_cost(self, brand_asset_service):
        """Test storage cost calculation."""
        total_bytes = 10 * 1024 * 1024 * 1024  # 10GB

        cost_estimate = brand_asset_service._calculate_storage_cost(total_bytes)

        assert cost_estimate["total_gb"] == 10.0
        assert cost_estimate["monthly_cost_usd"] > 0
        assert cost_estimate["annual_cost_usd"] == cost_estimate["monthly_cost_usd"] * 12


if __name__ == "__main__":
    pytest.main([__file__])