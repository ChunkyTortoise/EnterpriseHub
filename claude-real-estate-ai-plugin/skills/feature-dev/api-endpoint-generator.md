---
name: API Endpoint Generator
description: This skill should be used when the user asks to "generate FastAPI endpoint", "create API routes", "build REST endpoints", "API from specification", "auto-generate endpoints", "endpoint scaffolding", or wants to create production-ready FastAPI endpoints with authentication, validation, and documentation.
version: 1.0.0
---

# API Endpoint Generator

## Overview

Generate production-ready FastAPI endpoints with comprehensive validation, authentication, error handling, and documentation in under 15 minutes. Follows EnterpriseHub patterns and integrates seamlessly with existing service architecture.

**Time Savings:** Reduce API endpoint creation from 2 hours to 15 minutes (87.5% faster)

## Core Capabilities

### 1. Endpoint Specification Parsing
- Natural language to OpenAPI specification
- Request/response model generation
- Authentication requirement detection
- Rate limiting configuration

### 2. Code Generation
- FastAPI router with proper structure
- Pydantic models with validation
- Authentication middleware integration
- Error handling patterns

### 3. Documentation Generation
- OpenAPI/Swagger documentation
- Usage examples
- Integration guides
- Testing instructions

### 4. Security Integration
- JWT authentication patterns
- Rate limiting configuration
- Input validation and sanitization
- CORS policy setup

## Endpoint Generation Templates

### 1. CRUD Endpoint Template

