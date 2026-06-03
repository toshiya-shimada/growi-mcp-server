from __future__ import annotations


class GrowiError(Exception):
    """Base class for GROWI integration failures."""


class GrowiAuthError(GrowiError):
    """Authentication failed (401)."""


class GrowiPermissionError(GrowiError):
    """Permission denied (403)."""


class GrowiNotFoundError(GrowiError):
    """Requested GROWI entity was not found (404)."""


class GrowiValidationError(GrowiError):
    """GROWI rejected the request as invalid, or local input validation failed."""


class GrowiConflictError(GrowiError):
    """GROWI reported a conflicting state (409)."""


class GrowiTransportError(GrowiError):
    """Network or protocol failure communicating with GROWI."""


class GrowiOwnershipError(GrowiError):
    """Operation blocked because the current user is not the page creator."""


class ConfigurationError(GrowiError):
    """Invalid runtime configuration."""
