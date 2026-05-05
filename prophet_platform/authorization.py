"""Tenant-scoped RBAC primitives for production Prophet services."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
from typing import Iterable


SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,120}$")
LOCAL_IDENTITY_PROVIDERS = {
    "local",
    "local-dev",
    "local_label",
    "prophet-local-control",
}


class Role(str, Enum):
    VIEWER = "viewer"
    ANALYST = "analyst"
    APPROVER = "approver"
    AUDITOR = "auditor"
    ADMIN = "admin"


class Action(str, Enum):
    READ_READINESS = "read_readiness"
    READ_POLICY = "read_policy"
    READ_RUN = "read_run"
    CREATE_RUN = "create_run"
    GENERATE_FORECAST = "generate_forecast"
    RUN_FIXTURE_SANDBOX = "run_fixture_sandbox"
    GENERATE_EVIDENCE = "generate_evidence"
    APPROVE_EVIDENCE = "approve_evidence"
    DENY_EVIDENCE = "deny_evidence"
    EXPORT_HANDOFF = "export_handoff"
    MANAGE_POLICY = "manage_policy"
    MANAGE_USERS = "manage_users"
    MANAGE_INTEGRATIONS = "manage_integrations"
    READ_AUDIT = "read_audit"


VIEWER_ACTIONS = frozenset(
    {
        Action.READ_READINESS,
        Action.READ_POLICY,
        Action.READ_RUN,
    }
)
ANALYST_ACTIONS = VIEWER_ACTIONS | frozenset(
    {
        Action.CREATE_RUN,
        Action.GENERATE_FORECAST,
        Action.RUN_FIXTURE_SANDBOX,
        Action.GENERATE_EVIDENCE,
    }
)
APPROVER_ACTIONS = ANALYST_ACTIONS | frozenset(
    {
        Action.APPROVE_EVIDENCE,
        Action.DENY_EVIDENCE,
        Action.EXPORT_HANDOFF,
    }
)
AUDITOR_ACTIONS = frozenset(
    {
        Action.READ_READINESS,
        Action.READ_POLICY,
        Action.READ_RUN,
        Action.READ_AUDIT,
    }
)
ADMIN_ACTIONS = frozenset(Action)

ROLE_PERMISSIONS = {
    Role.VIEWER: VIEWER_ACTIONS,
    Role.ANALYST: ANALYST_ACTIONS,
    Role.APPROVER: APPROVER_ACTIONS,
    Role.AUDITOR: AUDITOR_ACTIONS,
    Role.ADMIN: ADMIN_ACTIONS,
}


class AuthorizationError(PermissionError):
    """Raised when a production action is not permitted."""


@dataclass(frozen=True)
class Principal:
    subject_id: str
    tenant_id: str
    roles: tuple[str, ...]
    identity_provider: str

    def __init__(
        self,
        *,
        subject_id: str,
        tenant_id: str,
        roles: Iterable[str | Role],
        identity_provider: str,
    ) -> None:
        object.__setattr__(self, "subject_id", _safe_id(subject_id, "subject_id"))
        object.__setattr__(self, "tenant_id", _safe_id(tenant_id, "tenant_id"))
        object.__setattr__(self, "roles", tuple(sorted({_role_value(role) for role in roles})))
        object.__setattr__(
            self,
            "identity_provider",
            _safe_id(identity_provider, "identity_provider"),
        )


@dataclass(frozen=True)
class TenantResource:
    tenant_id: str
    resource_type: str
    resource_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "tenant_id", _safe_id(self.tenant_id, "resource.tenant_id"))
        object.__setattr__(
            self,
            "resource_type",
            _safe_id(self.resource_type, "resource.resource_type"),
        )
        object.__setattr__(self, "resource_id", _safe_id(self.resource_id, "resource.resource_id"))


@dataclass(frozen=True)
class AuthorizationDecision:
    allowed: bool
    action: str
    reason: str
    subject_id: str
    principal_tenant_id: str
    resource_tenant_id: str
    roles: tuple[str, ...]
    production_mode: bool


def can(
    principal: Principal,
    action: str | Action,
    resource: TenantResource,
    *,
    production_mode: bool,
) -> AuthorizationDecision:
    """Return a deny-by-default authorization decision."""

    normalized_action = _action(action)
    base = {
        "action": normalized_action.value,
        "subject_id": principal.subject_id,
        "principal_tenant_id": principal.tenant_id,
        "resource_tenant_id": resource.tenant_id,
        "roles": principal.roles,
        "production_mode": production_mode,
    }
    if production_mode and principal.identity_provider in LOCAL_IDENTITY_PROVIDERS:
        return AuthorizationDecision(
            allowed=False,
            reason="local identity providers are not accepted in production mode",
            **base,
        )
    if principal.tenant_id != resource.tenant_id:
        return AuthorizationDecision(
            allowed=False,
            reason="principal tenant does not match resource tenant",
            **base,
        )
    if not principal.roles:
        return AuthorizationDecision(
            allowed=False,
            reason="principal has no roles",
            **base,
        )

    unknown_roles = sorted(set(principal.roles) - {role.value for role in Role})
    if unknown_roles:
        return AuthorizationDecision(
            allowed=False,
            reason=f"principal has unknown roles: {', '.join(unknown_roles)}",
            **base,
        )

    allowed_actions = frozenset(
        permission
        for role_value in principal.roles
        for permission in ROLE_PERMISSIONS[Role(role_value)]
    )
    if normalized_action in allowed_actions:
        return AuthorizationDecision(
            allowed=True,
            reason="allowed by tenant role",
            **base,
        )
    return AuthorizationDecision(
        allowed=False,
        reason="role does not allow action",
        **base,
    )


def authorize(
    principal: Principal,
    action: str | Action,
    resource: TenantResource,
    *,
    production_mode: bool,
) -> AuthorizationDecision:
    """Return the decision or raise AuthorizationError when denied."""

    decision = can(
        principal,
        action,
        resource,
        production_mode=production_mode,
    )
    if not decision.allowed:
        raise AuthorizationError(decision.reason)
    return decision


def _safe_id(value: str, field: str) -> str:
    if not isinstance(value, str) or not SAFE_ID_RE.fullmatch(value):
        raise ValueError(f"{field} must be a safe non-empty identifier")
    return value


def _role_value(role: str | Role) -> str:
    return role.value if isinstance(role, Role) else _safe_id(str(role), "role")


def _action(action: str | Action) -> Action:
    if isinstance(action, Action):
        return action
    try:
        return Action(str(action))
    except ValueError as exc:
        raise ValueError(f"unknown action: {action}") from exc
