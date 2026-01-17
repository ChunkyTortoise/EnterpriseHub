# API Design Patterns Reference

**Token Budget**: ~3-4k tokens (load on-demand only)
**Trigger**: When designing REST/GraphQL endpoints, implementing pagination, or handling API errors

## REST API Design Principles

### 1. Resource-Based URLs

```python
# ✅ GOOD: Resource-oriented, noun-based
GET    /api/v1/contacts                 # List contacts
GET    /api/v1/contacts/{id}            # Get specific contact
POST   /api/v1/contacts                 # Create contact
PUT    /api/v1/contacts/{id}            # Update contact (full)
PATCH  /api/v1/contacts/{id}            # Update contact (partial)
DELETE /api/v1/contacts/{id}            # Delete contact

# Nested resources
GET    /api/v1/contacts/{id}/properties  # Get contact's properties
POST   /api/v1/contacts/{id}/notes       # Add note to contact

# ❌ BAD: Verb-based, RPC-style
POST   /api/v1/getContact
POST   /api/v1/updateContactInfo
POST   /api/v1/deleteContact
```

### 2. HTTP Status Codes

**Use Semantic Status Codes**:
```python
from fastapi import HTTPException, status

# Success responses
200 OK              # Successful GET, PUT, PATCH, DELETE
201 Created         # Successful POST (resource created)
202 Accepted        # Async operation accepted
204 No Content      # Successful DELETE (no body)

# Client errors
400 Bad Request     # Invalid input, validation failed
401 Unauthorized    # Missing or invalid authentication
403 Forbidden       # Authenticated but not authorized
404 Not Found       # Resource doesn't exist
409 Conflict        # Resource conflict (duplicate, version mismatch)
422 Unprocessable   # Valid syntax, semantic error
429 Too Many Requests  # Rate limit exceeded

# Server errors
500 Internal Server Error  # Unexpected server error
502 Bad Gateway            # Upstream service error
503 Service Unavailable    # Temporary unavailability
```

**Implementation**:
```python
from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/api/v1/contacts")

@router.get("/{contact_id}", response_model=Contact)
async def get_contact(contact_id: str):
    contact = await db.contacts.find_one({"_id": contact_id})

    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contact {contact_id} not found"
        )

    return contact

@router.post("/", response_model=Contact, status_code=status.HTTP_201_CREATED)
async def create_contact(contact: ContactCreate):
    # Check for duplicate
    existing = await db.contacts.find_one({"email": contact.email})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Contact with email {contact.email} already exists"
        )

    # Create new contact
    new_contact = await db.contacts.insert_one(contact.dict())
    return await db.contacts.find_one({"_id": new_contact.inserted_id})
```

### 3. Pagination Patterns

**Offset-Based Pagination** (Simple, familiar):
```python
from pydantic import BaseModel
from typing import List, Generic, TypeVar

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int

@router.get("/contacts", response_model=PaginatedResponse[Contact])
async def list_contacts(
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None
):
    # Validate pagination params
    if page < 1:
        raise HTTPException(400, "Page must be >= 1")
    if page_size < 1 or page_size > 100:
        raise HTTPException(400, "Page size must be 1-100")

    # Build query
    query = {}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}}
        ]

    # Get total count
    total = await db.contacts.count_documents(query)

    # Get paginated results
    skip = (page - 1) * page_size
    items = await db.contacts.find(query).skip(skip).limit(page_size).to_list(None)

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )
```

**Cursor-Based Pagination** (Better performance, real-time friendly):
```python
class CursorPaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    next_cursor: Optional[str]
    has_more: bool

@router.get("/contacts", response_model=CursorPaginatedResponse[Contact])
async def list_contacts(
    cursor: Optional[str] = None,
    limit: int = 20
):
    query = {}

    # Decode cursor (base64 encoded timestamp + id)
    if cursor:
        decoded = base64.b64decode(cursor).decode()
        timestamp, last_id = decoded.split(":")
        query["$or"] = [
            {"created_at": {"$lt": timestamp}},
            {"created_at": timestamp, "_id": {"$lt": last_id}}
        ]

    # Fetch limit + 1 to check if there are more
    items = await db.contacts.find(query)\
        .sort([("created_at", -1), ("_id", -1)])\
        .limit(limit + 1)\
        .to_list(None)

    has_more = len(items) > limit
    if has_more:
        items = items[:limit]

    # Generate next cursor
    next_cursor = None
    if has_more and items:
        last = items[-1]
        cursor_data = f"{last.created_at}:{last.id}"
        next_cursor = base64.b64encode(cursor_data.encode()).decode()

    return CursorPaginatedResponse(
        items=items,
        next_cursor=next_cursor,
        has_more=has_more
    )
```

### 4. Error Response Format

**Consistent Error Structure**:
```python
from pydantic import BaseModel
from typing import Optional, List

class ErrorDetail(BaseModel):
    field: Optional[str]
    message: str
    code: str

class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[List[ErrorDetail]] = None
    request_id: Optional[str] = None

# Usage
@app.exception_handler(ValidationError)
async def validation_exception_handler(request, exc):
    errors = [
        ErrorDetail(
            field=error["loc"][-1],
            message=error["msg"],
            code="validation_error"
        )
        for error in exc.errors()
    ]

    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error="Validation Error",
            message="Request validation failed",
            details=errors,
            request_id=str(uuid.uuid4())
        ).dict()
    )
```

### 5. Versioning

