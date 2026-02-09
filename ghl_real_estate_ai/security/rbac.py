"""
Role-Based Access Control (RBAC) System
Provides comprehensive permission management with hierarchical roles and fine-grained permissions
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional

from .audit_logger import AuditLogger


class PermissionType(str, Enum):
    """Types of permissions in the system"""

    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"
    ADMIN = "admin"
    MANAGE = "manage"


class ResourceType(str, Enum):
    """System resources that can have permissions"""

    # Core entities
    USERS = "users"
    LEADS = "leads"
    PROPERTIES = "properties"
    CONTACTS = "contacts"
    CAMPAIGNS = "campaigns"
    REPORTS = "reports"
    ANALYTICS = "analytics"

    # System features
    API = "api"
    WEBHOOKS = "webhooks"
    INTEGRATIONS = "integrations"
    WORKFLOWS = "workflows"
    AUTOMATION = "automation"

    # Admin features
    SYSTEM_CONFIG = "system_config"
    AUDIT_LOGS = "audit_logs"
    RATE_LIMITS = "rate_limits"
    SECURITY = "security"
    BILLING = "billing"

    # AI/ML features
    AI_MODELS = "ai_models"
    CLAUDE_ASSISTANT = "claude_assistant"
    PREDICTIVE_SCORING = "predictive_scoring"
    BEHAVIORAL_ANALYSIS = "behavioral_analysis"

    # Data and exports
    DATA_EXPORT = "data_export"
    DATA_IMPORT = "data_import"
    BACKUPS = "backups"


@dataclass
class Permission:
    """Individual permission with scope and conditions"""

    name: str
    resource: ResourceType
    permission_type: PermissionType
    scope: str = "*"  # * for all, specific ID for individual resources
    conditions: Dict = field(default_factory=dict)
    expires_at: Optional[datetime] = None
    granted_by: Optional[str] = None
    granted_at: datetime = field(default_factory=datetime.utcnow)

    def is_valid(self) -> bool:
        """Check if permission is still valid"""
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        return True

    def matches(self, resource: ResourceType, permission_type: PermissionType, scope: str = "*") -> bool:
        """Check if this permission matches the requested access"""
        if not self.is_valid():
            return False

        # Check resource
        if self.resource != resource:
            return False

        # Check permission type
        if self.permission_type != permission_type:
            # Check if we have a higher-level permission
            hierarchy = {
                PermissionType.READ: 1,
                PermissionType.EXECUTE: 2,
                PermissionType.WRITE: 3,
                PermissionType.DELETE: 4,
                PermissionType.MANAGE: 5,
                PermissionType.ADMIN: 6,
            }

            current_level = hierarchy.get(self.permission_type, 0)
            required_level = hierarchy.get(permission_type, 0)

            if current_level < required_level:
                return False

        # Check scope
        if self.scope == "*":
            return True  # Global permission
        elif scope == "*":
            return False  # Requesting global but we only have specific
        else:
            return self.scope == scope

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            "name": self.name,
            "resource": self.resource.value,
            "permission_type": self.permission_type.value,
            "scope": self.scope,
            "conditions": self.conditions,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "granted_by": self.granted_by,
            "granted_at": self.granted_at.isoformat(),
        }


@dataclass
class Role:
    """Role containing multiple permissions with inheritance"""

    name: str
    display_name: str
    description: str
    permissions: List[Permission] = field(default_factory=list)
    parent_roles: List[str] = field(default_factory=list)
    is_system_role: bool = False
    created_by: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def add_permission(self, permission: Permission):
        """Add permission to role"""
        # Remove any existing permission with same name
        self.permissions = [p for p in self.permissions if p.name != permission.name]
        self.permissions.append(permission)

    def remove_permission(self, permission_name: str) -> bool:
        """Remove permission from role"""
        original_count = len(self.permissions)
        self.permissions = [p for p in self.permissions if p.name != permission_name]
        return len(self.permissions) < original_count

    def get_all_permissions(self, role_manager: "RoleManager" = None) -> List[Permission]:
        """Get all permissions including inherited ones"""
        all_permissions = self.permissions.copy()

        if role_manager:
            # Add permissions from parent roles
            for parent_name in self.parent_roles:
                parent_role = role_manager.get_role(parent_name)
                if parent_role:
                    all_permissions.extend(parent_role.get_all_permissions(role_manager))

        # Remove duplicates (keep the most specific permission)
        unique_permissions = {}
        for perm in all_permissions:
            key = f"{perm.resource.value}:{perm.permission_type.value}:{perm.scope}"
            if key not in unique_permissions or perm.scope != "*":
                unique_permissions[key] = perm

        return list(unique_permissions.values())

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "permissions": [p.to_dict() for p in self.permissions],
            "parent_roles": self.parent_roles,
            "is_system_role": self.is_system_role,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
        }


class RoleManager:
    """Manages roles and permissions with enterprise features"""

    def __init__(self):
        self.audit_logger = AuditLogger()
        self.roles: Dict[str, Role] = {}
        self._initialize_system_roles()

    def _initialize_system_roles(self):
        """Initialize default system roles"""

        # Super Admin Role
        super_admin = Role(
            name="super_admin",
            display_name="Super Administrator",
            description="Full system access with all permissions",
            is_system_role=True,
        )

        # Add all permissions for super admin
        for resource in ResourceType:
            super_admin.add_permission(
                Permission(
                    name=f"super_admin_{resource.value}_all",
                    resource=resource,
                    permission_type=PermissionType.ADMIN,
                    scope="*",
                )
            )

        self.roles["super_admin"] = super_admin

        # Admin Role
        admin = Role(
            name="admin",
            display_name="Administrator",
            description="Administrative access to most features",
            is_system_role=True,
        )

        admin_resources = [
            ResourceType.USERS,
            ResourceType.LEADS,
            ResourceType.PROPERTIES,
            ResourceType.CONTACTS,
            ResourceType.CAMPAIGNS,
            ResourceType.REPORTS,
            ResourceType.ANALYTICS,
            ResourceType.WORKFLOWS,
            ResourceType.AUTOMATION,
            ResourceType.AI_MODELS,
            ResourceType.CLAUDE_ASSISTANT,
            ResourceType.PREDICTIVE_SCORING,
            ResourceType.BEHAVIORAL_ANALYSIS,
        ]

        for resource in admin_resources:
            admin.add_permission(
                Permission(
                    name=f"admin_{resource.value}_manage",
                    resource=resource,
                    permission_type=PermissionType.MANAGE,
                    scope="*",
                )
            )

        # API access
        admin.add_permission(
            Permission(
                name="admin_api_access", resource=ResourceType.API, permission_type=PermissionType.EXECUTE, scope="*"
            )
        )

        self.roles["admin"] = admin

        # Manager Role
        manager = Role(
            name="manager",
            display_name="Manager",
            description="Management access to leads and teams",
            is_system_role=True,
        )

        manager_permissions = [
            (ResourceType.LEADS, PermissionType.MANAGE),
            (ResourceType.CONTACTS, PermissionType.MANAGE),
            (ResourceType.PROPERTIES, PermissionType.WRITE),
            (ResourceType.CAMPAIGNS, PermissionType.WRITE),
            (ResourceType.REPORTS, PermissionType.READ),
            (ResourceType.ANALYTICS, PermissionType.READ),
            (ResourceType.WORKFLOWS, PermissionType.WRITE),
            (ResourceType.AUTOMATION, PermissionType.WRITE),
            (ResourceType.CLAUDE_ASSISTANT, PermissionType.EXECUTE),
            (ResourceType.PREDICTIVE_SCORING, PermissionType.READ),
            (ResourceType.BEHAVIORAL_ANALYSIS, PermissionType.READ),
            (ResourceType.API, PermissionType.EXECUTE),
        ]

        for resource, perm_type in manager_permissions:
            manager.add_permission(
                Permission(
                    name=f"manager_{resource.value}_{perm_type.value}",
                    resource=resource,
                    permission_type=perm_type,
                    scope="*",
                )
            )

        self.roles["manager"] = manager

        # Agent Role
        agent = Role(
            name="agent",
            display_name="Agent",
            description="Standard agent access to leads and properties",
            is_system_role=True,
        )

        agent_permissions = [
            (ResourceType.LEADS, PermissionType.WRITE),
            (ResourceType.CONTACTS, PermissionType.WRITE),
            (ResourceType.PROPERTIES, PermissionType.READ),
            (ResourceType.CAMPAIGNS, PermissionType.READ),
            (ResourceType.REPORTS, PermissionType.READ),
            (ResourceType.ANALYTICS, PermissionType.READ),
            (ResourceType.WORKFLOWS, PermissionType.EXECUTE),
            (ResourceType.CLAUDE_ASSISTANT, PermissionType.EXECUTE),
            (ResourceType.PREDICTIVE_SCORING, PermissionType.READ),
            (ResourceType.API, PermissionType.EXECUTE),
        ]

        for resource, perm_type in agent_permissions:
            agent.add_permission(
                Permission(
                    name=f"agent_{resource.value}_{perm_type.value}",
                    resource=resource,
                    permission_type=perm_type,
                    scope="*",
                )
            )

        self.roles["agent"] = agent

        # Viewer Role
        viewer = Role(
            name="viewer", display_name="Viewer", description="Read-only access to basic features", is_system_role=True
        )

        viewer_resources = [
            ResourceType.LEADS,
            ResourceType.CONTACTS,
            ResourceType.PROPERTIES,
            ResourceType.CAMPAIGNS,
            ResourceType.REPORTS,
            ResourceType.ANALYTICS,
        ]

        for resource in viewer_resources:
            viewer.add_permission(
                Permission(
                    name=f"viewer_{resource.value}_read",
                    resource=resource,
                    permission_type=PermissionType.READ,
                    scope="*",
                )
            )

        self.roles["viewer"] = viewer

        # API User Role
        api_user = Role(
            name="api_user", display_name="API User", description="API access for integrations", is_system_role=True
        )

        api_user.add_permission(
            Permission(
                name="api_user_api_access", resource=ResourceType.API, permission_type=PermissionType.EXECUTE, scope="*"
            )
        )

        api_user.add_permission(
            Permission(
                name="api_user_webhooks",
                resource=ResourceType.WEBHOOKS,
                permission_type=PermissionType.EXECUTE,
                scope="*",
            )
        )

        api_user.add_permission(
            Permission(
                name="api_user_integrations",
                resource=ResourceType.INTEGRATIONS,
                permission_type=PermissionType.EXECUTE,
                scope="*",
            )
        )

        self.roles["api_user"] = api_user

    def create_role(
        self,
        name: str,
        display_name: str,
        description: str,
        permissions: List[Permission] = None,
        parent_roles: List[str] = None,
        created_by: str = None,
    ) -> Role:
        """Create a new role"""
        if name in self.roles:
            raise ValueError(f"Role '{name}' already exists")

        role = Role(
            name=name,
            display_name=display_name,
            description=description,
            permissions=permissions or [],
            parent_roles=parent_roles or [],
            created_by=created_by,
        )

        self.roles[name] = role

        # Audit log
        self.audit_logger.log_admin_action(
            "role_created",
            {
                "role_name": name,
                "display_name": display_name,
                "created_by": created_by,
                "permissions_count": len(permissions or []),
                "parent_roles": parent_roles or [],
            },
        )

        return role

    def get_role(self, name: str) -> Optional[Role]:
        """Get role by name"""
        return self.roles.get(name)

    def update_role(self, name: str, display_name: str = None, description: str = None, updated_by: str = None) -> bool:
        """Update role properties"""
        role = self.roles.get(name)
        if not role:
            return False

        if role.is_system_role:
            raise ValueError("Cannot modify system roles")

        changes = {}
        if display_name is not None:
            changes["display_name"] = {"old": role.display_name, "new": display_name}
            role.display_name = display_name

        if description is not None:
            changes["description"] = {"old": role.description, "new": description}
            role.description = description

        if changes:
            self.audit_logger.log_admin_action(
                "role_updated", {"role_name": name, "updated_by": updated_by, "changes": changes}
            )

        return True

    def delete_role(self, name: str, deleted_by: str = None) -> bool:
        """Delete a role"""
        role = self.roles.get(name)
        if not role:
            return False

        if role.is_system_role:
            raise ValueError("Cannot delete system roles")

        del self.roles[name]

        self.audit_logger.log_admin_action(
            "role_deleted",
            {
                "role_name": name,
                "display_name": role.display_name,
                "deleted_by": deleted_by,
                "permissions_count": len(role.permissions),
            },
        )

        return True

    def add_permission_to_role(self, role_name: str, permission: Permission, granted_by: str = None) -> bool:
        """Add permission to role"""
        role = self.roles.get(role_name)
        if not role:
            return False

        if role.is_system_role:
            raise ValueError("Cannot modify system role permissions")

        permission.granted_by = granted_by
        role.add_permission(permission)

        self.audit_logger.log_admin_action(
            "permission_granted", {"role_name": role_name, "permission": permission.to_dict(), "granted_by": granted_by}
        )

        return True

    def remove_permission_from_role(self, role_name: str, permission_name: str, removed_by: str = None) -> bool:
        """Remove permission from role"""
        role = self.roles.get(role_name)
        if not role:
            return False

        if role.is_system_role:
            raise ValueError("Cannot modify system role permissions")

        removed = role.remove_permission(permission_name)

        if removed:
            self.audit_logger.log_admin_action(
                "permission_revoked",
                {"role_name": role_name, "permission_name": permission_name, "removed_by": removed_by},
            )

        return removed

    def check_permission(
        self, user_roles: List[str], resource: ResourceType, permission_type: PermissionType, scope: str = "*"
    ) -> bool:
        """Check if user roles have required permission"""

        for role_name in user_roles:
            role = self.get_role(role_name)
            if not role:
                continue

            permissions = role.get_all_permissions(self)

            for permission in permissions:
                if permission.matches(resource, permission_type, scope):
                    return True

        return False

    def get_user_permissions(self, user_roles: List[str]) -> List[Permission]:
        """Get all permissions for user roles"""
        all_permissions = []

        for role_name in user_roles:
            role = self.get_role(role_name)
            if role:
                all_permissions.extend(role.get_all_permissions(self))

        # Remove duplicates
        unique_permissions = {}
        for perm in all_permissions:
            key = f"{perm.resource.value}:{perm.permission_type.value}:{perm.scope}"
            if key not in unique_permissions:
                unique_permissions[key] = perm

        return list(unique_permissions.values())

    def list_roles(self, include_system: bool = True) -> List[Role]:
        """List all roles"""
        roles = list(self.roles.values())

        if not include_system:
            roles = [r for r in roles if not r.is_system_role]

        return sorted(roles, key=lambda r: (r.is_system_role, r.name))

    def export_roles(self) -> Dict:
        """Export all roles to dictionary"""
        return {
            "roles": {name: role.to_dict() for name, role in self.roles.items()},
            "exported_at": datetime.utcnow().isoformat(),
        }

    def import_roles(self, roles_data: Dict, imported_by: str = None):
        """Import roles from dictionary"""
        imported_count = 0

        for name, role_data in roles_data.get("roles", {}).items():
            if name in self.roles and self.roles[name].is_system_role:
                continue  # Skip system roles

            # Create permissions
            permissions = []
            for perm_data in role_data.get("permissions", []):
                perm = Permission(
                    name=perm_data["name"],
                    resource=ResourceType(perm_data["resource"]),
                    permission_type=PermissionType(perm_data["permission_type"]),
                    scope=perm_data.get("scope", "*"),
                    conditions=perm_data.get("conditions", {}),
                    granted_by=imported_by,
                )
                permissions.append(perm)

            # Create role
            role = Role(
                name=name,
                display_name=role_data["display_name"],
                description=role_data["description"],
                permissions=permissions,
                parent_roles=role_data.get("parent_roles", []),
                created_by=imported_by,
            )

            self.roles[name] = role
            imported_count += 1

        self.audit_logger.log_admin_action(
            "roles_imported", {"imported_by": imported_by, "roles_count": imported_count, "source": "import_operation"}
        )

        return imported_count


# Predefined system roles for easy access
class SystemRole:
    """System role constants"""

    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MANAGER = "manager"
    AGENT = "agent"
    VIEWER = "viewer"
    API_USER = "api_user"


# Permission checking decorators and functions
def require_permission(resource: ResourceType, permission_type: PermissionType, scope: str = "*"):
    """Decorator to check permissions for FastAPI endpoints"""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract user from request context
            # This will be implemented with the authentication middleware
            pass

        return wrapper

    return decorator


def create_permission(
    name: str,
    resource: ResourceType,
    permission_type: PermissionType,
    scope: str = "*",
    expires_in_days: int = None,
    conditions: Dict = None,
) -> Permission:
    """Helper function to create permissions"""
    expires_at = None
    if expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

    return Permission(
        name=name,
        resource=resource,
        permission_type=permission_type,
        scope=scope,
        conditions=conditions or {},
        expires_at=expires_at,
    )
