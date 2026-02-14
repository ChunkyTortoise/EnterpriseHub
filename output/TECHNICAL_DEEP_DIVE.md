# Technical Deep Dive - AI Secretary SaaS

**Purpose**: Advanced technical preparation for in-depth interview questions  
**Target**: Chase Ashley Interview (Feb 12, 2026)

---

## 1. Gmail API Integration Details

### OAuth 2.0 Flow Implementation

```python
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from cryptography.fernet import Fernet
import json

class GmailConnector:
    """
    Handles Gmail OAuth and API interactions.
    
    Security considerations:
    - Tokens encrypted at rest with Fernet
    - Automatic token refresh before expiry
    - Scope limited to minimum required
    """
    
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.compose',
    ]
    
    def __init__(self, encryption_key: bytes, db_session):
        self.fernet = Fernet(encryption_key)
        self.db = db_session
    
    async def connect(self, user_id: str, auth_code: str) -> dict:
        """
        Exchange authorization code for tokens.
        Stores encrypted tokens in database.
        """
        from google_auth_oauthlib.flow import Flow
        
        flow = Flow.from_client_secrets_file(
            'credentials.json',
            scopes=self.SCOPES,
            redirect_uri='urn:ietf:wg:oauth:2.0:oob'
        )
        
        flow.fetch_token(code=auth_code)
        credentials = flow.credentials
        
        # Encrypt and store
        token_data = {
            'access_token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'expiry': credentials.expiry.isoformat() if credentials.expiry else None
        }
        
        encrypted = self.fernet.encrypt(json.dumps(token_data).encode())
        
        await self.db.execute("""
            INSERT INTO email_connections (user_id, provider, encrypted_tokens)
            VALUES ($1, 'gmail', $2)
            ON CONFLICT (user_id, provider) 
            DO UPDATE SET encrypted_tokens = $2
        """, user_id, encrypted)
        
        return {'status': 'connected', 'provider': 'gmail'}
    
    async def get_service(self, user_id: str):
        """
        Get authenticated Gmail service with auto-refresh.
        """
        # Fetch encrypted tokens
        row = await self.db.fetchrow(
            "SELECT encrypted_tokens FROM email_connections WHERE user_id = $1 AND provider = 'gmail'",
            user_id
        )
        
        if not row:
            raise ValueError("Gmail not connected for user")
        
        # Decrypt
        token_data = json.loads(self.fernet.decrypt(row['encrypted_tokens']))
        
        # Create credentials
        credentials = Credentials(
            token=token_data['access_token'],
            refresh_token=token_data['refresh_token'],
            token_uri=token_data['token_uri'],
            client_id=token_data['client_id'],
            client_secret=token_data['client_secret'],
        )
        
        # Refresh if expired
        if credentials.expired:
            credentials.refresh(Request())
            # Update stored tokens
            await self._update_tokens(user_id, credentials)
        
        return build('gmail', 'v1', credentials=credentials)
    
    async def fetch_unread(self, user_id: str, max_results: int = 50) -> list:
        """
        Fetch unread emails for processing.
        """
        service = await self.get_service(user_id)
        
        results = service.users().messages().list(
            userId='me',
            labelIds=['INBOX', 'UNREAD'],
            maxResults=max_results
        ).execute()
        
        messages = []
        for msg in results.get('messages', []):
            full_msg = service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='full'
            ).execute()
            messages.append(self._parse_message(full_msg))
        
        return messages
    
    def _parse_message(self, msg: dict) -> dict:
        """Parse Gmail message into structured format."""
        headers = {h['name']: h['value'] for h in msg['payload']['headers']}
        
        return {
            'id': msg['id'],
            'thread_id': msg['threadId'],
            'from': headers.get('From', ''),
            'to': headers.get('To', ''),
            'subject': headers.get('Subject', ''),
            'date': headers.get('Date', ''),
            'body': self._extract_body(msg['payload']),
            'labels': msg.get('labelIds', []),
        }
```

