"""
Enterprise Input Validation System
Comprehensive input validation and sanitization to prevent injection attacks and malicious input
"""

import re
import html
import json
import urllib.parse
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

import bleach
from pydantic import BaseModel, ValidationError, validator
from email_validator import validate_email, EmailNotValidError


class ValidationSeverity(str, Enum):
    """Validation error severity levels"""
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ValidationRule:
    """Input validation rule"""
    name: str
    pattern: str
    severity: ValidationSeverity
    description: str
    action: str = "reject"  # reject, sanitize, warn


@dataclass
class ValidationResult:
    """Validation result"""
    is_valid: bool
    sanitized_value: Any = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    severity: ValidationSeverity = ValidationSeverity.LOW


class InputValidator:
    """
    Comprehensive input validation system for enterprise security
    """
    
    def __init__(self):
        self._initialize_rules()
        
        # HTML sanitizer configuration
        self.allowed_html_tags = [
            'p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'
        ]
        self.allowed_html_attributes = {
            '*': ['class'],
            'a': ['href', 'title'],
            'img': ['src', 'alt', 'width', 'height']
        }
        
        # File upload validation
        self.allowed_file_extensions = {
            'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'],
            'document': ['.pdf', '.doc', '.docx', '.txt', '.rtf'],
            'spreadsheet': ['.xls', '.xlsx', '.csv'],
            'archive': ['.zip', '.tar', '.gz']
        }
        
        self.max_file_size = 10 * 1024 * 1024  # 10MB
    
    def _initialize_rules(self):
        """Initialize validation rules for common attack patterns"""
        
        self.validation_rules = [
            # SQL Injection
            ValidationRule(
                name="sql_injection",
                pattern=r"(?i)(union\s+select|insert\s+into|update\s+set|delete\s+from|drop\s+table|exec\s*\(|sp_|xp_|'.*or.*'.*=.*')",
                severity=ValidationSeverity.CRITICAL,
                description="SQL injection attempt detected",
                action="reject"
            ),
            
            # XSS (Cross-Site Scripting)
            ValidationRule(
                name="xss_script_tags",
                pattern=r"(?i)<\s*script[^>]*>.*?</\s*script\s*>|<\s*script[^>]*>",
                severity=ValidationSeverity.HIGH,
                description="Script tag detected",
                action="sanitize"
            ),
            ValidationRule(
                name="xss_javascript_protocol",
                pattern=r"(?i)javascript\s*:|data\s*:.*script|vbscript\s*:",
                severity=ValidationSeverity.HIGH,
                description="Dangerous JavaScript protocol detected",
                action="reject"
            ),
            ValidationRule(
                name="xss_event_handlers",
                pattern=r"(?i)on(load|error|click|mouse|focus|blur|change|submit|key|resize)\s*=",
                severity=ValidationSeverity.HIGH,
                description="JavaScript event handler detected",
                action="sanitize"
            ),
            
            # LDAP Injection
            ValidationRule(
                name="ldap_injection",
                pattern=r"[()=*|&]|\\[0-9a-fA-F]{2}",
                severity=ValidationSeverity.MEDIUM,
                description="LDAP injection attempt detected",
                action="reject"
            ),
            
            # Command Injection
            ValidationRule(
                name="command_injection",
                pattern=r"(?i)(\||;|&|`|\$\(|\${|<|>|&&|\|\||exec|eval|system|shell_exec|passthru)",
                severity=ValidationSeverity.CRITICAL,
                description="Command injection attempt detected",
                action="reject"
            ),
            
            # Path Traversal
            ValidationRule(
                name="path_traversal",
                pattern=r"(\.\.[\\/]|\.\.%2f|\.\.%5c|%2e%2e[\\/]|%2e%2e%2f|%2e%2e%5c)",
                severity=ValidationSeverity.HIGH,
                description="Path traversal attempt detected",
                action="reject"
            ),
            
            # XXE (XML External Entity)
            ValidationRule(
                name="xxe_injection",
                pattern=r"(?i)<!entity|<!doctype.*entity|system\s+['\"]|public\s+['\"]",
                severity=ValidationSeverity.HIGH,
                description="XXE injection attempt detected",
                action="reject"
            ),
            
            # NoSQL Injection
            ValidationRule(
                name="nosql_injection",
                pattern=r"(?i)(\$gt|\$lt|\$ne|\$in|\$nin|\$regex|\$where|\$exists|\$type)",
                severity=ValidationSeverity.MEDIUM,
                description="NoSQL injection attempt detected",
                action="reject"
            ),
            
            # Header Injection
            ValidationRule(
                name="header_injection",
                pattern=r"[\r\n]",
                severity=ValidationSeverity.MEDIUM,
                description="Header injection attempt detected",
                action="sanitize"
            ),
            
            # Suspicious Unicode
            ValidationRule(
                name="suspicious_unicode",
                pattern=r"[\u0000-\u001F\u007F-\u009F\uFEFF\u200B-\u200D\u2060]",
                severity=ValidationSeverity.LOW,
                description="Suspicious Unicode characters detected",
                action="sanitize"
            )
        ]
        
        # Create lookup dictionary for faster access
        self.rules_by_name = {rule.name: rule for rule in self.validation_rules}
    
    async def validate_string(
        self,
        value: str,
        field_name: str = "input",
        max_length: Optional[int] = None,
        min_length: Optional[int] = None,
        allow_html: bool = False,
        custom_rules: Optional[List[str]] = None
    ) -> ValidationResult:
        """
        Validate string input against security rules
        
        Args:
            value: String to validate
            field_name: Name of the field being validated
            max_length: Maximum allowed length
            min_length: Minimum required length
            allow_html: Whether to allow HTML content
            custom_rules: List of specific rule names to check
            
        Returns:
            ValidationResult: Validation result with sanitized value if applicable
        """
        if not isinstance(value, str):
            return ValidationResult(
                is_valid=False,
                errors=[f"{field_name} must be a string"],
                severity=ValidationSeverity.MEDIUM
            )
        
        result = ValidationResult(is_valid=True, sanitized_value=value)
        original_value = value
        
        # Length validation
        if max_length and len(value) > max_length:
            result.errors.append(f"{field_name} exceeds maximum length of {max_length}")
            result.severity = ValidationSeverity.MEDIUM
            result.is_valid = False
        
        if min_length and len(value) < min_length:
            result.errors.append(f"{field_name} is shorter than minimum length of {min_length}")
            result.severity = ValidationSeverity.LOW
            result.is_valid = False
        
        # Security rule validation
        rules_to_check = self.validation_rules
        if custom_rules:
            rules_to_check = [self.rules_by_name[name] for name in custom_rules if name in self.rules_by_name]
        
        for rule in rules_to_check:
            if re.search(rule.pattern, value):
                if rule.action == "reject":
                    result.errors.append(f"{field_name}: {rule.description}")
                    result.severity = max(result.severity, rule.severity)
                    result.is_valid = False
                elif rule.action == "sanitize":
                    # Sanitize the value
                    value = re.sub(rule.pattern, '', value)
                    result.warnings.append(f"{field_name}: {rule.description} - content sanitized")
                    result.severity = max(result.severity, rule.severity)
                elif rule.action == "warn":
                    result.warnings.append(f"{field_name}: {rule.description}")
        
        # HTML sanitization if allowed
        if allow_html and value != original_value:
            value = self._sanitize_html(value)
        elif not allow_html:
            # Remove all HTML if not allowed
            value = html.escape(value)
        
        result.sanitized_value = value
        return result
    
    async def validate_email(self, email: str, field_name: str = "email") -> ValidationResult:
        """Validate email address"""
        try:
            # Basic string validation first
            string_result = await self.validate_string(email, field_name, max_length=320)
            if not string_result.is_valid:
                return string_result
            
            # Email format validation
            validated_email = validate_email(string_result.sanitized_value)
            
            return ValidationResult(
                is_valid=True,
                sanitized_value=validated_email.email,
                warnings=string_result.warnings
            )
            
        except EmailNotValidError as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"{field_name}: {str(e)}"],
                severity=ValidationSeverity.MEDIUM
            )
    
    async def validate_url(self, url: str, field_name: str = "url", allowed_schemes: List[str] = None) -> ValidationResult:
        """Validate URL"""
        if allowed_schemes is None:
            allowed_schemes = ['http', 'https']
        
        # Basic string validation first
        string_result = await self.validate_string(url, field_name, max_length=2048)
        if not string_result.is_valid:
            return string_result
        
        try:
            parsed = urllib.parse.urlparse(string_result.sanitized_value)
            
            # Check scheme
            if parsed.scheme.lower() not in allowed_schemes:
                return ValidationResult(
                    is_valid=False,
                    errors=[f"{field_name}: Invalid URL scheme. Allowed: {', '.join(allowed_schemes)}"],
                    severity=ValidationSeverity.MEDIUM
                )
            
            # Check for dangerous patterns
            if parsed.hostname:
                # Block private/localhost addresses in production
                dangerous_hosts = ['localhost', '127.0.0.1', '0.0.0.0', '::1']
                if parsed.hostname.lower() in dangerous_hosts:
                    return ValidationResult(
                        is_valid=False,
                        errors=[f"{field_name}: Localhost URLs not allowed"],
                        severity=ValidationSeverity.HIGH
                    )
            
            return ValidationResult(
                is_valid=True,
                sanitized_value=string_result.sanitized_value,
                warnings=string_result.warnings
            )
            
        except Exception:
            return ValidationResult(
                is_valid=False,
                errors=[f"{field_name}: Invalid URL format"],
                severity=ValidationSeverity.MEDIUM
            )
    
    async def validate_json(self, json_str: str, field_name: str = "json", max_size: int = 1024*1024) -> ValidationResult:
        """Validate JSON input"""
        # Size check
        if len(json_str.encode('utf-8')) > max_size:
            return ValidationResult(
                is_valid=False,
                errors=[f"{field_name}: JSON too large (max {max_size} bytes)"],
                severity=ValidationSeverity.MEDIUM
            )
        
        # Basic string validation
        string_result = await self.validate_string(json_str, field_name)
        if not string_result.is_valid:
            return string_result
        
        try:
            # Parse JSON
            parsed_json = json.loads(string_result.sanitized_value)
            
            # Check for deeply nested structures (potential DoS)
            max_depth = 10
            if self._get_json_depth(parsed_json) > max_depth:
                return ValidationResult(
                    is_valid=False,
                    errors=[f"{field_name}: JSON nesting too deep (max {max_depth} levels)"],
                    severity=ValidationSeverity.MEDIUM
                )
            
            return ValidationResult(
                is_valid=True,
                sanitized_value=parsed_json,
                warnings=string_result.warnings
            )
            
        except json.JSONDecodeError as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"{field_name}: Invalid JSON format - {str(e)}"],
                severity=ValidationSeverity.MEDIUM
            )
    
    async def validate_file_upload(
        self,
        filename: str,
        content_type: str,
        file_size: int,
        allowed_types: Optional[List[str]] = None
    ) -> ValidationResult:
        """Validate file upload"""
        result = ValidationResult(is_valid=True)
        
        # Size check
        if file_size > self.max_file_size:
            result.errors.append(f"File too large (max {self.max_file_size // (1024*1024)}MB)")
            result.severity = ValidationSeverity.MEDIUM
            result.is_valid = False
        
        # Filename validation
        filename_result = await self.validate_string(
            filename,
            "filename",
            max_length=255,
            custom_rules=["path_traversal", "command_injection"]
        )
        if not filename_result.is_valid:
            result.errors.extend(filename_result.errors)
            result.severity = max(result.severity, filename_result.severity)
            result.is_valid = False
        
        # Extension check
        if filename:
            file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
            
            if allowed_types:
                allowed_extensions = []
                for file_type in allowed_types:
                    allowed_extensions.extend(self.allowed_file_extensions.get(file_type, []))
                
                if file_ext and f'.{file_ext}' not in allowed_extensions:
                    result.errors.append(f"File type not allowed. Allowed: {', '.join(allowed_extensions)}")
                    result.severity = ValidationSeverity.MEDIUM
                    result.is_valid = False
        
        # Content type validation
        dangerous_content_types = [
            'application/x-executable',
            'application/x-dosexec',
            'application/x-msdownload',
            'text/x-script',
            'application/javascript'
        ]
        
        if content_type.lower() in dangerous_content_types:
            result.errors.append("Dangerous file type detected")
            result.severity = ValidationSeverity.HIGH
            result.is_valid = False
        
        return result
    
    async def validate_headers(self, headers: Dict[str, str]) -> ValidationResult:
        """Validate HTTP headers"""
        result = ValidationResult(is_valid=True, sanitized_value={})
        
        for name, value in headers.items():
            # Validate header name
            if not re.match(r'^[a-zA-Z0-9\-_]+$', name):
                result.errors.append(f"Invalid header name: {name}")
                result.severity = ValidationSeverity.MEDIUM
                result.is_valid = False
                continue
            
            # Validate header value
            header_result = await self.validate_string(
                value,
                f"header_{name}",
                max_length=8192,
                custom_rules=["header_injection", "xss_script_tags"]
            )
            
            if not header_result.is_valid:
                result.errors.extend(header_result.errors)
                result.warnings.extend(header_result.warnings)
                result.severity = max(result.severity, header_result.severity)
                result.is_valid = False
            else:
                result.sanitized_value[name] = header_result.sanitized_value
                if header_result.warnings:
                    result.warnings.extend(header_result.warnings)
        
        return result
    
    async def validate_query_params(self, params: Dict[str, str]) -> ValidationResult:
        """Validate query parameters"""
        result = ValidationResult(is_valid=True, sanitized_value={})
        
        for name, value in params.items():
            # Validate parameter name
            if not re.match(r'^[a-zA-Z0-9\-_\[\]]+$', name):
                result.errors.append(f"Invalid parameter name: {name}")
                result.severity = ValidationSeverity.MEDIUM
                result.is_valid = False
                continue
            
            # Validate parameter value
            param_result = await self.validate_string(
                value,
                f"param_{name}",
                max_length=2048
            )
            
            if not param_result.is_valid:
                result.errors.extend(param_result.errors)
                result.warnings.extend(param_result.warnings)
                result.severity = max(result.severity, param_result.severity)
                result.is_valid = False
            else:
                result.sanitized_value[name] = param_result.sanitized_value
                if param_result.warnings:
                    result.warnings.extend(param_result.warnings)
        
        return result
    
    def _sanitize_html(self, html_content: str) -> str:
        """Sanitize HTML content using bleach"""
        return bleach.clean(
            html_content,
            tags=self.allowed_html_tags,
            attributes=self.allowed_html_attributes,
            strip=True
        )
    
    def _get_json_depth(self, obj: Any, depth: int = 0) -> int:
        """Calculate JSON nesting depth"""
        if isinstance(obj, dict):
            return max([self._get_json_depth(v, depth + 1) for v in obj.values()] + [depth])
        elif isinstance(obj, list):
            return max([self._get_json_depth(item, depth + 1) for item in obj] + [depth])
        else:
            return depth
    
    def add_custom_rule(self, rule: ValidationRule):
        """Add custom validation rule"""
        self.validation_rules.append(rule)
        self.rules_by_name[rule.name] = rule
    
    def remove_rule(self, rule_name: str) -> bool:
        """Remove validation rule"""
        if rule_name in self.rules_by_name:
            rule = self.rules_by_name[rule_name]
            self.validation_rules.remove(rule)
            del self.rules_by_name[rule_name]
            return True
        return False
    
    def get_rule_stats(self) -> Dict[str, int]:
        """Get validation rule statistics"""
        severity_counts = {}
        action_counts = {}
        
        for rule in self.validation_rules:
            severity_counts[rule.severity.value] = severity_counts.get(rule.severity.value, 0) + 1
            action_counts[rule.action] = action_counts.get(rule.action, 0) + 1
        
        return {
            "total_rules": len(self.validation_rules),
            "by_severity": severity_counts,
            "by_action": action_counts
        }


# Pydantic models for common validations
class SecureBaseModel(BaseModel):
    """Base Pydantic model with security validations"""
    
    class Config:
        # Prevent extra fields
        extra = "forbid"
        # Validate assignment
        validate_assignment = True
        # Use enum values
        use_enum_values = True


class SecureStringField(BaseModel):
    """Secure string field with validation"""
    value: str
    
    @validator('value')
    def validate_secure_string(cls, v):
        if not isinstance(v, str):
            raise ValueError('Must be a string')
        
        # Basic security checks
        if len(v) > 10000:
            raise ValueError('String too long')
        
        # Check for null bytes
        if '\x00' in v:
            raise ValueError('Null bytes not allowed')
        
        return v


class SecureEmailField(BaseModel):
    """Secure email field with validation"""
    email: str
    
    @validator('email')
    def validate_email_format(cls, v):
        try:
            validated_email = validate_email(v)
            return validated_email.email
        except EmailNotValidError as e:
            raise ValueError(f'Invalid email: {e}')


def create_input_validator() -> InputValidator:
    """Factory function to create input validator"""
    return InputValidator()