```python
"""
{resource}_routes.py - Auto-generated CRUD endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from uuid import UUID

from ghl_real_estate_ai.api.middleware.auth import get_current_user, require_permissions
from ghl_real_estate_ai.services.{service_name} import {ServiceClass}
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from pydantic import BaseModel, Field

logger = get_logger(__name__)
router = APIRouter(prefix="/api/{resource_plural}", tags=["{resource}"])

# Auto-generated Pydantic Models
class {ResourceName}Base(BaseModel):
    """Base {resource} model with common fields."""
    name: str = Field(..., min_length=1, max_length=255, description="{Resource} name")
    description: Optional[str] = Field(None, max_length=1000, description="{Resource} description")

class {ResourceName}Create({ResourceName}Base):
    """Model for creating new {resource}."""
    # Auto-generated creation fields
    pass

class {ResourceName}Update(BaseModel):
    """Model for updating existing {resource}."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    # Auto-generated update fields

class {ResourceName}Response({ResourceName}Base):
    """Model for {resource} response with metadata."""
    id: UUID
    created_at: str
    updated_at: str
    created_by: str
    # Auto-generated response fields

class {ResourceName}ListResponse(BaseModel):
    """Paginated list response for {resource}s."""
    items: List[{ResourceName}Response]
    total: int
    page: int
    per_page: int
    total_pages: int

# CREATE
@router.post("/", response_model={ResourceName}Response)
async def create_{resource}(
    {resource}_data: {ResourceName}Create,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> {ResourceName}Response:
    """
    Create a new {resource}.

    - **name**: {Resource} name (required)
    - **description**: {Resource} description (optional)
    """
    try:
        logger.info(f"Creating {resource}", extra={{
            "user_id": current_user.get("id"),
            "resource_name": {resource}_data.name
        }})

        service = {ServiceClass}(location_id=current_user.get("location_id"))
        result = await service.create_{resource}(
            {resource}_data.model_dump(),
            created_by=current_user.get("id")
        )

        return {ResourceName}Response(**result)

    except ValueError as e:
        logger.warning(f"Validation error creating {resource}: {{e}}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating {resource}: {{e}}")
        raise HTTPException(status_code=500, detail="Internal server error")

# READ (List)
@router.get("/", response_model={ResourceName}ListResponse)
async def list_{resource_plural}(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search term"),
    sort_by: Optional[str] = Query("created_at", description="Sort field"),
    sort_order: Optional[str] = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> {ResourceName}ListResponse:
    """
    List {resource}s with pagination and filtering.

    - **page**: Page number (default: 1)
    - **per_page**: Items per page (default: 10, max: 100)
    - **search**: Search term for filtering
    - **sort_by**: Field to sort by (default: created_at)
    - **sort_order**: Sort order - asc or desc (default: desc)
    """
    try:
        service = {ServiceClass}(location_id=current_user.get("location_id"))

        result = await service.list_{resource_plural}(
            page=page,
            per_page=per_page,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            user_id=current_user.get("id")
        )

        return {ResourceName}ListResponse(**result)

    except Exception as e:
        logger.error(f"Error listing {resource_plural}: {{e}}")
        raise HTTPException(status_code=500, detail="Internal server error")

# READ (Single)
@router.get("/{{id}}", response_model={ResourceName}Response)
async def get_{resource}(
    id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> {ResourceName}Response:
    """
    Get a specific {resource} by ID.

    - **id**: {Resource} UUID
    """
    try:
        service = {ServiceClass}(location_id=current_user.get("location_id"))
        result = await service.get_{resource}(
            {resource}_id=id,
            user_id=current_user.get("id")
        )

        if not result:
            raise HTTPException(status_code=404, detail="{Resource} not found")

        return {ResourceName}Response(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting {resource}: {{e}}")
        raise HTTPException(status_code=500, detail="Internal server error")

# UPDATE
@router.put("/{{id}}", response_model={ResourceName}Response)
async def update_{resource}(
    id: UUID,
    {resource}_data: {ResourceName}Update,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> {ResourceName}Response:
    """
    Update an existing {resource}.

    - **id**: {Resource} UUID
    - **{resource}_data**: Updated {resource} data
    """
    try:
        logger.info(f"Updating {resource} {{id}}", extra={{
            "user_id": current_user.get("id"),
            "resource_id": str(id)
        }})

        service = {ServiceClass}(location_id=current_user.get("location_id"))

        # Check if resource exists and user has permission
        existing = await service.get_{resource}(
            {resource}_id=id,
            user_id=current_user.get("id")
        )
        if not existing:
            raise HTTPException(status_code=404, detail="{Resource} not found")

        # Only update provided fields
        update_data = {resource}_data.model_dump(exclude_unset=True)
        result = await service.update_{resource}(
            {resource}_id=id,
            update_data=update_data,
            updated_by=current_user.get("id")
        )

        return {ResourceName}Response(**result)

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Validation error updating {resource}: {{e}}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating {resource}: {{e}}")
        raise HTTPException(status_code=500, detail="Internal server error")

# DELETE
@router.delete("/{{id}}")
async def delete_{resource}(
    id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Delete a {resource}.

    - **id**: {Resource} UUID
    """
    try:
        logger.info(f"Deleting {resource} {{id}}", extra={{
            "user_id": current_user.get("id"),
            "resource_id": str(id)
        }})

        service = {ServiceClass}(location_id=current_user.get("location_id"))

        # Check if resource exists and user has permission
        existing = await service.get_{resource}(
            {resource}_id=id,
            user_id=current_user.get("id")
        )
        if not existing:
            raise HTTPException(status_code=404, detail="{Resource} not found")

        await service.delete_{resource}(
            {resource}_id=id,
            user_id=current_user.get("id")
        )

        return {{"message": "{Resource} deleted successfully"}}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting {resource}: {{e}}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

### 2. Action Endpoint Template

```python
"""
{action}_routes.py - Auto-generated action endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from ghl_real_estate_ai.api.middleware.auth import get_current_user
from ghl_real_estate_ai.services.{service_name} import {ServiceClass}
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/{endpoint_prefix}", tags=["{action}"])

class {ActionName}Request(BaseModel):
    """Request model for {action} operation."""
    # Auto-generated request fields based on action requirements

class {ActionName}Response(BaseModel):
    """Response model for {action} operation."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    task_id: Optional[str] = None  # For background tasks