### Webhook for Real-Time Email Monitoring

```python
from fastapi import APIRouter, Request, BackgroundTasks

router = APIRouter()

@router.post('/webhooks/gmail/{user_id}')
async def gmail_push_notification(
    user_id: str,
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Handle Gmail push notifications via Google Pub/Sub.
    
    Setup:
    1. Create Pub/Sub topic in Google Cloud
    2. Configure Gmail API watch() on topic
    3. This endpoint receives push notifications
    """
    data = await request.json()
    
    # Decode Pub/Sub message
    import base64
    message_data = json.loads(
        base64.b64decode(data['message']['data']).decode()
    )
    
    email_address = message_data.get('emailAddress')
    history_id = message_data.get('historyId')
    
    # Process in background
    background_tasks.add_task(
        process_new_emails,
        user_id,
        history_id
    )
    
    return {'status': 'acknowledged'}

async def process_new_emails(user_id: str, history_id: str):
    """Process new emails since last history ID."""
    connector = GmailConnector(...)
    
    # Get history of changes
    service = await connector.get_service(user_id)
    history = service.users().history().list(
        userId='me',
        startHistoryId=history_id
    ).execute()
    
    for change in history.get('history', []):
        for msg_added in change.get('messagesAdded', []):
            message_id = msg_added['message']['id']
            # Process each new message
            await process_single_email(user_id, message_id)
```

---

## 2. Calendar Integration Deep Dive

### Availability Detection Algorithm

```python
from datetime import datetime, timedelta
from typing import List, Dict, Optional

class CalendarAvailabilityEngine:
    """
    Intelligent availability detection with preference awareness.
    """
    
    def __init__(self, calendar_service, user_preferences: dict):
        self.calendar = calendar_service
        self.prefs = user_preferences
    
    async def find_slots(
        self,
        duration_minutes: int,
        date_range_start: datetime,
        date_range_end: datetime,
        constraints: Optional[dict] = None
    ) -> List[dict]:
        """
        Find available time slots respecting all constraints.
        
        Constraints considered:
        - Business hours (user preference)
        - Buffer time between meetings
        - No-meeting days
        - Preferred meeting times
        - Existing calendar events
        """
        
        # Get busy periods from calendar
        busy_periods = await self._get_busy_periods(
            date_range_start,
            date_range_end
        )
        
        # Generate candidate slots
        candidate_slots = self._generate_candidate_slots(
            date_range_start,
            date_range_end,
            duration_minutes
        )
        
        # Filter out conflicts
        available_slots = []
        for slot in candidate_slots:
            if self._is_available(slot, busy_periods, constraints):
                available_slots.append(slot)
        
        # Score and rank slots
        scored_slots = [
            {**slot, 'score': self._score_slot(slot)}
            for slot in available_slots
        ]
        
        return sorted(scored_slots, key=lambda x: x['score'], reverse=True)
    
    def _generate_candidate_slots(
        self,
        start: datetime,
        end: datetime,
        duration: int
    ) -> List[dict]:
        """Generate all possible meeting slots."""
        slots = []
        current = start
        
        business_hours = self.prefs.get('business_hours', {'start': 9, 'end': 17})
        buffer = self.prefs.get('buffer_minutes', 15)
        no_meeting_days = self.prefs.get('no_meeting_days', [])
        
        while current < end:
            # Skip no-meeting days
            if current.strftime('%A') in no_meeting_days:
                current += timedelta(days=1)
                continue
            
            # Generate slots within business hours
            day_start = current.replace(
                hour=business_hours['start'],
                minute=0,
                second=0
            )
            day_end = current.replace(
                hour=business_hours['end'],
                minute=0,
                second=0
            )
            
            slot_time = day_start
            while slot_time + timedelta(minutes=duration + buffer) <= day_end:
                slots.append({
                    'start': slot_time.isoformat(),
                    'end': (slot_time + timedelta(minutes=duration)).isoformat(),
                    'date': current.strftime('%Y-%m-%d'),
                    'day_of_week': current.strftime('%A'),
                    'time_of_day': self._categorize_time(slot_time.hour)
                })
                slot_time += timedelta(minutes=30)  # 30-min slot granularity
            
            current += timedelta(days=1)
        
        return slots
    
    def _is_available(
        self,
        slot: dict,
        busy_periods: List[dict],
        constraints: Optional[dict]
    ) -> bool:
        """Check if slot conflicts with any busy period."""
        slot_start = datetime.fromisoformat(slot['start'])
        slot_end = datetime.fromisoformat(slot['end'])
        buffer = self.prefs.get('buffer_minutes', 15)
        
        for busy in busy_periods:
            busy_start = datetime.fromisoformat(busy['start'])
            busy_end = datetime.fromisoformat(busy['end'])
            
            # Check overlap with buffer
            if (slot_start < busy_end + timedelta(minutes=buffer) and
                slot_end + timedelta(minutes=buffer) > busy_start):
                return False
        
        # Check additional constraints
        if constraints:
            if constraints.get('avoid_mornings') and slot['time_of_day'] == 'morning':
                return False
            if constraints.get('avoid_friday_afternoon') and slot['day_of_week'] == 'Friday' and slot['time_of_day'] == 'afternoon':
                return False
        
        return True
    
    def _score_slot(self, slot: dict) -> float:
        """
        Score slot based on preferences.
        Higher score = better slot.
        """
        score = 0.0
        
        # Preferred time of day
        preferred_times = self.prefs.get('preferred_meeting_times', ['morning'])
        if slot['time_of_day'] in preferred_times:
            score += 0.4
        
        # Prefer earlier in the week
        day_scores = {'Monday': 0.2, 'Tuesday': 0.15, 'Wednesday': 0.1, 
                      'Thursday': 0.05, 'Friday': 0.0}
        score += day_scores.get(slot['day_of_week'], 0)
        
        # Prefer slots not too early or late in business hours
        hour = datetime.fromisoformat(slot['start']).hour
        if 10 <= hour <= 15:
            score += 0.3  # Core hours bonus
        elif 9 <= hour <= 16:
            score += 0.1  # Edge hours small bonus
        
        return score
```