**URL-Based Versioning** (Recommended for simplicity):
```python
from fastapi import APIRouter

# Version 1
v1_router = APIRouter(prefix="/api/v1")

@v1_router.get("/contacts")
async def list_contacts_v1():
    # Old implementation
    pass

# Version 2
v2_router = APIRouter(prefix="/api/v2")

@v2_router.get("/contacts")
async def list_contacts_v2():
    # New implementation with breaking changes
    pass

app.include_router(v1_router)
app.include_router(v2_router)
```

### 6. Filtering and Searching

**Query Parameter Filtering**:
```python
from enum import Enum
from datetime import datetime

class ContactStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    LEAD = "lead"

@router.get("/contacts")
async def list_contacts(
    # Filters
    status: Optional[ContactStatus] = None,
    tags: Optional[List[str]] = Query(None),
    created_after: Optional[datetime] = None,
    created_before: Optional[datetime] = None,

    # Search
    search: Optional[str] = None,

    # Sorting
    sort_by: Optional[str] = "created_at",
    sort_order: Optional[str] = "desc",

    # Pagination
    page: int = 1,
    page_size: int = 20
):
    # Build query
    query = {}

    if status:
        query["status"] = status

    if tags:
        query["tags"] = {"$all": tags}

    if created_after or created_before:
        query["created_at"] = {}
        if created_after:
            query["created_at"]["$gte"] = created_after
        if created_before:
            query["created_at"]["$lte"] = created_before

    if search:
        query["$text"] = {"$search": search}

    # Sorting
    sort_direction = -1 if sort_order == "desc" else 1
    sort = [(sort_by, sort_direction)]

    # Execute query with pagination
    # ... (see pagination examples above)
```

### 7. Rate Limiting Headers

**Communicate Rate Limits to Clients**:
```python
@app.middleware("http")
async def rate_limit_headers(request, call_next):
    client_id = request.client.host

    # Get current rate limit status
    limit = 100
    remaining = await rate_limiter.get_remaining(client_id, limit)
    reset_time = await rate_limiter.get_reset_time(client_id)

    response = await call_next(request)

    # Add rate limit headers
    response.headers["X-RateLimit-Limit"] = str(limit)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Reset"] = str(int(reset_time.timestamp()))

    return response
```

### 8. HATEOAS (Optional, for Discoverability)

**Hypermedia Links in Responses**:
```python
class Contact(BaseModel):
    id: str
    name: str
    email: str

    # HATEOAS links
    _links: dict = {}

    def __init__(self, **data):
        super().__init__(**data)
        self._links = {
            "self": f"/api/v1/contacts/{self.id}",
            "properties": f"/api/v1/contacts/{self.id}/properties",
            "notes": f"/api/v1/contacts/{self.id}/notes",
            "update": f"/api/v1/contacts/{self.id}",
            "delete": f"/api/v1/contacts/{self.id}"
        }
```

## Async API Patterns

### 1. Long-Running Operations

**Async Task Pattern**:
```python
from celery import Celery
import uuid

celery_app = Celery('tasks', broker='redis://localhost:6379')

@router.post("/contacts/import", status_code=202)
async def import_contacts(file: UploadFile):
    """Start async import job."""
    job_id = str(uuid.uuid4())

    # Queue task
    celery_app.send_task(
        'import_contacts_task',
        args=[file.filename, job_id]
    )

    return {
        "job_id": job_id,
        "status": "processing",
        "status_url": f"/api/v1/jobs/{job_id}"
    }

@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Check job status."""
    job = await db.jobs.find_one({"_id": job_id})

    if not job:
        raise HTTPException(404, "Job not found")

    return {
        "job_id": job_id,
        "status": job["status"],  # pending, processing, completed, failed
        "progress": job.get("progress", 0),
        "result": job.get("result"),
        "error": job.get("error")
    }
```

### 2. Webhooks

**Webhook Delivery Pattern**:
```python
class WebhookEvent(BaseModel):
    event_type: str
    timestamp: datetime
    data: dict

async def send_webhook(url: str, event: WebhookEvent, secret: str):
    """Send webhook with signature verification."""
    import hmac
    import hashlib

    payload = event.json()

    # Generate signature
    signature = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()

    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Signature": signature,
        "X-Webhook-Event": event.event_type
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                url,
                content=payload,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            return True
        except Exception as e:
            # Log failure, retry later
            await db.webhook_failures.insert_one({
                "url": url,
                "event": event.dict(),
                "error": str(e),
                "retry_count": 0
            })
            return False
```

## API Documentation

**OpenAPI/Swagger Auto-Documentation**:
```python
from fastapi import FastAPI

app = FastAPI(
    title="GHL Real Estate AI API",
    description="AI-powered real estate lead management and automation",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

@router.post(
    "/contacts",
    response_model=Contact,
    status_code=201,
    summary="Create new contact",
    description="Create a new contact in the CRM. Email must be unique.",
    responses={
        201: {"description": "Contact created successfully"},
        409: {"description": "Contact with email already exists"},
        422: {"description": "Validation error"}
    }
)
async def create_contact(contact: ContactCreate):
    """
    Create a new contact with the following information:
    - **name**: Full name of the contact
    - **email**: Unique email address
    - **phone**: Optional phone number
    - **tags**: Optional list of tags for categorization
    """
    pass
```

---

**Reference Updates**: Review when API standards evolve
**Last Updated**: 2026-01-16
