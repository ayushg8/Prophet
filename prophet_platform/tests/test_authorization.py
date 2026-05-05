from __future__ import annotations

import unittest

from prophet_platform.authorization import (
    Action,
    AuthorizationError,
    Principal,
    Role,
    TenantResource,
    authorize,
    can,
)


class AuthorizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.resource = TenantResource(
            tenant_id="tenant-alpha",
            resource_type="evidence_bundle",
            resource_id="bundle-001",
        )

    def test_approver_can_approve_evidence_for_same_tenant(self) -> None:
        principal = Principal(
            subject_id="user-approver",
            tenant_id="tenant-alpha",
            roles=[Role.APPROVER],
            identity_provider="oidc-prod",
        )

        decision = authorize(
            principal,
            Action.APPROVE_EVIDENCE,
            self.resource,
            production_mode=True,
        )

        self.assertTrue(decision.allowed)
        self.assertEqual(decision.reason, "allowed by tenant role")

    def test_viewer_cannot_export_handoff(self) -> None:
        principal = Principal(
            subject_id="user-viewer",
            tenant_id="tenant-alpha",
            roles=[Role.VIEWER],
            identity_provider="oidc-prod",
        )

        decision = can(
            principal,
            Action.EXPORT_HANDOFF,
            self.resource,
            production_mode=True,
        )

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "role does not allow action")

    def test_cross_tenant_access_is_denied_even_for_admin(self) -> None:
        principal = Principal(
            subject_id="user-admin",
            tenant_id="tenant-beta",
            roles=[Role.ADMIN],
            identity_provider="oidc-prod",
        )

        with self.assertRaisesRegex(AuthorizationError, "principal tenant"):
            authorize(
                principal,
                Action.READ_RUN,
                self.resource,
                production_mode=True,
            )

    def test_local_identity_provider_is_rejected_in_production_mode(self) -> None:
        principal = Principal(
            subject_id="local-operator",
            tenant_id="tenant-alpha",
            roles=[Role.ADMIN],
            identity_provider="prophet-local-control",
        )

        decision = can(
            principal,
            Action.MANAGE_USERS,
            self.resource,
            production_mode=True,
        )

        self.assertFalse(decision.allowed)
        self.assertIn("local identity", decision.reason)

    def test_local_identity_provider_can_be_used_in_development_mode(self) -> None:
        principal = Principal(
            subject_id="local-operator",
            tenant_id="tenant-alpha",
            roles=[Role.ADMIN],
            identity_provider="prophet-local-control",
        )

        decision = can(
            principal,
            Action.MANAGE_USERS,
            self.resource,
            production_mode=False,
        )

        self.assertTrue(decision.allowed)

    def test_unknown_role_is_denied(self) -> None:
        principal = Principal(
            subject_id="user-unknown",
            tenant_id="tenant-alpha",
            roles=["superuser"],
            identity_provider="oidc-prod",
        )

        decision = can(
            principal,
            Action.READ_RUN,
            self.resource,
            production_mode=True,
        )

        self.assertFalse(decision.allowed)
        self.assertIn("unknown roles", decision.reason)

    def test_unsafe_identifiers_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "tenant_id"):
            Principal(
                subject_id="user-safe",
                tenant_id="../tenant-alpha",
                roles=[Role.VIEWER],
                identity_provider="oidc-prod",
            )


if __name__ == "__main__":
    unittest.main()