---

## 3. Task Classification System

### Intent Detection with Claude

```python
from pydantic import BaseModel
from typing import Literal, Optional
import anthropic

class TaskIntent(BaseModel):
    """Structured output for task classification."""
    task_type: Literal[
        'calendar_scheduling',
        'calendar_query',
        'email_draft',
        'email_reply',
        'email_forward',
        'research',
        'reminder',
        'contact_management',
        'general_question'
    ]
    confidence: float
    entities: dict
    priority: Literal['low', 'medium', 'high', 'urgent']
    requires_approval: bool
    suggested_agent: str

class TaskClassifier:
    """
    Classifies user requests into structured intents.
    Uses Claude Haiku for speed and cost efficiency.
    """
    
    INTENT_PROMPT = """
You are a task classification system for an AI secretary. Analyze the user's request and classify it.

Output a JSON object with these fields:
- task_type: One of the predefined types
- confidence: 0.0 to 1.0
- entities: Extracted entities (contacts, dates, durations, topics)
- priority: low/medium/high/urgent
- requires_approval: true if action is irreversible or sensitive
- suggested_agent: Which agent should handle this

Task Types:
- calendar_scheduling: Create, modify, or cancel meetings
- calendar_query: Check availability or existing events
- email_draft: Compose new email
- email_reply: Respond to existing email
- email_forward: Forward email to someone
- research: Look up information
- reminder: Set a reminder or alarm
- contact_management: Add/update contact info
- general_question: General knowledge question

User request: {request}

Context (if any): {context}

Output JSON only:
"""
    
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
    
    async def classify(
        self,
        request: str,
        context: Optional[dict] = None
    ) -> TaskIntent:
        """
        Classify user request into structured intent.
        """
        prompt = self.INTENT_PROMPT.format(
            request=request,
            context=json.dumps(context) if context else "None"
        )
        
        response = self.client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Parse response
        import json
        result = json.loads(response.content[0].text)
        
        return TaskIntent(**result)
    
    async def classify_batch(
        self,
        requests: List[str]
    ) -> List[TaskIntent]:
        """
        Batch classification for efficiency.
        """
        # Group requests into single prompt
        batch_prompt = """
Classify each request. Output a JSON array.

Requests:
{requests}

Output JSON array only:
""".format(requests="\n".join(f"{i+1}. {r}" for i, r in enumerate(requests)))
        
        response = self.client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=2000,
            messages=[{"role": "user", "content": batch_prompt}]
        )
        
        results = json.loads(response.content[0].text)
        return [TaskIntent(**r) for r in results]
```

