"""Errors shared by domain, adapters and API; no provider details in messages."""


class AuditError(Exception):
    pass


class GitHubNotFound(AuditError):
    pass
