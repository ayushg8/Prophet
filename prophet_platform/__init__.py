"""Production platform primitives for Prophet."""

from .authorization import (
    Action,
    AuthorizationDecision,
    AuthorizationError,
    Principal,
    Role,
    TenantResource,
    authorize,
    can,
)

__all__ = [
    "Action",
    "AuthorizationDecision",
    "AuthorizationError",
    "Principal",
    "Role",
    "TenantResource",
    "authorize",
    "can",
]