---

## 4. Preference Learning System

### Learning from User Edits

```python
class PreferenceLearner:
    """
    Learns user preferences from their edits to AI-generated content.
    """
    
    def __init__(self, llm_client, db_session):
        self.llm = llm_client
        self.db = db_session
    
    async def analyze_edit(
        self,
        user_id: str,
        original: str,
        edited: str,
        context: dict
    ) -> dict:
        """
        Analyze what changed and infer preferences.
        """
        prompt = f"""
Compare the original AI-generated content with the user's edit.
Identify what preferences or patterns we can infer.

Original:
{original}

User's Edit:
{edited}

Context: {json.dumps(context)}

Output JSON with inferred preferences:
{{
    "tone_change": "more_formal" | "more_casual" | "no_change",
    "length_change": "shorter" | "longer" | "no_change",
    "specific_phrases_added": ["phrase1", "phrase2"],
    "specific_phrases_removed": ["phrase1", "phrase2"],
    "structure_change": "description of structural changes",
    "inferred_preferences": {{
        "preferred_greeting": "...",
        "preferred_closing": "...",
        "avoid_phrases": [...],
        "prefer_phrases": [...]
    }}
}}
"""
        
        response = await self.llm.generate(prompt)
        insights = json.loads(response)
        
        # Update user preferences
        await self._update_preferences(user_id, insights)
        
        return insights
    
    async def _update_preferences(self, user_id: str, insights: dict):
        """Update stored preferences based on insights."""
        # Fetch current preferences
        current = await self.db.fetchrow(
            "SELECT preferences FROM user_preferences WHERE user_id = $1",
            user_id
        )
        
        prefs = current['preferences'] if current else {}
        
        # Merge with new insights
        inferred = insights.get('inferred_preferences', {})
        
        for key, value in inferred.items():
            if key not in prefs:
                prefs[key] = value
            elif isinstance(value, list):
                # Merge lists, avoiding duplicates
                existing = set(prefs.get(key, []))
                prefs[key] = list(existing | set(value))
            else:
                # Update value
                prefs[key] = value
        
        # Save updated preferences
        await self.db.execute("""
            INSERT INTO user_preferences (user_id, preferences)
            VALUES ($1, $2)
            ON CONFLICT (user_id) DO UPDATE SET preferences = $2
        """, user_id, json.dumps(prefs))
```

---

## 5. Error Handling & Resilience

### Retry Logic with Exponential Backoff

```python
import asyncio
from functools import wraps
from typing import Callable, Type

def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: tuple = (Exception,)
):
    """
    Decorator for retrying async functions with exponential backoff.
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        raise
                    
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    await asyncio.sleep(delay)
            
            raise last_exception
        return wrapper
    return decorator

# Usage
@retry_with_backoff(max_retries=3, exceptions=(ConnectionError, TimeoutError))
async def fetch_gmail_messages(user_id: str):
    """Fetch messages with automatic retry."""
    service = await get_gmail_service(user_id)
    return service.users().messages().list(userId='me').execute()
```

