"""
Granular RBAC (Role-Based Access Control) for Enterprise Intelligence

This module provides the security layer for the Competitive Intelligence Engine,
ensuring that sensitive strategic data is only accessible to authorized roles.

Roles:
- CEO: Full strategic oversight across all engines.
- SUPPLY_CHAIN_MANAGER: Operational access to supply chain data.
- CMO: Marketing and customer intelligence focus.
- ANALYST: Read-only access to non-sensitive data.
"""

from enum import Enum, auto
from typing import Dict, List, Optional, Set
from dataclasses import dataclass

class Role(Enum):
    CEO = auto()
    SUPPLY_CHAIN_MANAGER = auto()
    CMO = auto()
    ANALYST = auto()
    UNAUTHORIZED = auto()

class Permission(Enum):
    # Strategic Permissions
    VIEW_MNA_THREATS = auto()
    VIEW_EXECUTIVE_SUMMARIES = auto()
    EXECUTE_STRATEGIC_RESPONSE = auto()
    
    # Supply Chain Permissions
    VIEW_SUPPLIER_VULNERABILITIES = auto()
    VIEW_PROCUREMENT_SAVINGS = auto()
    OPTIMIZE_SUPPLY_CHAIN = auto()
    
    # Customer/Marketing Permissions
    VIEW_CUSTOMER_DEFECTION_RISK = auto()
    VIEW_MARKET_SHARE_ANALYSIS = auto()
    
    # General Permissions
    READ_PUBLIC_INTELLIGENCE = auto()

# Role to Permission Mapping
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.CEO: {
        Permission.VIEW_MNA_THREATS,
        Permission.VIEW_EXECUTIVE_SUMMARIES,
        Permission.EXECUTE_STRATEGIC_RESPONSE,
        Permission.VIEW_SUPPLIER_VULNERABILITIES,
        Permission.VIEW_PROCUREMENT_SAVINGS,
        Permission.OPTIMIZE_SUPPLY_CHAIN,
        Permission.VIEW_CUSTOMER_DEFECTION_RISK,
        Permission.VIEW_MARKET_SHARE_ANALYSIS,
        Permission.READ_PUBLIC_INTELLIGENCE,
    },
    Role.SUPPLY_CHAIN_MANAGER: {
        Permission.VIEW_SUPPLIER_VULNERABILITIES,
        Permission.VIEW_PROCUREMENT_SAVINGS,
        Permission.OPTIMIZE_SUPPLY_CHAIN,
        Permission.READ_PUBLIC_INTELLIGENCE,
    },
    Role.CMO: {
        Permission.VIEW_CUSTOMER_DEFECTION_RISK,
        Permission.VIEW_MARKET_SHARE_ANALYSIS,
        Permission.READ_PUBLIC_INTELLIGENCE,
    },
    Role.ANALYST: {
        Permission.READ_PUBLIC_INTELLIGENCE,
    }
}

@dataclass
class User:
    id: str
    username: str
    role: Role

class RBACService:
    """Service to handle permission checks."""
    
    @staticmethod
    def has_permission(user: User, permission: Permission) -> bool:
        """Check if a user has a specific permission."""
        if user.role == Role.UNAUTHORIZED:
            return False
        
        permissions = ROLE_PERMISSIONS.get(user.role, set())
        return permission in permissions

    @staticmethod
    def validate_access(user: User, required_permission: Permission):
        """Validate access or raise an exception."""
        if not RBACService.has_permission(user, required_permission):
            raise PermissionError(
                f"User {user.username} with role {user.role.name} "
                f"does not have required permission: {required_permission.name}"
            )
