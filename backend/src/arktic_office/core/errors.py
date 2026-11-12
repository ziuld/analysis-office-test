"""Errors shared by domain, adapters and API; no provider details in messages."""


class AuditError(Exception):
    pass


class SpecialistTimeout(AuditError):
    """A local deadline prevents a specialist from starting or finishing a call."""


class GitHubNotFound(AuditError):
    pass