### Circuit Breaker Pattern

```python
from enum import Enum
from datetime import datetime, timedelta

class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovered

class CircuitBreaker:
    """
    Circuit breaker for external API calls.
    Prevents cascading failures.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.state = CircuitState.CLOSED
        self.last_failure_time = None
    
    async def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        
        if self.state == CircuitState.OPEN:
            if self._should_attempt_recovery():
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_recovery(self) -> bool:
        """Check if enough time has passed to try recovery."""
        if self.last_failure_time is None:
            return True
        return datetime.now() - self.last_failure_time > timedelta(seconds=self.recovery_timeout)
    
    def _on_success(self):
        """Reset on successful call."""
        self.failures = 0
        self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        """Handle failure, potentially opening circuit."""
        self.failures += 1
        self.last_failure_time = datetime.now()
        
        if self.failures >= self.failure_threshold:
            self.state = CircuitState.OPEN
```

---

## 6. Performance Optimization

### Caching Strategy

```python
from functools import lru_cache
import hashlib

class MultiTierCache:
    """
    3-tier caching: L1 (memory) -> L2 (Redis) -> L3 (Database)
    """
    
    def __init__(self, redis_client, db_session, l1_size: int = 1000):
        self.redis = redis_client
        self.db = db_session
        self._l1_cache = {}  # Simple dict for L1
        self._l1_size = l1_size
    
    async def get(self, key: str) -> Optional[dict]:
        """Get from cache, checking L1 -> L2 -> L3."""
        
        # L1: In-memory
        if key in self._l1_cache:
            return self._l1_cache[key]
        
        # L2: Redis
        cached = await self.redis.get(key)
        if cached:
            result = json.loads(cached)
            self._l1_cache[key] = result  # Promote to L1
            return result
        
        # L3: Database (if applicable)
        # ... database lookup
        
        return None
    
    async def set(
        self,
        key: str,
        value: dict,
        ttl_seconds: int = 3600
    ):
        """Set in all cache tiers."""
        
        # L1
        if len(self._l1_cache) >= self._l1_size:
            # Simple eviction: remove random item
            self._l1_cache.pop(next(iter(self._l1_cache)))
        self._l1_cache[key] = value
        
        # L2
        await self.redis.setex(
            key,
            ttl_seconds,
            json.dumps(value)
        )
    
    @staticmethod
    def make_key(tenant_id: str, key_type: str, identifier: str) -> str:
        """Generate namespaced cache key."""
        return f"tenant:{tenant_id}:{key_type}:{identifier}"
```

---

## 7. Security Best Practices

### Input Sanitization

```python
import re
from html import escape

class InputSanitizer:
    """
    Sanitize user inputs to prevent injection attacks.
    """
    
    @staticmethod
    def sanitize_email_content(content: str) -> str:
        """Sanitize email content before processing."""
        # Remove potential script tags
        content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.IGNORECASE | re.DOTALL)
        
        # Escape HTML entities
        content = escape(content)
        
        # Remove null bytes
        content = content.replace('\x00', '')
        
        return content.strip()
    
    @staticmethod
    def sanitize_search_query(query: str) -> str:
        """Sanitize search queries."""
        # Remove special characters that could be used for injection
        query = re.sub(r'[;\'"\\]', '', query)
        
        # Limit length
        return query[:500].strip()
```

### PII Redaction

```python
import re

class PIIRedactor:
    """
    Redact PII from logs and responses.
    """
    
    PATTERNS = {
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
        'credit_card': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
    }
    
    @classmethod
    def redact(cls, text: str) -> str:
        """Redact all PII from text."""
        for pii_type, pattern in cls.PATTERNS.items():
            text = re.sub(
                pattern,
                f'[{pii_type.upper()}_REDACTED]',
                text
            )
        return text
```

---

**File Location**: `EnterpriseHub/output/TECHNICAL_DEEP_DIVE.md`