@router.post("/{action_endpoint}")
async def {action_name}(
    request: {ActionName}Request,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> {ActionName}Response:
    """
    {Action description}

    Auto-generated endpoint with:
    - Input validation
    - Authentication checking
    - Background task support
    - Comprehensive error handling
    """
    try:
        logger.info(f"Starting {action}", extra={{
            "user_id": current_user.get("id"),
            "action_params": request.model_dump()
        }})

        service = {ServiceClass}(location_id=current_user.get("location_id"))

        # Validate permissions if needed
        if hasattr(service, 'check_permissions'):
            await service.check_permissions(
                action="{action}",
                user_id=current_user.get("id"),
                params=request.model_dump()
            )

        # Execute action (sync or async based on complexity)
        if hasattr(service, '{action_name}_async'):
            # Background task for long-running operations
            task_id = f"{action}_{current_user.get('id')}_{datetime.now().isoformat()}"
            background_tasks.add_task(
                service.{action_name}_async,
                request=request,
                task_id=task_id,
                user_id=current_user.get("id")
            )

            return {ActionName}Response(
                success=True,
                message="{Action} started successfully",
                task_id=task_id
            )
        else:
            # Immediate execution
            result = await service.{action_name}(
                request=request,
                user_id=current_user.get("id")
            )

            return {ActionName}Response(
                success=True,
                message="{Action} completed successfully",
                data=result
            )

    except PermissionError as e:
        logger.warning(f"Permission denied for {action}: {{e}}")
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    except ValueError as e:
        logger.warning(f"Validation error in {action}: {{e}}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in {action}: {{e}}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Status endpoint for background tasks
@router.get("/task/{{task_id}}/status")
async def get_task_status(
    task_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get status of background task."""
    try:
        service = {ServiceClass}(location_id=current_user.get("location_id"))
        status = await service.get_task_status(task_id, current_user.get("id"))

        if not status:
            raise HTTPException(status_code=404, detail="Task not found")

        return status

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task status: {{e}}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

### 3. Analytics Endpoint Template

```python
"""
{analytics_type}_analytics_routes.py - Auto-generated analytics endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, List, Optional
from datetime import datetime, date
from pydantic import BaseModel, Field

from ghl_real_estate_ai.api.middleware.auth import get_current_user
from ghl_real_estate_ai.services.{analytics_service} import {AnalyticsService}
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/analytics/{analytics_prefix}", tags=["analytics"])

class AnalyticsRequest(BaseModel):
    """Request model for analytics query."""
    start_date: date = Field(..., description="Start date for analysis")
    end_date: date = Field(..., description="End date for analysis")
    metrics: List[str] = Field(default=["all"], description="Metrics to calculate")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Additional filters")
    group_by: Optional[str] = Field(default=None, description="Grouping dimension")

class AnalyticsResponse(BaseModel):
    """Response model for analytics data."""
    metrics: Dict[str, Any]
    time_series: List[Dict[str, Any]]
    summary: Dict[str, Any]
    generated_at: str

@router.get("/dashboard")
async def get_{analytics_type}_dashboard(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get {analytics_type} analytics dashboard data.

    Returns comprehensive analytics for the specified time period.
    """
    try:
        service = {AnalyticsService}(location_id=current_user.get("location_id"))

        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        dashboard_data = await service.get_dashboard_analytics(
            start_date=start_date,
            end_date=end_date,
            user_id=current_user.get("id")
        )

        return {{
            "dashboard": dashboard_data,
            "period": {{
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            }},
            "generated_at": datetime.now().isoformat()
        }}

    except Exception as e:
        logger.error(f"Error getting {analytics_type} dashboard: {{e}}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/query")
async def query_{analytics_type}_analytics(
    request: AnalyticsRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> AnalyticsResponse:
    """
    Execute custom analytics query.

    Supports flexible querying with date ranges, metrics selection,
    filtering, and grouping options.
    """
    try:
        logger.info(f"Analytics query", extra={{
            "user_id": current_user.get("id"),
            "query_params": request.model_dump()
        }})

        service = {AnalyticsService}(location_id=current_user.get("location_id"))

        result = await service.execute_analytics_query(
            query=request,
            user_id=current_user.get("id")
        )

        return AnalyticsResponse(
            metrics=result.get("metrics", {{}},
            time_series=result.get("time_series", []),
            summary=result.get("summary", {{}},
            generated_at=datetime.now().isoformat()
        )

    except ValueError as e:
        logger.warning(f"Invalid analytics query: {{e}}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error executing analytics query: {{e}}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

## Real Estate AI Endpoint Specializations

### 1. Lead Management Endpoints
```python
# Auto-generated lead scoring endpoint
@router.post("/leads/{lead_id}/score")
async def score_lead(
    lead_id: str,
    scoring_config: Optional[Dict[str, Any]] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Score lead based on engagement and behavior patterns."""
```

### 2. Property Matching Endpoints
```python
# Auto-generated property matching endpoint
@router.post("/properties/match")
async def match_properties(
    preferences: PropertyPreferences,
    limit: int = Query(10, le=50),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[PropertyMatch]:
    """Find properties matching client preferences."""
```

### 3. GHL Integration Endpoints
```python
# Auto-generated GHL webhook endpoint
@router.post("/ghl/webhook")
async def handle_ghl_webhook(
    webhook_data: Dict[str, Any],
    signature: str = Header(...),
    background_tasks: BackgroundTasks
) -> Dict[str, str]:
    """Process GoHighLevel webhook events."""
```

### 4. Analytics Endpoints
```python
# Auto-generated lead conversion analytics
@router.get("/analytics/conversion")
async def get_conversion_analytics(
    start_date: date,
    end_date: date,
    agent_id: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> ConversionAnalytics:
    """Get lead conversion analytics and funnel metrics."""
```

## Authentication Patterns

### 1. JWT Authentication
```python
from ghl_real_estate_ai.api.middleware.auth import get_current_user, require_permissions

@router.post("/secure-endpoint")
async def secure_endpoint(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Endpoint requiring JWT authentication."""
```

### 2. Permission-Based Access
```python
@router.post("/admin-endpoint")
async def admin_endpoint(
    current_user: Dict[str, Any] = Depends(require_permissions(["admin", "superuser"]))
):
    """Endpoint requiring specific permissions."""
```

### 3. Tenant Isolation
```python
@router.get("/tenant-data")
async def get_tenant_data(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Endpoint with automatic tenant isolation."""
    service = SomeService(location_id=current_user.get("location_id"))
```

## Error Handling Patterns

### 1. Standard HTTP Errors
```python
try:
    result = await service.some_operation()
    return result
except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
except PermissionError as e:
    raise HTTPException(status_code=403, detail="Insufficient permissions")
except NotFoundError as e:
    raise HTTPException(status_code=404, detail=str(e))
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise HTTPException(status_code=500, detail="Internal server error")
```

### 2. Validation Errors
```python
from pydantic import ValidationError

try:
    validated_data = SomeModel(**input_data)
except ValidationError as e:
    raise HTTPException(
        status_code=422,
        detail={
            "message": "Validation failed",
            "errors": e.errors()
        }
    )
```

## Rate Limiting Configuration

### 1. Global Rate Limiting
```python
from fastapi_limiter.depends import RateLimiter

@router.post("/limited-endpoint")
@limiter.limit("10/minute")
async def limited_endpoint(
    request: Request,
    response: Response
):
    """Endpoint with rate limiting."""
```

### 2. User-Based Rate Limiting
```python
@router.post("/user-limited")
async def user_limited_endpoint(
    current_user: Dict[str, Any] = Depends(get_current_user),
    ratelimit: RateLimiter = Depends(RateLimiter(times=5, seconds=60))
):
    """Endpoint with per-user rate limiting."""
```

## Integration Checklist

### Main Application Integration
- [ ] Add router to main.py imports
- [ ] Include router with proper prefix
- [ ] Configure middleware order
- [ ] Update OpenAPI tags

### Service Integration
- [ ] Service class properly initialized
- [ ] Location ID passed correctly
- [ ] Demo mode handled
- [ ] Error handling consistent

### Authentication Integration
- [ ] JWT middleware applied
- [ ] Permission checks implemented
- [ ] Tenant isolation enforced
- [ ] Security headers added

### Documentation Integration
- [ ] OpenAPI schemas complete
- [ ] Examples provided
- [ ] Error responses documented
- [ ] Integration guide written

## Usage Examples

### Example 1: Lead Scoring Endpoint
```
User: "Create an API endpoint to score leads based on email engagement and website activity"

Generated:
└── api/routes/lead_scoring_routes.py
    ├── POST /api/leads/{id}/score
    ├── GET /api/leads/{id}/score/history
    ├── PUT /api/scoring/weights
    └── GET /api/scoring/metrics
```

### Example 2: Property Search Endpoint
```
User: "Build a property search API with filters for price, location, and features"

Generated:
└── api/routes/property_search_routes.py
    ├── POST /api/properties/search
    ├── GET /api/properties/filters
    ├── POST /api/properties/match
    └── GET /api/properties/suggestions/{lead_id}
```

This skill accelerates API development by generating production-ready FastAPI endpoints with comprehensive validation, authentication, error handling, and documentation in minutes rather than hours.