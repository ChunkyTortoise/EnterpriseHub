"""
Database Service for Customer Intelligence Platform.

Provides database operations for customer intelligence data:
- Customer management
- Conversation history
- Scoring data
- Knowledge base documents
- Department context
"""

import asyncio
import json
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union
import logging
import os

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class CustomerStatus(Enum):
    """Customer status enumeration."""
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    NURTURING = "nurturing"
    HOT = "hot"
    CONVERTED = "converted"
    LOST = "lost"
    SILENT = "silent"


class ScoreType(Enum):
    """Score type enumeration."""
    LEAD_SCORING = "lead_scoring"
    ENGAGEMENT = "engagement_prediction"
    CHURN = "churn_prediction"
    LTV = "customer_ltv"


class ConversationRole(Enum):
    """Conversation role enumeration."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


# ============================================================================
# Database Models
# ============================================================================

class Customer(BaseModel):
    """Customer data model."""
    id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    industry: Optional[str] = None
    department: str = "General"
    status: CustomerStatus = CustomerStatus.NEW
    created_at: datetime
    updated_at: datetime
    last_interaction_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    tags: List[str] = []
    
    class Config:
        use_enum_values = True


class CustomerScore(BaseModel):
    """Customer score data model."""
    id: str
    customer_id: str
    score_type: ScoreType
    score: float
    confidence: float
    model_version: str
    features: Dict[str, Any]
    created_at: datetime
    
    class Config:
        use_enum_values = True


class ConversationMessage(BaseModel):
    """Conversation message data model."""
    id: str
    conversation_id: str
    customer_id: str
    role: ConversationRole
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        use_enum_values = True


class KnowledgeDocument(BaseModel):
    """Knowledge base document model."""
    id: str
    title: str
    content: str
    document_type: str
    department: Optional[str] = None
    tags: List[str] = []
    created_at: datetime
    updated_at: datetime
    metadata: Optional[Dict[str, Any]] = None


# ============================================================================
# Mock Database Implementation
# ============================================================================

class MockDatabase:
    """Mock database implementation for demo purposes."""
    
    def __init__(self):
        self.customers: Dict[str, Customer] = {}
        self.scores: Dict[str, CustomerScore] = {}
        self.conversations: Dict[str, List[ConversationMessage]] = {}
        self.knowledge_docs: Dict[str, KnowledgeDocument] = {}
        logger.info("Initialized MockDatabase")
        
        # Initialize with sample data
        self._initialize_sample_data()
    
    def _initialize_sample_data(self):
        """Initialize with sample customers and data."""
        sample_customers = [
            {
                "name": "Acme Corporation",
                "email": "contact@acme.com",
                "company": "Acme Corp",
                "industry": "Technology",
                "department": "Sales",
                "status": CustomerStatus.QUALIFIED
            },
            {
                "name": "TechStart Inc",
                "email": "hello@techstart.com", 
                "company": "TechStart Inc",
                "industry": "Software",
                "department": "Marketing",
                "status": CustomerStatus.HOT
            },
            {
                "name": "Global Solutions",
                "email": "info@globalsol.com",
                "company": "Global Solutions Ltd",
                "industry": "Consulting",
                "department": "Customer Success",
                "status": CustomerStatus.NEW
            }
        ]
        
        for customer_data in sample_customers:
            customer = Customer(
                id=str(uuid.uuid4()),
                created_at=datetime.now(),
                updated_at=datetime.now(),
                **customer_data
            )
            self.customers[customer.id] = customer
            
            # Add sample scores
            score = CustomerScore(
                id=str(uuid.uuid4()),
                customer_id=customer.id,
                score_type=ScoreType.LEAD_SCORING,
                score=0.7 + (hash(customer.id) % 30) / 100,
                confidence=0.8 + (hash(customer.id) % 20) / 100,
                model_version="v1.0",
                features={"engagement": 0.8, "company_size": 0.6},
                created_at=datetime.now()
            )
            self.scores[score.id] = score

    # Customer operations
    async def create_customer(self, customer_data: Dict[str, Any]) -> Customer:
        """Create a new customer."""
        customer = Customer(
            id=str(uuid.uuid4()),
            created_at=datetime.now(),
            updated_at=datetime.now(),
            **customer_data
        )
        self.customers[customer.id] = customer
        return customer
    
    async def get_customer(self, customer_id: str) -> Optional[Customer]:
        """Get customer by ID."""
        return self.customers.get(customer_id)
    
    async def get_customers(
        self,
        department: Optional[str] = None,
        status: Optional[CustomerStatus] = None,
        limit: int = 100
    ) -> List[Customer]:
        """Get customers with filters."""
        customers = list(self.customers.values())
        
        if department:
            customers = [c for c in customers if c.department == department]
        
        if status:
            customers = [c for c in customers if c.status == status]
        
        return customers[:limit]
    
    async def update_customer(self, customer_id: str, updates: Dict[str, Any]) -> Optional[Customer]:
        """Update customer data."""
        if customer_id not in self.customers:
            return None
        
        customer = self.customers[customer_id]
        for key, value in updates.items():
            if hasattr(customer, key):
                setattr(customer, key, value)
        
        customer.updated_at = datetime.now()
        return customer
    
    async def delete_customer(self, customer_id: str) -> bool:
        """Delete a customer."""
        if customer_id in self.customers:
            del self.customers[customer_id]
            return True
        return False

    # Score operations
    async def create_score(self, score_data: Dict[str, Any]) -> CustomerScore:
        """Create a new customer score."""
        score = CustomerScore(
            id=str(uuid.uuid4()),
            created_at=datetime.now(),
            **score_data
        )
        self.scores[score.id] = score
        return score
    
    async def get_customer_scores(
        self,
        customer_id: str,
        score_type: Optional[ScoreType] = None,
        limit: int = 10
    ) -> List[CustomerScore]:
        """Get scores for a customer."""
        scores = [s for s in self.scores.values() if s.customer_id == customer_id]
        
        if score_type:
            scores = [s for s in scores if s.score_type == score_type]
        
        # Sort by creation date (newest first)
        scores.sort(key=lambda x: x.created_at, reverse=True)
        return scores[:limit]
    
    async def get_latest_score(self, customer_id: str, score_type: ScoreType) -> Optional[CustomerScore]:
        """Get the latest score for a customer and score type."""
        scores = await self.get_customer_scores(customer_id, score_type, limit=1)
        return scores[0] if scores else None

    # Conversation operations
    async def create_conversation_message(self, message_data: Dict[str, Any]) -> ConversationMessage:
        """Create a new conversation message."""
        message = ConversationMessage(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            **message_data
        )
        
        conversation_id = message.conversation_id
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []
        
        self.conversations[conversation_id].append(message)
        return message
    
    async def get_conversation(self, conversation_id: str) -> List[ConversationMessage]:
        """Get all messages in a conversation."""
        return self.conversations.get(conversation_id, [])
    
    async def get_customer_conversations(self, customer_id: str) -> List[ConversationMessage]:
        """Get all conversation messages for a customer."""
        messages = []
        for conversation in self.conversations.values():
            customer_messages = [m for m in conversation if m.customer_id == customer_id]
            messages.extend(customer_messages)
        
        # Sort by timestamp
        messages.sort(key=lambda x: x.timestamp, reverse=True)
        return messages

    # Knowledge base operations
    async def create_knowledge_document(self, doc_data: Dict[str, Any]) -> KnowledgeDocument:
        """Create a new knowledge document."""
        doc = KnowledgeDocument(
            id=str(uuid.uuid4()),
            created_at=datetime.now(),
            updated_at=datetime.now(),
            **doc_data
        )
        self.knowledge_docs[doc.id] = doc
        return doc
    
    async def get_knowledge_documents(
        self,
        document_type: Optional[str] = None,
        department: Optional[str] = None,
        limit: int = 50
    ) -> List[KnowledgeDocument]:
        """Get knowledge documents with filters."""
        docs = list(self.knowledge_docs.values())
        
        if document_type:
            docs = [d for d in docs if d.document_type == document_type]
        
        if department:
            docs = [d for d in docs if d.department == department]
        
        return docs[:limit]
    
    async def search_knowledge_documents(self, query: str, limit: int = 10) -> List[KnowledgeDocument]:
        """Search knowledge documents by content."""
        query = query.lower()
        matching_docs = []
        
        for doc in self.knowledge_docs.values():
            if (query in doc.title.lower() or 
                query in doc.content.lower() or
                any(query in tag.lower() for tag in doc.tags)):
                matching_docs.append(doc)
        
        return matching_docs[:limit]

    # Analytics operations
    async def get_customer_analytics(self, department: Optional[str] = None) -> Dict[str, Any]:
        """Get customer analytics data."""
        customers = await self.get_customers(department=department)
        total_customers = len(customers)
        
        # Count by status
        status_counts = {}
        for status in CustomerStatus:
            count = len([c for c in customers if c.status == status])
            status_counts[status.value] = count
        
        # Average scores
        scores = list(self.scores.values())
        if department:
            customer_ids = [c.id for c in customers]
            scores = [s for s in scores if s.customer_id in customer_ids]
        
        avg_score = sum(s.score for s in scores) / len(scores) if scores else 0
        avg_confidence = sum(s.confidence for s in scores) / len(scores) if scores else 0
        
        return {
            "total_customers": total_customers,
            "status_distribution": status_counts,
            "average_score": avg_score,
            "average_confidence": avg_confidence,
            "total_scores": len(scores),
            "last_updated": datetime.now()
        }


# ============================================================================
# Database Service (Legacy - now imports from production service)
# ============================================================================

# Import production database service
try:
    from ..database.service import DatabaseService as ProductionDatabaseService
    logger.info("Using production PostgreSQL database service")

    # Create a wrapper for backward compatibility
    class DatabaseService(ProductionDatabaseService):
        """Production database service wrapper for backward compatibility."""
        pass

except ImportError as e:
    logger.warning(f"Failed to import production database service: {e}")
    logger.info("Falling back to MockDatabase for development")

    class DatabaseService:
        """
        Fallback Database Service using MockDatabase.
        Used when PostgreSQL is not available.
        """

        _instance = None

        def __new__(cls):
            if cls._instance is None:
                cls._instance = super(DatabaseService, cls).__new__(cls)
                cls._instance._initialize()
            return cls._instance

        def _initialize(self):
            """Initialize database connection."""
            # Fallback to mock database
            self.db = MockDatabase()
            logger.info("Initialized DatabaseService with MockDatabase")

        async def health_check(self) -> Dict[str, Any]:
            """Check database health."""
            try:
                # Simple health check for MockDatabase fallback
                customers = await self.db.get_customers(limit=1)
                return {
                    "status": "healthy",
                    "database_type": "mock",
                    "customers_count": len(await self.db.get_customers()),
                    "scores_count": len(self.db.scores),
                    "conversations_count": len(self.db.conversations),
                    "knowledge_docs_count": len(self.db.knowledge_docs),
                    "timestamp": datetime.now()
                }
            except Exception as e:
                logger.error(f"Database health check failed: {e}")
                return {
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": datetime.now()
                }

        # Delegate all operations to the mock database
        async def create_customer(self, customer_data: Dict[str, Any]) -> Customer:
            return await self.db.create_customer(customer_data)

        async def get_customer(self, customer_id: str) -> Optional[Customer]:
            return await self.db.get_customer(customer_id)

        async def get_customers(self, **kwargs) -> List[Customer]:
            return await self.db.get_customers(**kwargs)

        async def update_customer(self, customer_id: str, updates: Dict[str, Any]) -> Optional[Customer]:
            return await self.db.update_customer(customer_id, updates)

        async def delete_customer(self, customer_id: str) -> bool:
            return await self.db.delete_customer(customer_id)

        async def create_score(self, score_data: Dict[str, Any]) -> CustomerScore:
            return await self.db.create_score(score_data)

        async def get_customer_scores(self, **kwargs) -> List[CustomerScore]:
            return await self.db.get_customer_scores(**kwargs)

        async def get_latest_score(self, customer_id: str, score_type: ScoreType) -> Optional[CustomerScore]:
            return await self.db.get_latest_score(customer_id, score_type)

        async def create_conversation_message(self, message_data: Dict[str, Any]) -> ConversationMessage:
            return await self.db.create_conversation_message(message_data)

        async def get_conversation(self, conversation_id: str) -> List[ConversationMessage]:
            return await self.db.get_conversation(conversation_id)

        async def get_customer_conversations(self, customer_id: str) -> List[ConversationMessage]:
            return await self.db.get_customer_conversations(customer_id)

        async def create_knowledge_document(self, doc_data: Dict[str, Any]) -> KnowledgeDocument:
            return await self.db.create_knowledge_document(doc_data)

        async def get_knowledge_documents(self, **kwargs) -> List[KnowledgeDocument]:
            return await self.db.get_knowledge_documents(**kwargs)

        async def search_knowledge_documents(self, query: str, limit: int = 10) -> List[KnowledgeDocument]:
            return await self.db.search_knowledge_documents(query, limit)

        async def get_customer_analytics(self, department: Optional[str] = None) -> Dict[str, Any]:
            return await self.db.get_customer_analytics(department)


# Global accessor
def get_database_service() -> DatabaseService:
    """Get the global database service instance."""
    return DatabaseService()


# Export main classes and functions
__all__ = [
    'DatabaseService', 'Customer', 'CustomerScore', 'ConversationMessage', 
    'KnowledgeDocument', 'CustomerStatus', 'ScoreType', 'ConversationRole',
    'get_database_service'
]