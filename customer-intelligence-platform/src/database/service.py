"""
Production Database Service for Customer Intelligence Platform.

Replaces MockDatabase with async PostgreSQL implementation while
maintaining the same interface for backward compatibility.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import UUID
import uuid

from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, create_async_engine
from sqlalchemy.orm import sessionmaker, selectinload
from sqlalchemy import select, func, text, and_, or_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from .models import (
    Customer as CustomerModel,
    CustomerScore as CustomerScoreModel,
    ConversationMessage as ConversationMessageModel,
    KnowledgeDocument as KnowledgeDocumentModel,
    Tenant,
    AuditLog,
    CustomerStatus,
    ScoreType,
    ConversationRole
)
from .schema import create_database_engine, health_check_database

# Import Pydantic models for backward compatibility
from ..utils.database_service import (
    Customer, CustomerScore, ConversationMessage, KnowledgeDocument
)

logger = logging.getLogger(__name__)

class TenantContext:
    """Thread-local tenant context for row-level security."""
    _tenant_id: Optional[str] = None

    @classmethod
    def set_tenant(cls, tenant_id: str) -> None:
        cls._tenant_id = tenant_id

    @classmethod
    def get_tenant(cls) -> Optional[str]:
        return cls._tenant_id

    @classmethod
    def clear(cls) -> None:
        cls._tenant_id = None

@asynccontextmanager
async def tenant_context(session: AsyncSession, tenant_id: str):
    """Set tenant context for row-level security."""
    try:
        # Set tenant context in PostgreSQL session
        await session.execute(text(f"SELECT set_current_tenant('{tenant_id}')"))
        TenantContext.set_tenant(tenant_id)
        yield
    finally:
        TenantContext.clear()

class PostgreSQLDatabase:
    """Production PostgreSQL database implementation."""

    def __init__(self, engine: AsyncEngine, default_tenant_id: str):
        self.engine = engine
        self.default_tenant_id = default_tenant_id
        self.session_factory = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        logger.info("Initialized PostgreSQLDatabase")

    async def get_session(self) -> AsyncSession:
        """Get database session with tenant context."""
        return self.session_factory()

    def _to_pydantic_customer(self, customer: CustomerModel) -> Customer:
        """Convert SQLAlchemy Customer to Pydantic Customer."""
        return Customer(
            id=str(customer.id),
            name=customer.name,
            email=customer.email,
            phone=customer.phone,
            company=customer.company,
            industry=customer.industry,
            department=customer.department,
            status=customer.status,
            created_at=customer.created_at,
            updated_at=customer.updated_at,
            last_interaction_at=customer.last_interaction_at,
            metadata=customer.metadata or {},
            tags=customer.tags or []
        )

    def _to_pydantic_score(self, score: CustomerScoreModel) -> CustomerScore:
        """Convert SQLAlchemy CustomerScore to Pydantic CustomerScore."""
        return CustomerScore(
            id=str(score.id),
            customer_id=str(score.customer_id),
            score_type=score.score_type,
            score=score.score,
            confidence=score.confidence,
            model_version=score.model_version,
            features=score.features,
            created_at=score.created_at
        )

    def _to_pydantic_message(self, message: ConversationMessageModel) -> ConversationMessage:
        """Convert SQLAlchemy ConversationMessage to Pydantic ConversationMessage."""
        return ConversationMessage(
            id=str(message.id),
            conversation_id=str(message.conversation_id),
            customer_id=str(message.customer_id),
            role=message.role,
            content=message.content,
            timestamp=message.timestamp,
            metadata=message.metadata or {}
        )

    def _to_pydantic_document(self, doc: KnowledgeDocumentModel) -> KnowledgeDocument:
        """Convert SQLAlchemy KnowledgeDocument to Pydantic KnowledgeDocument."""
        return KnowledgeDocument(
            id=str(doc.id),
            title=doc.title,
            content=doc.content,
            document_type=doc.document_type,
            department=doc.department,
            tags=doc.tags or [],
            created_at=doc.created_at,
            updated_at=doc.updated_at,
            metadata=doc.metadata or {}
        )

    async def _log_audit_event(
        self,
        session: AsyncSession,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log audit event for compliance."""
        try:
            audit_log = AuditLog(
                tenant_id=uuid.UUID(self.default_tenant_id),
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details
            )
            session.add(audit_log)
        except Exception as e:
            logger.warning(f"Audit logging failed: {e}")

    # Customer operations
    async def create_customer(self, customer_data: Dict[str, Any]) -> Customer:
        """Create a new customer."""
        async with self.get_session() as session:
            async with tenant_context(session, self.default_tenant_id):
                try:
                    customer = CustomerModel(
                        id=uuid.uuid4(),
                        tenant_id=uuid.UUID(self.default_tenant_id),
                        **customer_data
                    )
                    session.add(customer)

                    await self._log_audit_event(
                        session, "CREATE", "customer", str(customer.id), customer_data
                    )

                    await session.commit()
                    return self._to_pydantic_customer(customer)
                except IntegrityError as e:
                    await session.rollback()
                    logger.error(f"Customer creation failed: {e}")
                    raise
                except Exception as e:
                    await session.rollback()
                    logger.error(f"Unexpected error creating customer: {e}")
                    raise

    async def get_customer(self, customer_id: str) -> Optional[Customer]:
        """Get customer by ID."""
        async with self.get_session() as session:
            async with tenant_context(session, self.default_tenant_id):
                try:
                    result = await session.execute(
                        select(CustomerModel).where(CustomerModel.id == uuid.UUID(customer_id))
                    )
                    customer = result.scalar_one_or_none()
                    return self._to_pydantic_customer(customer) if customer else None
                except Exception as e:
                    logger.error(f"Error fetching customer {customer_id}: {e}")
                    return None

    async def get_customers(
        self,
        department: Optional[str] = None,
        status: Optional[CustomerStatus] = None,
        limit: int = 100
    ) -> List[Customer]:
        """Get customers with filters."""
        async with self.get_session() as session:
            async with tenant_context(session, self.default_tenant_id):
                try:
                    query = select(CustomerModel)

                    if department:
                        query = query.where(CustomerModel.department == department)

                    if status:
                        query = query.where(CustomerModel.status == status)

                    query = query.limit(limit).order_by(CustomerModel.created_at.desc())

                    result = await session.execute(query)
                    customers = result.scalars().all()
                    return [self._to_pydantic_customer(c) for c in customers]
                except Exception as e:
                    logger.error(f"Error fetching customers: {e}")
                    return []

    async def update_customer(self, customer_id: str, updates: Dict[str, Any]) -> Optional[Customer]:
        """Update customer data."""
        async with self.get_session() as session:
            async with tenant_context(session, self.default_tenant_id):
                try:
                    result = await session.execute(
                        select(CustomerModel).where(CustomerModel.id == uuid.UUID(customer_id))
                    )
                    customer = result.scalar_one_or_none()

                    if not customer:
                        return None

                    # Update fields
                    for key, value in updates.items():
                        if hasattr(customer, key):
                            setattr(customer, key, value)

                    customer.updated_at = datetime.utcnow()

                    await self._log_audit_event(
                        session, "UPDATE", "customer", customer_id, updates
                    )

                    await session.commit()
                    return self._to_pydantic_customer(customer)
                except Exception as e:
                    await session.rollback()
                    logger.error(f"Error updating customer {customer_id}: {e}")
                    return None

    async def delete_customer(self, customer_id: str) -> bool:
        """Delete a customer."""
        async with self.get_session() as session:
            async with tenant_context(session, self.default_tenant_id):
                try:
                    result = await session.execute(
                        select(CustomerModel).where(CustomerModel.id == uuid.UUID(customer_id))
                    )
                    customer = result.scalar_one_or_none()

                    if not customer:
                        return False

                    await self._log_audit_event(
                        session, "DELETE", "customer", customer_id
                    )

                    await session.delete(customer)
                    await session.commit()
                    return True
                except Exception as e:
                    await session.rollback()
                    logger.error(f"Error deleting customer {customer_id}: {e}")
                    return False

    # Score operations
    async def create_score(self, score_data: Dict[str, Any]) -> CustomerScore:
        """Create a new customer score."""
        async with self.get_session() as session:
            async with tenant_context(session, self.default_tenant_id):
                try:
                    score = CustomerScoreModel(
                        id=uuid.uuid4(),
                        tenant_id=uuid.UUID(self.default_tenant_id),
                        customer_id=uuid.UUID(score_data['customer_id']),
                        **{k: v for k, v in score_data.items() if k != 'customer_id'}
                    )
                    session.add(score)

                    await self._log_audit_event(
                        session, "CREATE", "customer_score", str(score.id), score_data
                    )

                    await session.commit()
                    return self._to_pydantic_score(score)
                except Exception as e:
                    await session.rollback()
                    logger.error(f"Error creating score: {e}")
                    raise

    async def get_customer_scores(
        self,
        customer_id: str,
        score_type: Optional[ScoreType] = None,
        limit: int = 10
    ) -> List[CustomerScore]:
        """Get scores for a customer."""
        async with self.get_session() as session:
            async with tenant_context(session, self.default_tenant_id):
                try:
                    query = select(CustomerScoreModel).where(
                        CustomerScoreModel.customer_id == uuid.UUID(customer_id)
                    )

                    if score_type:
                        query = query.where(CustomerScoreModel.score_type == score_type)

                    query = query.order_by(CustomerScoreModel.created_at.desc()).limit(limit)

                    result = await session.execute(query)
                    scores = result.scalars().all()
                    return [self._to_pydantic_score(s) for s in scores]
                except Exception as e:
                    logger.error(f"Error fetching customer scores: {e}")
                    return []

    async def get_latest_score(self, customer_id: str, score_type: ScoreType) -> Optional[CustomerScore]:
        """Get the latest score for a customer and score type."""
        scores = await self.get_customer_scores(customer_id, score_type, limit=1)
        return scores[0] if scores else None

    # Conversation operations
    async def create_conversation_message(self, message_data: Dict[str, Any]) -> ConversationMessage:
        """Create a new conversation message."""
        async with self.get_session() as session:
            async with tenant_context(session, self.default_tenant_id):
                try:
                    message = ConversationMessageModel(
                        id=uuid.uuid4(),
                        tenant_id=uuid.UUID(self.default_tenant_id),
                        customer_id=uuid.UUID(message_data['customer_id']),
                        conversation_id=uuid.UUID(message_data['conversation_id']),
                        **{k: v for k, v in message_data.items() if k not in ['customer_id', 'conversation_id']}
                    )
                    session.add(message)
                    await session.commit()
                    return self._to_pydantic_message(message)
                except Exception as e:
                    await session.rollback()
                    logger.error(f"Error creating conversation message: {e}")
                    raise

    async def get_conversation(self, conversation_id: str) -> List[ConversationMessage]:
        """Get all messages in a conversation."""
        async with self.get_session() as session:
            async with tenant_context(session, self.default_tenant_id):
                try:
                    result = await session.execute(
                        select(ConversationMessageModel)
                        .where(ConversationMessageModel.conversation_id == uuid.UUID(conversation_id))
                        .order_by(ConversationMessageModel.timestamp.asc())
                    )
                    messages = result.scalars().all()
                    return [self._to_pydantic_message(m) for m in messages]
                except Exception as e:
                    logger.error(f"Error fetching conversation: {e}")
                    return []

    async def get_customer_conversations(self, customer_id: str) -> List[ConversationMessage]:
        """Get all conversation messages for a customer."""
        async with self.get_session() as session:
            async with tenant_context(session, self.default_tenant_id):
                try:
                    result = await session.execute(
                        select(ConversationMessageModel)
                        .where(ConversationMessageModel.customer_id == uuid.UUID(customer_id))
                        .order_by(ConversationMessageModel.timestamp.desc())
                    )
                    messages = result.scalars().all()
                    return [self._to_pydantic_message(m) for m in messages]
                except Exception as e:
                    logger.error(f"Error fetching customer conversations: {e}")
                    return []

    # Knowledge base operations
    async def create_knowledge_document(self, doc_data: Dict[str, Any]) -> KnowledgeDocument:
        """Create a new knowledge document."""
        async with self.get_session() as session:
            async with tenant_context(session, self.default_tenant_id):
                try:
                    doc = KnowledgeDocumentModel(
                        id=uuid.uuid4(),
                        tenant_id=uuid.UUID(self.default_tenant_id),
                        **doc_data
                    )
                    session.add(doc)
                    await session.commit()
                    return self._to_pydantic_document(doc)
                except Exception as e:
                    await session.rollback()
                    logger.error(f"Error creating knowledge document: {e}")
                    raise

    async def get_knowledge_documents(
        self,
        document_type: Optional[str] = None,
        department: Optional[str] = None,
        limit: int = 50
    ) -> List[KnowledgeDocument]:
        """Get knowledge documents with filters."""
        async with self.get_session() as session:
            async with tenant_context(session, self.default_tenant_id):
                try:
                    query = select(KnowledgeDocumentModel)

                    if document_type:
                        query = query.where(KnowledgeDocumentModel.document_type == document_type)

                    if department:
                        query = query.where(KnowledgeDocumentModel.department == department)

                    query = query.limit(limit).order_by(KnowledgeDocumentModel.created_at.desc())

                    result = await session.execute(query)
                    docs = result.scalars().all()
                    return [self._to_pydantic_document(d) for d in docs]
                except Exception as e:
                    logger.error(f"Error fetching knowledge documents: {e}")
                    return []

    async def search_knowledge_documents(self, query: str, limit: int = 10) -> List[KnowledgeDocument]:
        """Search knowledge documents by content."""
        async with self.get_session() as session:
            async with tenant_context(session, self.default_tenant_id):
                try:
                    # Use PostgreSQL full-text search
                    search_query = select(KnowledgeDocumentModel).where(
                        or_(
                            func.to_tsvector('english', KnowledgeDocumentModel.title).match(query),
                            func.to_tsvector('english', KnowledgeDocumentModel.content).match(query),
                            KnowledgeDocumentModel.tags.any(func.lower(query))
                        )
                    ).limit(limit)

                    result = await session.execute(search_query)
                    docs = result.scalars().all()
                    return [self._to_pydantic_document(d) for d in docs]
                except Exception as e:
                    logger.error(f"Error searching knowledge documents: {e}")
                    # Fallback to simple text search
                    query_lower = query.lower()
                    all_docs = await self.get_knowledge_documents(limit=100)
                    matching_docs = [
                        doc for doc in all_docs
                        if (query_lower in doc.title.lower() or
                            query_lower in doc.content.lower() or
                            any(query_lower in tag.lower() for tag in doc.tags))
                    ]
                    return matching_docs[:limit]

    # Analytics operations
    async def get_customer_analytics(self, department: Optional[str] = None) -> Dict[str, Any]:
        """Get customer analytics data."""
        async with self.get_session() as session:
            async with tenant_context(session, self.default_tenant_id):
                try:
                    # Base customer query
                    customer_query = select(CustomerModel)
                    if department:
                        customer_query = customer_query.where(CustomerModel.department == department)

                    result = await session.execute(customer_query)
                    customers = result.scalars().all()
                    total_customers = len(customers)

                    # Count by status
                    status_counts = {}
                    for status in CustomerStatus:
                        count = len([c for c in customers if c.status == status])
                        status_counts[status.value] = count

                    # Score statistics
                    score_query = select(CustomerScoreModel)
                    if department:
                        customer_ids = [c.id for c in customers]
                        score_query = score_query.where(CustomerScoreModel.customer_id.in_(customer_ids))

                    result = await session.execute(score_query)
                    scores = result.scalars().all()

                    avg_score = sum(s.score for s in scores) / len(scores) if scores else 0
                    avg_confidence = sum(s.confidence for s in scores) / len(scores) if scores else 0

                    return {
                        "total_customers": total_customers,
                        "status_distribution": status_counts,
                        "average_score": avg_score,
                        "average_confidence": avg_confidence,
                        "total_scores": len(scores),
                        "last_updated": datetime.utcnow()
                    }
                except Exception as e:
                    logger.error(f"Error fetching analytics: {e}")
                    return {
                        "total_customers": 0,
                        "status_distribution": {},
                        "average_score": 0,
                        "average_confidence": 0,
                        "total_scores": 0,
                        "last_updated": datetime.utcnow()
                    }

