# Personalization Engine Architecture

## Overview
A domain-agnostic personalization engine for user-specific retrieval based on history and preferences. Designed as a standalone package that can be integrated into any application.

## Architecture Diagram

```mermaid
flowchart TB
    subgraph UserProfile["User Profile Management"]
        UP[user_profile.py]
        PS[profile_store.py]
    end
    
    subgraph Retrieval["Personalized Retrieval"]
        PR[personalized_retrieval.py]
    end
    
    subgraph Feedback["Feedback Loop"]
        FC[feedback_collector.py]
    end
    
    subgraph Storage[(Storage)]
        Redis[(Redis Cache)]
        DB[(Database)]
    end
    
    User[User/Client] -->|Query| PR
    PR -->|Load Profile| PS
    PS -->|Fetch| Redis
    PS -->|Persist| DB
    
    User -->|Interactions| FC
    FC -->|Update Profile| UP
    UP -->|Store| PS
    
    PR -->|Ranked Results| User
```

## Module Descriptions

### 1. user_profile.py
**Purpose**: User profile management with preference extraction

**Key Components**:
- `UserProfile` dataclass - Core user profile structure
- `PreferenceExtractor` - Extract preferences from various sources
- `InterestModel` - Model user interests with confidence scores
- `ProfileManager` - Manage profile lifecycle

**Features**:
- Preference extraction from history
- Interest modeling with confidence scoring
- Explicit preference setting
- Profile versioning

### 2. profile_store.py
**Purpose**: Storage layer for user profiles

**Key Components**:
- `ProfileStore` - Abstract base class
- `RedisProfileStore` - Redis-backed storage
- `InMemoryProfileStore` - In-memory storage for testing
- `ProfileSerializer` - Serialization/deserialization

**Features**:
- Multi-tier caching
- Async operations
- Batch operations
- TTL management

### 3. personalized_retrieval.py
**Purpose**: User-aware result ranking and filtering

**Key Components**:
- `PersonalizedRetriever` - Main retrieval engine
- `RankingEngine` - Score and rank items
- `QueryExpander` - Adaptive query expansion
- `ContentFilter` - Filter based on preferences

**Features**:
- User-aware result ranking
- Content filtering
- Adaptive query expansion
- Multi-factor scoring

### 4. feedback_collector.py
**Purpose**: Explicit and implicit feedback collection

**Key Components**:
- `FeedbackCollector` - Collect and process feedback
- `ExplicitFeedback` - Ratings, likes, dislikes
- `ImplicitFeedback` - Click-through, dwell time
- `FeedbackProcessor` - Update profiles from feedback

**Features**:
- Explicit feedback (ratings, thumbs up/down)
- Implicit feedback (dwell time, clicks, scroll depth)
- Profile update mechanisms
- Feedback weight decay

## Data Models

### UserProfile
```python
@dataclass
class UserProfile:
    user_id: str
    preferences: Dict[str, Preference]
    interests: Dict[str, Interest]
    interaction_history: List[Interaction]
    explicit_preferences: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
```

### Preference
```python
@dataclass
class Preference:
    name: str
    value: Any
    confidence: float
    source: PreferenceSource
    category: PreferenceCategory
    last_updated: datetime
```

### Feedback
```python
@dataclass
class Feedback:
    user_id: str
    item_id: str
    feedback_type: FeedbackType
    value: float
    context: Dict[str, Any]
    timestamp: datetime
```

## Integration Points

The engine is designed to be framework-agnostic:

1. **Storage**: Pluggable storage backends (Redis, PostgreSQL, etc.)
2. **Items**: Works with any item type through generic interfaces
3. **Scoring**: Customizable scoring functions
4. **Feedback**: Extensible feedback types

## Performance Targets

- Profile retrieval: < 10ms
- Preference extraction: < 50ms
- Retrieval ranking: < 100ms for 1000 items
- Feedback processing: < 20ms
