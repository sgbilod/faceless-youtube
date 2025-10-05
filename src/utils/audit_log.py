"""
Audit logging for security-sensitive operations

Provides comprehensive audit trail for:
- Authentication events (login, logout, failures)
- Authorization decisions
- Data access and modifications
- Configuration changes
- Security events

All audit logs are structured with consistent fields and severity levels.
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

# Create dedicated audit logger (separate from application logs)
audit_logger = logging.getLogger("audit")


class AuditEventType(Enum):
    """Categories of auditable events"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    CONFIGURATION_CHANGE = "configuration_change"
    SECURITY_EVENT = "security_event"


class AuditAction(Enum):
    """Specific actions to audit"""
    # Authentication
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGED = "password_changed"
    
    # API Keys
    API_KEY_CREATED = "api_key_created"
    API_KEY_REVOKED = "api_key_revoked"
    API_KEY_USED = "api_key_used"
    
    # Video operations
    VIDEO_CREATED = "video_created"
    VIDEO_UPDATED = "video_updated"
    VIDEO_DELETED = "video_deleted"
    VIDEO_UPLOADED = "video_uploaded"
    VIDEO_VIEWED = "video_viewed"
    
    # Script operations
    SCRIPT_GENERATED = "script_generated"
    SCRIPT_MODIFIED = "script_modified"
    SCRIPT_DELETED = "script_deleted"
    
    # Configuration
    SETTINGS_CHANGED = "settings_changed"
    USER_ROLE_CHANGED = "user_role_changed"
    
    # Security
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"


def log_audit_event(
    event_type: AuditEventType,
    action: AuditAction,
    user: str,
    resource: Optional[str] = None,
    success: bool = True,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> None:
    """
    Log a security audit event
    
    Args:
        event_type: Category of event (authentication, data_access, etc.)
        action: Specific action taken (login, video_created, etc.)
        user: Username or user ID performing the action
        resource: Resource affected (video_id, script_id, etc.)
        success: Whether action succeeded
        details: Additional context (changes made, error message, etc.)
        ip_address: Client IP address
        user_agent: Client user agent string
        
    Example:
        >>> log_audit_event(
        ...     event_type=AuditEventType.AUTHENTICATION,
        ...     action=AuditAction.LOGIN,
        ...     user="user@example.com",
        ...     success=True,
        ...     ip_address="192.168.1.1"
        ... )
    """
    # Build log message
    status = "SUCCESS" if success else "FAILURE"
    message = (
        f"AUDIT: {event_type.value.upper()} - "
        f"{action.value} - {status}"
    )
    
    # Build extra fields
    extra_fields = {
        "event_type": event_type.value,
        "action": action.value,
        "user": user,
        "success": success,
        "timestamp": datetime.utcnow().isoformat() + 'Z',
        "event": "audit"
    }
    
    if resource:
        extra_fields["resource"] = resource
    if details:
        extra_fields["details"] = details
    if ip_address:
        extra_fields["ip_address"] = ip_address
    if user_agent:
        extra_fields["user_agent"] = user_agent
    
    # Log at appropriate level
    if not success:
        # Failed operations are warnings
        audit_logger.warning(message, extra=extra_fields)
    elif action in (
        AuditAction.UNAUTHORIZED_ACCESS,
        AuditAction.RATE_LIMIT_EXCEEDED,
        AuditAction.SUSPICIOUS_ACTIVITY
    ):
        # Security events are warnings even if "successful"
        audit_logger.warning(message, extra=extra_fields)
    else:
        # Normal operations are info
        audit_logger.info(message, extra=extra_fields)


# Convenience functions for common operations

def log_login(
    user: str,
    success: bool,
    ip_address: str,
    user_agent: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log login attempt
    
    Args:
        user: Username or email
        success: Whether login succeeded
        ip_address: Client IP
        user_agent: Browser user agent
        details: Additional context (e.g., {"reason": "invalid_password"})
    """
    action = AuditAction.LOGIN if success else AuditAction.LOGIN_FAILED
    log_audit_event(
        event_type=AuditEventType.AUTHENTICATION,
        action=action,
        user=user,
        success=success,
        ip_address=ip_address,
        user_agent=user_agent,
        details=details
    )


def log_logout(user: str, ip_address: str) -> None:
    """Log user logout"""
    log_audit_event(
        event_type=AuditEventType.AUTHENTICATION,
        action=AuditAction.LOGOUT,
        user=user,
        success=True,
        ip_address=ip_address
    )


def log_data_access(
    user: str,
    resource: str,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log data access
    
    Args:
        user: Username
        resource: Resource accessed (e.g., "video:123")
        details: Access context
    """
    log_audit_event(
        event_type=AuditEventType.DATA_ACCESS,
        action=AuditAction.VIDEO_VIEWED,
        user=user,
        resource=resource,
        details=details
    )


def log_data_modification(
    user: str,
    resource: str,
    action: AuditAction,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None
) -> None:
    """
    Log data modification
    
    Args:
        user: Username
        resource: Resource modified
        action: Type of modification (VIDEO_CREATED, VIDEO_DELETED, etc.)
        details: Changes made
        ip_address: Client IP
    """
    log_audit_event(
        event_type=AuditEventType.DATA_MODIFICATION,
        action=action,
        user=user,
        resource=resource,
        details=details,
        ip_address=ip_address
    )


def log_security_event(
    event_action: AuditAction,
    user: str,
    details: Dict[str, Any],
    ip_address: Optional[str] = None
) -> None:
    """
    Log security-related event
    
    Args:
        event_action: Type of security event
        user: User involved
        details: Event details
        ip_address: Client IP
    """
    log_audit_event(
        event_type=AuditEventType.SECURITY_EVENT,
        action=event_action,
        user=user,
        success=False,  # Security events are typically failures
        details=details,
        ip_address=ip_address
    )