class DatabaseService:
    """
    Production Database Service for Customer Intelligence Platform.
    Replaces MockDatabase with PostgreSQL while maintaining the same interface.
    """

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseService, cls).__new__(cls)
        return cls._instance

    async def _initialize(self):
        """Initialize PostgreSQL connection."""
        if self._initialized:
            return

        try:
            from .schema import init_database

            # Create engine and initialize database
            self.engine = await create_database_engine()

            # Initialize database schema and get default tenant
            self.default_tenant_id = await init_database(self.engine)

            # Initialize PostgreSQL database
            self.db = PostgreSQLDatabase(self.engine, self.default_tenant_id)

            self._initialized = True
            logger.info("Initialized DatabaseService with PostgreSQL")

        except Exception as e:
            logger.error(f"Failed to initialize DatabaseService: {e}")
            # Fallback to MockDatabase for development
            from ..utils.database_service import MockDatabase
            self.db = MockDatabase()
            logger.warning("Fallback to MockDatabase due to PostgreSQL initialization failure")

    async def health_check(self) -> Dict[str, Any]:
        """Check database health."""
        if not self._initialized:
            await self._initialize()

        if hasattr(self, 'engine'):
            return await health_check_database(self.engine)
        else:
            # Fallback health check for MockDatabase
            try:
                customers = await self.db.get_customers(limit=1)
                return {
                    "status": "healthy",
                    "database_type": "mock",
                    "customers_count": len(await self.db.get_customers()),
                    "timestamp": datetime.utcnow()
                }
            except Exception as e:
                return {
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": datetime.utcnow()
                }

    # Delegate all operations to the database implementation
    async def create_customer(self, customer_data: Dict[str, Any]) -> Customer:
        if not self._initialized:
            await self._initialize()
        return await self.db.create_customer(customer_data)

    async def get_customer(self, customer_id: str) -> Optional[Customer]:
        if not self._initialized:
            await self._initialize()
        return await self.db.get_customer(customer_id)

    async def get_customers(self, **kwargs) -> List[Customer]:
        if not self._initialized:
            await self._initialize()
        return await self.db.get_customers(**kwargs)

    async def update_customer(self, customer_id: str, updates: Dict[str, Any]) -> Optional[Customer]:
        if not self._initialized:
            await self._initialize()
        return await self.db.update_customer(customer_id, updates)

    async def delete_customer(self, customer_id: str) -> bool:
        if not self._initialized:
            await self._initialize()
        return await self.db.delete_customer(customer_id)

    async def create_score(self, score_data: Dict[str, Any]) -> CustomerScore:
        if not self._initialized:
            await self._initialize()
        return await self.db.create_score(score_data)

    async def get_customer_scores(self, **kwargs) -> List[CustomerScore]:
        if not self._initialized:
            await self._initialize()
        return await self.db.get_customer_scores(**kwargs)

    async def get_latest_score(self, customer_id: str, score_type: ScoreType) -> Optional[CustomerScore]:
        if not self._initialized:
            await self._initialize()
        return await self.db.get_latest_score(customer_id, score_type)

    async def create_conversation_message(self, message_data: Dict[str, Any]) -> ConversationMessage:
        if not self._initialized:
            await self._initialize()
        return await self.db.create_conversation_message(message_data)

    async def get_conversation(self, conversation_id: str) -> List[ConversationMessage]:
        if not self._initialized:
            await self._initialize()
        return await self.db.get_conversation(conversation_id)

    async def get_customer_conversations(self, customer_id: str) -> List[ConversationMessage]:
        if not self._initialized:
            await self._initialize()
        return await self.db.get_customer_conversations(customer_id)

    async def create_knowledge_document(self, doc_data: Dict[str, Any]) -> KnowledgeDocument:
        if not self._initialized:
            await self._initialize()
        return await self.db.create_knowledge_document(doc_data)

    async def get_knowledge_documents(self, **kwargs) -> List[KnowledgeDocument]:
        if not self._initialized:
            await self._initialize()
        return await self.db.get_knowledge_documents(**kwargs)

    async def search_knowledge_documents(self, query: str, limit: int = 10) -> List[KnowledgeDocument]:
        if not self._initialized:
            await self._initialize()
        return await self.db.search_knowledge_documents(query, limit)

    async def get_customer_analytics(self, department: Optional[str] = None) -> Dict[str, Any]:
        if not self._initialized:
            await self._initialize()
        return await self.db.get_customer_analytics(department)

# Global accessor (maintains backward compatibility)
def get_database_service() -> DatabaseService:
    """Get the global database service instance."""
    return DatabaseService()