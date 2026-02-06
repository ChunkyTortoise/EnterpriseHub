"""
Human Review Queue Management

Priority-based review queue with SLA tracking, load balancing, and escalation
management for enterprise document processing workflows.

Features:
- Priority-based assignment (Critical, High, Medium, Low)
- Role-based routing (Partner, Associate, Paralegal)
- SLA tracking with automated escalation
- Load balancing across reviewers
- Performance metrics and feedback loops
"""

import asyncio
import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple, Set, Any, Union
import statistics
import heapq
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from .database_schema import (
    DocumentVersion, ReviewAssignment, QualityMetrics, AuditTrail,
    ProcessingStatus, ReviewPriority, AuditEventType
)

# Import EnterpriseHub patterns
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from ghl_real_estate_ai.services.cache_service import CacheService
from ghl_real_estate_ai.security.audit_logger import AuditLogger

logger = logging.getLogger(__name__)

class ReviewerRole(Enum):
    """Legal reviewer roles with different capabilities and authority."""
    PARALEGAL = "paralegal"
    ASSOCIATE = "associate" 
    PARTNER = "partner"
    SENIOR_PARTNER = "senior_partner"

class ReviewType(Enum):
    """Types of review required based on document complexity and confidence."""
    SPOT_CHECK = "spot_check"         # Random quality check
    QUALITY_REVIEW = "quality_review" # Focused validation
    FULL_REVIEW = "full_review"       # Comprehensive analysis
    TECHNICAL_REVIEW = "technical_review"  # Specialist expertise
    COMPLIANCE_REVIEW = "compliance_review" # Regulatory compliance

class ReviewStatus(Enum):
    """Current status of review assignment."""
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ESCALATED = "escalated"
    CANCELLED = "cancelled"
    OVERDUE = "overdue"

class EscalationReason(Enum):
    """Reasons for escalating review to higher authority."""
    SLA_BREACH = "sla_breach"
    COMPLEXITY = "complexity"
    REVIEWER_REQUEST = "reviewer_request"
    QUALITY_CONCERNS = "quality_concerns"
    CLIENT_REQUEST = "client_request"
    COMPLIANCE_ISSUE = "compliance_issue"

@dataclass
class ReviewerCapacity:
    """Reviewer capacity and workload tracking."""
    reviewer_id: str
    role: ReviewerRole
    max_concurrent_reviews: int = 10
    current_workload: int = 0
    average_review_time_hours: float = 2.0
    specializations: Set[str] = field(default_factory=set)
    
    # Performance metrics
    completion_rate: float = 0.95  # % of reviews completed on time
    quality_score: float = 0.9    # Quality of review feedback
    throughput_per_day: float = 8.0  # Reviews completed per day
    
    # Availability
    is_available: bool = True
    next_available_slot: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def capacity_utilization(self) -> float:
        """Calculate current capacity utilization percentage."""
        return (self.current_workload / self.max_concurrent_reviews) * 100
    
    @property
    def estimated_availability(self) -> datetime:
        """Estimate when reviewer will be available for new assignments."""
        if self.current_workload < self.max_concurrent_reviews:
            return datetime.utcnow()
        
        # Estimate based on average review time
        reviews_to_complete = self.current_workload - self.max_concurrent_reviews + 1
        hours_until_available = reviews_to_complete * self.average_review_time_hours
        return datetime.utcnow() + timedelta(hours=hours_until_available)

@dataclass
class ReviewMetrics:
    """Performance metrics for review queue monitoring."""
    total_assigned: int = 0
    total_completed: int = 0
    total_overdue: int = 0
    total_escalated: int = 0
    
    # SLA metrics
    sla_compliance_rate: float = 0.0
    average_completion_time_hours: float = 0.0
    
    # Queue depth by priority
    critical_queue_depth: int = 0
    high_queue_depth: int = 0
    medium_queue_depth: int = 0
    low_queue_depth: int = 0
    
    # Workload distribution
    reviewer_utilization: Dict[str, float] = field(default_factory=dict)
    
    @property
    def total_queue_depth(self) -> int:
        """Total documents waiting for review."""
        return (self.critical_queue_depth + self.high_queue_depth + 
                self.medium_queue_depth + self.low_queue_depth)

class PriorityQueue:
    """Priority queue implementation for review assignments."""
    
    def __init__(self):
        self._heap = []
        self._index = 0
    
    def push(self, item: Tuple[ReviewPriority, datetime, str], doc_version_id: str):
        """Push item to priority queue with timestamp tie-breaking."""
        priority_value = self._priority_to_value(item[0])
        timestamp = item[1]
        
        # Use negative timestamp for FIFO within same priority
        heapq.heappush(self._heap, (priority_value, -timestamp.timestamp(), self._index, doc_version_id))
        self._index += 1
    
    def pop(self) -> Optional[str]:
        """Pop highest priority item from queue."""
        if not self._heap:
            return None
        
        _, _, _, doc_version_id = heapq.heappop(self._heap)
        return doc_version_id
    
    def peek(self) -> Optional[str]:
        """Peek at highest priority item without removing."""
        if not self._heap:
            return None
        return self._heap[0][3]
    
    def size(self) -> int:
        """Get queue size."""
        return len(self._heap)
    
    def _priority_to_value(self, priority: ReviewPriority) -> int:
        """Convert priority enum to numeric value for heapq (lower = higher priority)."""
        priority_values = {
            ReviewPriority.CRITICAL: 0,
            ReviewPriority.HIGH: 1,
            ReviewPriority.MEDIUM: 2,
            ReviewPriority.LOW: 3
        }
        return priority_values.get(priority, 3)

class HumanReviewQueue:
    """
    Enterprise-scale human review queue with intelligent assignment and SLA management.
    
    Features:
    - Priority-based assignment with role-based routing
    - SLA tracking with automated escalation
    - Load balancing across reviewers
    - Reviewer capacity and performance tracking
    - Quality feedback loops
    - Real-time metrics and monitoring
    """
    
    def __init__(self, db_session: Session, cache_service: CacheService = None):
        """Initialize human review queue management system."""
        
        self.db_session = db_session
        self.cache_service = cache_service or CacheService()
        self.audit_logger = AuditLogger()
        
        # Review queues by priority
        self.priority_queues = {
            ReviewPriority.CRITICAL: PriorityQueue(),
            ReviewPriority.HIGH: PriorityQueue(),
            ReviewPriority.MEDIUM: PriorityQueue(),
            ReviewPriority.LOW: PriorityQueue()
        }
        
        # Reviewer management
        self.reviewers: Dict[str, ReviewerCapacity] = {}
        self.role_queues: Dict[ReviewerRole, List[str]] = defaultdict(list)
        
        # SLA configuration (in hours)
        self.sla_targets = {
            ReviewPriority.CRITICAL: 2.0,    # 2 hours
            ReviewPriority.HIGH: 8.0,        # 8 hours  
            ReviewPriority.MEDIUM: 24.0,     # 24 hours
            ReviewPriority.LOW: 72.0         # 72 hours
        }
        
        # Assignment strategy configuration
        self.assignment_strategy = "load_balanced"  # Options: "round_robin", "load_balanced", "expertise_based"
        self.max_retries = 3
        
        # Performance tracking
        self.metrics = ReviewMetrics()
        self._last_metrics_update = datetime.utcnow()
        
        # Background tasks
        self._monitoring_active = False
        
        logger.info("HumanReviewQueue initialized")
    
    async def initialize_reviewers(self, reviewer_configs: List[Dict[str, Any]]):
        """Initialize reviewer capacity and configuration."""
        
        for config in reviewer_configs:
            reviewer_id = config["reviewer_id"]
            role = ReviewerRole(config["role"])
            
            capacity = ReviewerCapacity(
                reviewer_id=reviewer_id,
                role=role,
                max_concurrent_reviews=config.get("max_concurrent", 10),
                average_review_time_hours=config.get("avg_review_time", 2.0),
                specializations=set(config.get("specializations", [])),
                completion_rate=config.get("completion_rate", 0.95),
                quality_score=config.get("quality_score", 0.9),
                is_available=config.get("is_available", True)
            )
            
            self.reviewers[reviewer_id] = capacity
            self.role_queues[role].append(reviewer_id)
        
        logger.info(f"Initialized {len(self.reviewers)} reviewers across {len(self.role_queues)} roles")
    
    async def assign_document_for_review(
        self,
        doc_version: DocumentVersion,
        priority: ReviewPriority,
        review_type: ReviewType = ReviewType.QUALITY_REVIEW,
        required_role: ReviewerRole = None,
        due_date: datetime = None,
        client_preferences: Dict[str, Any] = None
    ) -> str:
        """
        Assign document for human review with intelligent reviewer selection.
        
        Args:
            doc_version: Document version to review
            priority: Review priority level
            review_type: Type of review required
            required_role: Specific reviewer role if needed
            due_date: Custom due date (overrides SLA default)
            client_preferences: Client-specific reviewer preferences
            
        Returns:
            assignment_id: Unique review assignment identifier
        """
        
        assignment_id = str(uuid.uuid4())
        current_time = datetime.utcnow()
        
        # Calculate due date based on SLA or custom requirement
        if not due_date:
            sla_hours = self.sla_targets.get(priority, 24.0)
            due_date = current_time + timedelta(hours=sla_hours)
        
        try:
            # Determine required reviewer role based on document and review type
            if not required_role:
                required_role = self._determine_required_role(doc_version, review_type, priority)
            
            # Select optimal reviewer
            assigned_reviewer = await self._select_optimal_reviewer(
                required_role, review_type, priority, client_preferences, doc_version
            )
            
            if not assigned_reviewer:
                # No available reviewer - add to queue
                await self._add_to_priority_queue(doc_version.id, priority, current_time)
                
                logger.warning(
                    f"No available reviewer for {doc_version.id} - added to {priority.value} queue"
                )
                return None
            
            # Create review assignment
            assignment = ReviewAssignment(
                id=assignment_id,
                document_version_id=doc_version.id,
                assigned_reviewer_id=assigned_reviewer.reviewer_id,
                reviewer_role=assigned_reviewer.role.value,
                priority=priority,
                status=ReviewStatus.ASSIGNED.value,
                review_type=review_type.value,
                assigned_at=current_time,
                due_date=due_date,
                estimated_duration_hours=assigned_reviewer.average_review_time_hours
            )
            
            self.db_session.add(assignment)
            
            # Update document status
            doc_version.processing_status = ProcessingStatus.HUMAN_REVIEW
            
            # Update reviewer workload
            assigned_reviewer.current_workload += 1
            
            # Commit database changes
            self.db_session.commit()
            
            # Audit log assignment
            await self.audit_logger.log_event(
                event_type=AuditEventType.REVIEW_ASSIGNED,
                event_description=f"Document assigned for {review_type.value} review",
                document_version_id=doc_version.id,
                user_id=assigned_reviewer.reviewer_id,
                event_data={
                    "assignment_id": assignment_id,
                    "priority": priority.value,
                    "review_type": review_type.value,
                    "due_date": due_date.isoformat(),
                    "reviewer_role": assigned_reviewer.role.value
                }
            )
            
            logger.info(
                f"Assigned document {doc_version.id} to reviewer {assigned_reviewer.reviewer_id} "
                f"({assigned_reviewer.role.value}) with priority {priority.value}"
            )
            
            return assignment_id
            
        except Exception as e:
            logger.error(f"Failed to assign document {doc_version.id} for review: {e}")
            self.db_session.rollback()
            raise
    
    async def _add_to_priority_queue(self, doc_version_id: str, priority: ReviewPriority, timestamp: datetime):
        """Add document to priority queue when no reviewers are available."""
        
        queue = self.priority_queues[priority]
        queue.push((priority, timestamp, doc_version_id), doc_version_id)
        
        # Update metrics
        self._update_queue_metrics()
        
        # Alert on critical queue buildup
        if priority == ReviewPriority.CRITICAL and queue.size() > 5:
            await self._alert_critical_queue_buildup()
    
    def _determine_required_role(
        self,
        doc_version: DocumentVersion,
        review_type: ReviewType,
        priority: ReviewPriority
    ) -> ReviewerRole:
        """Determine minimum reviewer role required based on document complexity."""
        
        # Role requirements based on review type and priority
        role_matrix = {
            ReviewType.SPOT_CHECK: {
                ReviewPriority.CRITICAL: ReviewerRole.ASSOCIATE,
                ReviewPriority.HIGH: ReviewerRole.PARALEGAL,
                ReviewPriority.MEDIUM: ReviewerRole.PARALEGAL,
                ReviewPriority.LOW: ReviewerRole.PARALEGAL
            },
            ReviewType.QUALITY_REVIEW: {
                ReviewPriority.CRITICAL: ReviewerRole.ASSOCIATE,
                ReviewPriority.HIGH: ReviewerRole.ASSOCIATE,
                ReviewPriority.MEDIUM: ReviewerRole.PARALEGAL,
                ReviewPriority.LOW: ReviewerRole.PARALEGAL
            },
            ReviewType.FULL_REVIEW: {
                ReviewPriority.CRITICAL: ReviewerRole.PARTNER,
                ReviewPriority.HIGH: ReviewerRole.ASSOCIATE,
                ReviewPriority.MEDIUM: ReviewerRole.ASSOCIATE,
                ReviewPriority.LOW: ReviewerRole.ASSOCIATE
            },
            ReviewType.TECHNICAL_REVIEW: {
                ReviewPriority.CRITICAL: ReviewerRole.SENIOR_PARTNER,
                ReviewPriority.HIGH: ReviewerRole.PARTNER,
                ReviewPriority.MEDIUM: ReviewerRole.PARTNER,
                ReviewPriority.LOW: ReviewerRole.ASSOCIATE
            },
            ReviewType.COMPLIANCE_REVIEW: {
                ReviewPriority.CRITICAL: ReviewerRole.PARTNER,
                ReviewPriority.HIGH: ReviewerRole.PARTNER,
                ReviewPriority.MEDIUM: ReviewerRole.ASSOCIATE,
                ReviewPriority.LOW: ReviewerRole.ASSOCIATE
            }
        }
        
        base_role = role_matrix.get(review_type, {}).get(priority, ReviewerRole.ASSOCIATE)
        
        # Adjust based on document complexity factors
        complexity_factors = 0
        
        if doc_version.overall_confidence and doc_version.overall_confidence < 0.6:
            complexity_factors += 1  # Low confidence requires higher role
        
        if hasattr(doc_version, 'file_size_bytes') and doc_version.file_size_bytes > 10000000:  # >10MB
            complexity_factors += 1  # Large document
        
        # Check for high-risk flags in processing results
        if doc_version.risk_assessment:
            risk_data = doc_version.risk_assessment
            if isinstance(risk_data, dict) and risk_data.get('high_risk_flags'):
                complexity_factors += 1
        
        # Escalate role based on complexity
        role_hierarchy = [ReviewerRole.PARALEGAL, ReviewerRole.ASSOCIATE, ReviewerRole.PARTNER, ReviewerRole.SENIOR_PARTNER]
        base_index = role_hierarchy.index(base_role)
        adjusted_index = min(len(role_hierarchy) - 1, base_index + complexity_factors)
        
        return role_hierarchy[adjusted_index]
    
    async def _select_optimal_reviewer(
        self,
        required_role: ReviewerRole,
        review_type: ReviewType,
        priority: ReviewPriority,
        client_preferences: Dict[str, Any] = None,
        doc_version: DocumentVersion = None
    ) -> Optional[ReviewerCapacity]:
        """Select optimal reviewer using configured assignment strategy."""
        
        # Get eligible reviewers for role
        role_hierarchy = [ReviewerRole.PARALEGAL, ReviewerRole.ASSOCIATE, ReviewerRole.PARTNER, ReviewerRole.SENIOR_PARTNER]
        min_role_index = role_hierarchy.index(required_role)
        
        eligible_reviewers = []
        for role in role_hierarchy[min_role_index:]:  # Include higher roles
            for reviewer_id in self.role_queues.get(role, []):
                reviewer = self.reviewers.get(reviewer_id)
                if reviewer and reviewer.is_available and reviewer.current_workload < reviewer.max_concurrent_reviews:
                    eligible_reviewers.append(reviewer)
        
        if not eligible_reviewers:
            return None
        
        # Apply assignment strategy
        if self.assignment_strategy == "load_balanced":
            return self._select_load_balanced_reviewer(eligible_reviewers)
        elif self.assignment_strategy == "expertise_based":
            return self._select_expertise_based_reviewer(eligible_reviewers, doc_version)
        else:  # round_robin
            return self._select_round_robin_reviewer(eligible_reviewers)
    
    def _select_load_balanced_reviewer(self, eligible_reviewers: List[ReviewerCapacity]) -> ReviewerCapacity:
        """Select reviewer with lowest current utilization."""
        return min(eligible_reviewers, key=lambda r: r.capacity_utilization)
    
    def _select_expertise_based_reviewer(
        self,
        eligible_reviewers: List[ReviewerCapacity],
        doc_version: DocumentVersion
    ) -> ReviewerCapacity:
        """Select reviewer based on expertise match and workload."""
        
        # Determine document specialization needs
        doc_specializations = set()
        
        if doc_version.legal_analysis:
            legal_data = doc_version.legal_analysis
            if isinstance(legal_data, dict):
                contract_type = legal_data.get('contract_type', '').lower()
                if 'employment' in contract_type:
                    doc_specializations.add('employment_law')
                elif 'real_estate' in contract_type or 'lease' in contract_type:
                    doc_specializations.add('real_estate')
                elif 'ip' in contract_type or 'intellectual' in contract_type:
                    doc_specializations.add('intellectual_property')
        
        # Score reviewers based on expertise match and capacity
        scored_reviewers = []
        for reviewer in eligible_reviewers:
            expertise_match = len(reviewer.specializations.intersection(doc_specializations))
            capacity_score = 1.0 - reviewer.capacity_utilization / 100  # Higher capacity = higher score
            quality_score = reviewer.quality_score
            
            # Weighted scoring: expertise (40%), capacity (30%), quality (30%)
            total_score = (expertise_match * 0.4) + (capacity_score * 0.3) + (quality_score * 0.3)
            scored_reviewers.append((total_score, reviewer))
        
        # Return highest scoring reviewer
        return max(scored_reviewers, key=lambda x: x[0])[1]
    
    def _select_round_robin_reviewer(self, eligible_reviewers: List[ReviewerCapacity]) -> ReviewerCapacity:
        """Select reviewer using round-robin assignment."""
        # Simple implementation - could be enhanced with persistent state
        return min(eligible_reviewers, key=lambda r: r.current_workload)
    
    async def complete_review(
        self,
        assignment_id: str,
        reviewer_id: str,
        approved: bool,
        review_notes: str = "",
        confidence_score: float = None,
        time_spent_hours: float = None,
        quality_feedback: Dict[str, Any] = None
    ) -> bool:
        """
        Mark review assignment as completed with feedback.
        
        Args:
            assignment_id: Review assignment ID
            reviewer_id: ID of reviewer completing the review
            approved: Whether document is approved
            review_notes: Reviewer comments and observations
            confidence_score: Reviewer's confidence in their assessment
            time_spent_hours: Actual time spent on review
            quality_feedback: Feedback on AI processing quality
            
        Returns:
            success: Whether completion was processed successfully
        """
        
        try:
            # Get assignment record
            assignment = self.db_session.query(ReviewAssignment).filter(
                ReviewAssignment.id == assignment_id
            ).first()
            
            if not assignment:
                logger.error(f"Review assignment {assignment_id} not found")
                return False
            
            if assignment.assigned_reviewer_id != reviewer_id:
                logger.error(f"Reviewer {reviewer_id} not authorized for assignment {assignment_id}")
                return False
            
            # Update assignment record
            completion_time = datetime.utcnow()
            assignment.status = ReviewStatus.COMPLETED.value
            assignment.completed_at = completion_time
            assignment.approved = approved
            assignment.review_notes = review_notes
            assignment.reviewer_confidence = confidence_score
            assignment.actual_duration_hours = time_spent_hours or assignment.estimated_duration_hours
            
            # Check SLA compliance
            if assignment.due_date and completion_time <= assignment.due_date:
                assignment.sla_met = True
            else:
                assignment.sla_met = False
                logger.warning(f"SLA breach for assignment {assignment_id}")
            
            # Update document status
            doc_version = self.db_session.query(DocumentVersion).filter(
                DocumentVersion.id == assignment.document_version_id
            ).first()
            
            if doc_version:
                if approved:
                    doc_version.processing_status = ProcessingStatus.APPROVED
                else:
                    doc_version.processing_status = ProcessingStatus.REJECTED
            
            # Update reviewer workload
            reviewer = self.reviewers.get(reviewer_id)
            if reviewer:
                reviewer.current_workload = max(0, reviewer.current_workload - 1)
                
                # Update performance metrics
                if time_spent_hours:
                    # Update running average (simple exponential smoothing)
                    alpha = 0.1  # Smoothing factor
                    reviewer.average_review_time_hours = (
                        alpha * time_spent_hours + 
                        (1 - alpha) * reviewer.average_review_time_hours
                    )
                
                # Update quality score if feedback provided
                if quality_feedback and 'ai_accuracy_rating' in quality_feedback:
                    ai_accuracy = quality_feedback['ai_accuracy_rating']
                    reviewer.quality_score = (
                        alpha * ai_accuracy + 
                        (1 - alpha) * reviewer.quality_score
                    )
            
            # Store quality feedback for AI improvement
            if quality_feedback:
                assignment.ai_accuracy_rating = quality_feedback.get('ai_accuracy_rating')
                assignment.false_positive_flags = quality_feedback.get('false_positives', [])
                assignment.false_negative_flags = quality_feedback.get('false_negatives', [])
            
            # Commit changes
            self.db_session.commit()
            
            # Process next queued document for this reviewer
            await self._assign_next_queued_document(reviewer_id)
            
            # Update metrics
            self._update_completion_metrics()
            
            # Audit log completion
            await self.audit_logger.log_event(
                event_type=AuditEventType.REVIEW_COMPLETED,
                event_description=f"Review completed: {'approved' if approved else 'rejected'}",
                document_version_id=assignment.document_version_id,
                user_id=reviewer_id,
                event_data={
                    "assignment_id": assignment_id,
                    "approved": approved,
                    "sla_met": assignment.sla_met,
                    "actual_duration_hours": assignment.actual_duration_hours,
                    "confidence_score": confidence_score
                }
            )
            
            logger.info(
                f"Review {assignment_id} completed by {reviewer_id}: "
                f"{'approved' if approved else 'rejected'}, "
                f"SLA: {'met' if assignment.sla_met else 'missed'}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to complete review {assignment_id}: {e}")
            self.db_session.rollback()
            return False
    
    async def _assign_next_queued_document(self, reviewer_id: str):
        """Assign next queued document to reviewer if available."""
        
        reviewer = self.reviewers.get(reviewer_id)
        if not reviewer or reviewer.current_workload >= reviewer.max_concurrent_reviews:
            return
        
        # Check priority queues in order
        for priority in [ReviewPriority.CRITICAL, ReviewPriority.HIGH, ReviewPriority.MEDIUM, ReviewPriority.LOW]:
            queue = self.priority_queues[priority]
            
            if queue.size() > 0:
                doc_version_id = queue.pop()
                
                # Get document and assign
                doc_version = self.db_session.query(DocumentVersion).filter(
                    DocumentVersion.id == doc_version_id
                ).first()
                
                if doc_version and doc_version.processing_status == ProcessingStatus.HUMAN_REVIEW:
                    await self.assign_document_for_review(
                        doc_version=doc_version,
                        priority=priority,
                        required_role=reviewer.role
                    )
                    break
    
    async def escalate_review(
        self,
        assignment_id: str,
        escalation_reason: EscalationReason,
        escalated_by: str,
        notes: str = ""
    ) -> str:
        """
        Escalate review to higher authority level.
        
        Args:
            assignment_id: Current review assignment ID
            escalation_reason: Reason for escalation
            escalated_by: User ID initiating escalation
            notes: Additional escalation notes
            
        Returns:
            new_assignment_id: ID of new escalated assignment
        """
        
        try:
            # Get current assignment
            assignment = self.db_session.query(ReviewAssignment).filter(
                ReviewAssignment.id == assignment_id
            ).first()
            
            if not assignment:
                logger.error(f"Assignment {assignment_id} not found for escalation")
                return None
            
            # Determine escalation target role
            current_role = ReviewerRole(assignment.reviewer_role)
            escalated_role = self._get_escalation_role(current_role, escalation_reason)
            
            if escalated_role == current_role:
                logger.warning(f"Cannot escalate assignment {assignment_id} - already at highest role")
                return None
            
            # Update current assignment
            assignment.status = ReviewStatus.ESCALATED.value
            assignment.escalated_at = datetime.utcnow()
            assignment.escalation_reason = escalation_reason.value
            assignment.escalation_count += 1
            assignment.escalated_to_role = escalated_role.value
            
            # Reduce workload of original reviewer
            original_reviewer = self.reviewers.get(assignment.assigned_reviewer_id)
            if original_reviewer:
                original_reviewer.current_workload = max(0, original_reviewer.current_workload - 1)
            
            # Create new escalated assignment
            doc_version = self.db_session.query(DocumentVersion).filter(
                DocumentVersion.id == assignment.document_version_id
            ).first()
            
            escalated_priority = self._escalate_priority(ReviewPriority(assignment.priority))
            
            new_assignment_id = await self.assign_document_for_review(
                doc_version=doc_version,
                priority=escalated_priority,
                review_type=ReviewType(assignment.review_type),
                required_role=escalated_role,
                due_date=assignment.due_date  # Keep original due date for urgency
            )
            
            # Audit log escalation
            await self.audit_logger.log_event(
                event_type=AuditEventType.REVIEW_ASSIGNED,  # Escalated review is a new assignment
                event_description=f"Review escalated: {escalation_reason.value}",
                document_version_id=assignment.document_version_id,
                user_id=escalated_by,
                event_data={
                    "original_assignment_id": assignment_id,
                    "new_assignment_id": new_assignment_id,
                    "escalation_reason": escalation_reason.value,
                    "original_role": current_role.value,
                    "escalated_role": escalated_role.value,
                    "notes": notes
                }
            )
            
            logger.info(
                f"Escalated assignment {assignment_id} from {current_role.value} "
                f"to {escalated_role.value}: {escalation_reason.value}"
            )
            
            return new_assignment_id
            
        except Exception as e:
            logger.error(f"Failed to escalate assignment {assignment_id}: {e}")
            self.db_session.rollback()
            return None
    
    def _get_escalation_role(self, current_role: ReviewerRole, reason: EscalationReason) -> ReviewerRole:
        """Determine target role for escalation based on current role and reason."""
        
        role_hierarchy = [ReviewerRole.PARALEGAL, ReviewerRole.ASSOCIATE, ReviewerRole.PARTNER, ReviewerRole.SENIOR_PARTNER]
        current_index = role_hierarchy.index(current_role)
        
        # Escalation rules based on reason
        if reason == EscalationReason.SLA_BREACH:
            # SLA breach: escalate one level
            return role_hierarchy[min(len(role_hierarchy) - 1, current_index + 1)]
        elif reason in [EscalationReason.COMPLIANCE_ISSUE, EscalationReason.CLIENT_REQUEST]:
            # Critical issues: escalate to Partner or above
            return role_hierarchy[max(2, current_index + 1)]  # Partner minimum
        elif reason == EscalationReason.COMPLEXITY:
            # Complexity: escalate one or two levels based on current role
            escalation_levels = {
                ReviewerRole.PARALEGAL: 2,    # To Associate
                ReviewerRole.ASSOCIATE: 1,     # To Partner
                ReviewerRole.PARTNER: 1       # To Senior Partner
            }
            levels_up = escalation_levels.get(current_role, 1)
            return role_hierarchy[min(len(role_hierarchy) - 1, current_index + levels_up)]
        else:
            # Default: escalate one level
            return role_hierarchy[min(len(role_hierarchy) - 1, current_index + 1)]
    
    def _escalate_priority(self, current_priority: ReviewPriority) -> ReviewPriority:
        """Escalate priority level when escalating review."""
        
        priority_hierarchy = [ReviewPriority.LOW, ReviewPriority.MEDIUM, ReviewPriority.HIGH, ReviewPriority.CRITICAL]
        current_index = priority_hierarchy.index(current_priority)
        
        # Escalate by one level, capped at CRITICAL
        return priority_hierarchy[min(len(priority_hierarchy) - 1, current_index + 1)]
    
    async def start_monitoring(self):
        """Start background monitoring tasks for SLA compliance and queue management."""
        
        if self._monitoring_active:
            return
        
        self._monitoring_active = True
        
        # Start monitoring tasks
        asyncio.create_task(self._monitor_sla_compliance())
        asyncio.create_task(self._monitor_queue_health())
        asyncio.create_task(self._update_metrics_periodically())
        
        logger.info("Started review queue monitoring tasks")
    
    async def _monitor_sla_compliance(self):
        """Monitor SLA compliance and auto-escalate overdue reviews."""
        
        while self._monitoring_active:
            try:
                current_time = datetime.utcnow()
                
                # Find overdue assignments
                overdue_assignments = self.db_session.query(ReviewAssignment).filter(
                    and_(
                        ReviewAssignment.status.in_([ReviewStatus.ASSIGNED.value, ReviewStatus.IN_PROGRESS.value]),
                        ReviewAssignment.due_date < current_time,
                        ReviewAssignment.escalation_count < self.max_retries
                    )
                ).all()
                
                for assignment in overdue_assignments:
                    # Update status to overdue
                    assignment.status = ReviewStatus.OVERDUE.value
                    assignment.sla_met = False
                    
                    # Auto-escalate if configured
                    await self.escalate_review(
                        assignment_id=assignment.id,
                        escalation_reason=EscalationReason.SLA_BREACH,
                        escalated_by="system",
                        notes=f"Auto-escalated due to SLA breach (overdue by {current_time - assignment.due_date})"
                    )
                
                if overdue_assignments:
                    self.db_session.commit()
                    logger.warning(f"Auto-escalated {len(overdue_assignments)} overdue reviews")
                
                # Sleep for 5 minutes before next check
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error(f"SLA monitoring error: {e}")
                await asyncio.sleep(60)  # Shorter retry on error
    
    async def _monitor_queue_health(self):
        """Monitor queue depths and alert on buildup."""
        
        while self._monitoring_active:
            try:
                # Update queue metrics
                self._update_queue_metrics()
                
                # Alert thresholds
                critical_threshold = 10
                high_threshold = 20
                
                if self.metrics.critical_queue_depth >= critical_threshold:
                    await self._alert_critical_queue_buildup()
                
                if self.metrics.total_queue_depth >= high_threshold:
                    await self._alert_queue_buildup()
                
                # Sleep for 2 minutes
                await asyncio.sleep(120)
                
            except Exception as e:
                logger.error(f"Queue health monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def _update_metrics_periodically(self):
        """Update performance metrics every 10 minutes."""
        
        while self._monitoring_active:
            try:
                self._update_completion_metrics()
                self._update_reviewer_utilization()
                
                # Sleep for 10 minutes
                await asyncio.sleep(600)
                
            except Exception as e:
                logger.error(f"Metrics update error: {e}")
                await asyncio.sleep(60)
    
    def _update_queue_metrics(self):
        """Update queue depth metrics."""
        self.metrics.critical_queue_depth = self.priority_queues[ReviewPriority.CRITICAL].size()
        self.metrics.high_queue_depth = self.priority_queues[ReviewPriority.HIGH].size()
        self.metrics.medium_queue_depth = self.priority_queues[ReviewPriority.MEDIUM].size()
        self.metrics.low_queue_depth = self.priority_queues[ReviewPriority.LOW].size()
    
    def _update_completion_metrics(self):
        """Update completion and SLA metrics from database."""
        
        # Get metrics from last 24 hours
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        completed_reviews = self.db_session.query(ReviewAssignment).filter(
            and_(
                ReviewAssignment.status == ReviewStatus.COMPLETED.value,
                ReviewAssignment.completed_at >= cutoff_time
            )
        ).all()
        
        self.metrics.total_completed = len(completed_reviews)
        
        if completed_reviews:
            # Calculate SLA compliance
            sla_met_count = sum(1 for r in completed_reviews if r.sla_met)
            self.metrics.sla_compliance_rate = (sla_met_count / len(completed_reviews)) * 100
            
            # Calculate average completion time
            completion_times = [
                r.actual_duration_hours for r in completed_reviews 
                if r.actual_duration_hours is not None
            ]
            
            if completion_times:
                self.metrics.average_completion_time_hours = statistics.mean(completion_times)
        
        # Get current assignment counts
        current_assignments = self.db_session.query(ReviewAssignment).filter(
            ReviewAssignment.status.in_([
                ReviewStatus.ASSIGNED.value,
                ReviewStatus.IN_PROGRESS.value
            ])
        ).all()
        
        self.metrics.total_assigned = len(current_assignments)
        
        # Count overdue and escalated
        overdue_count = self.db_session.query(ReviewAssignment).filter(
            and_(
                ReviewAssignment.status == ReviewStatus.OVERDUE.value,
                ReviewAssignment.due_date < datetime.utcnow()
            )
        ).count()
        
        escalated_count = self.db_session.query(ReviewAssignment).filter(
            ReviewAssignment.status == ReviewStatus.ESCALATED.value
        ).count()
        
        self.metrics.total_overdue = overdue_count
        self.metrics.total_escalated = escalated_count
    
    def _update_reviewer_utilization(self):
        """Update reviewer utilization metrics."""
        
        for reviewer_id, reviewer in self.reviewers.items():
            self.metrics.reviewer_utilization[reviewer_id] = reviewer.capacity_utilization
    
    async def _alert_critical_queue_buildup(self):
        """Alert on critical priority queue buildup."""
        
        # Implementation would integrate with alerting system
        logger.critical(
            f"ALERT: Critical priority queue depth ({self.metrics.critical_queue_depth}) "
            "exceeds threshold - immediate attention required"
        )
        
        # Could send email, Slack notification, etc.
    
    async def _alert_queue_buildup(self):
        """Alert on general queue buildup."""
        
        logger.warning(
            f"Queue buildup alert: Total depth {self.metrics.total_queue_depth} "
            f"(Critical: {self.metrics.critical_queue_depth}, "
            f"High: {self.metrics.high_queue_depth})"
        )
    
    async def get_review_dashboard(self) -> Dict[str, Any]:
        """Generate comprehensive review queue dashboard data."""
        
        # Update metrics before returning
        self._update_completion_metrics()
        self._update_queue_metrics()
        self._update_reviewer_utilization()
        
        # Get reviewer statistics
        reviewer_stats = {}
        for reviewer_id, reviewer in self.reviewers.items():
            reviewer_stats[reviewer_id] = {
                "role": reviewer.role.value,
                "current_workload": reviewer.current_workload,
                "capacity_utilization": reviewer.capacity_utilization,
                "is_available": reviewer.is_available,
                "completion_rate": reviewer.completion_rate,
                "quality_score": reviewer.quality_score,
                "estimated_availability": reviewer.estimated_availability.isoformat(),
                "specializations": list(reviewer.specializations)
            }
        
        return {
            "queue_metrics": {
                "total_depth": self.metrics.total_queue_depth,
                "critical_depth": self.metrics.critical_queue_depth,
                "high_depth": self.metrics.high_queue_depth,
                "medium_depth": self.metrics.medium_queue_depth,
                "low_depth": self.metrics.low_queue_depth
            },
            "performance_metrics": {
                "sla_compliance_rate": self.metrics.sla_compliance_rate,
                "average_completion_time_hours": self.metrics.average_completion_time_hours,
                "total_assigned": self.metrics.total_assigned,
                "total_completed": self.metrics.total_completed,
                "total_overdue": self.metrics.total_overdue,
                "total_escalated": self.metrics.total_escalated
            },
            "reviewer_statistics": reviewer_stats,
            "sla_targets": {p.value: h for p, h in self.sla_targets.items()},
            "system_health": {
                "monitoring_active": self._monitoring_active,
                "last_metrics_update": self._last_metrics_update.isoformat(),
                "assignment_strategy": self.assignment_strategy
            }
        }
    
    async def stop_monitoring(self):
        """Stop background monitoring tasks."""
        self._monitoring_active = False
        logger.info("Stopped review queue monitoring tasks")

# Testing and validation
async def validate_review_queue():
    """Test the human review queue with mock data."""
    
    logger.info("Validating HumanReviewQueue...")
    
    # Mock database session
    class MockSession:
        def __init__(self):
            self.assignments = {}
            self.documents = {}
        
        def add(self, obj):
            pass
        
        def commit(self):
            pass
        
        def rollback(self):
            pass
        
        def query(self, model):
            return MockQuery(self, model)
    
    class MockQuery:
        def __init__(self, session, model):
            self.session = session
            self.model = model
        
        def filter(self, condition):
            return self
        
        def first(self):
            return None
        
        def all(self):
            return []
        
        def count(self):
            return 0
    
    # Test review queue
    review_queue = HumanReviewQueue(db_session=MockSession())
    
    # Initialize test reviewers
    reviewers = [
        {
            "reviewer_id": "paralegal_1",
            "role": "paralegal",
            "max_concurrent": 5,
            "specializations": ["contracts"]
        },
        {
            "reviewer_id": "associate_1", 
            "role": "associate",
            "max_concurrent": 8,
            "specializations": ["employment_law", "contracts"]
        },
        {
            "reviewer_id": "partner_1",
            "role": "partner",
            "max_concurrent": 3,
            "specializations": ["compliance", "real_estate"]
        }
    ]
    
    await review_queue.initialize_reviewers(reviewers)
    
    assert len(review_queue.reviewers) == 3, "Should have 3 reviewers"
    assert len(review_queue.role_queues) == 3, "Should have 3 role queues"
    
    # Test assignment strategy
    paralegal = review_queue.reviewers["paralegal_1"]
    associate = review_queue.reviewers["associate_1"]
    
    eligible = [paralegal, associate]
    selected = review_queue._select_load_balanced_reviewer(eligible)
    
    assert selected is not None, "Should select a reviewer"
    
    logger.info("HumanReviewQueue validation completed successfully")

if __name__ == "__main__":
    # Run validation test
    asyncio.run(validate_review_queue())