"""Protect detected literal values at egress while retaining original local evidence."""
import json
import re
from pathlib import PurePosixPath


PROTECTED = "<valor protegido>"
TOKEN = re.compile(
    r"\b(?:(?:github_pat_|gh[pousr]_|sk-(?:proj-|live-)?|xox[baprs]-)[a-zA-Z0-9_-]{16,}"
    r"|(?:AKIA|ASIA)[A-Z0-9]{16})\b"
)
URL_PASSWORD = re.compile(r"\b[a-zA-Z][a-zA-Z0-9+.-]*://[^\s:/@]+:([^\s/@'\"<>]+)@")
CREDENTIAL = (r"(?:[\w-]*[_-])?(?:password|passwd|api[_-]?key|client[_-]?secret|access[_-]?token|"
              r"refresh[_-]?token|database[_-]?url|secret[_-]?key|secret|token)")
ASSIGNMENT = re.compile(r"\b" + CREDENTIAL + r"""\b ['"]? \s* [:=] \s*
    (?P<quote>['"])(?P<value>(?:\\.|(?!(?P=quote))[^\r\n\\])+)(?P=quote)""", re.I | re.X)
ESCAPED_ASSIGNMENT = re.compile(
    r'(?:(?<=\\n)|(?<=\\r)|\b)' + CREDENTIAL
    + r'\b(?:\\")?\s*[:=]\s*(?P<quote>\\")(?P<value>(?:(?!\\")[^\r\n])+)(?P=quote)', re.I)
ENV_VALUE = re.compile(r"(?im)^\s*(?:export\s+)?" + CREDENTIAL + r"\s*=\s*([^\r\n#]+)")
PRIVATE_KEY = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----([\s\S]*?)-----END [A-Z ]*PRIVATE KEY-----")


def literals(text):
    yield from (match.group() for match in TOKEN.finditer(text))
    yield from (match.group(1) for match in URL_PASSWORD.finditer(text))
    yield from (match["value"] for match in ASSIGNMENT.finditer(text)
                if not URL_PASSWORD.search(match["value"]))
    for key in PRIVATE_KEY.finditer(text):
        yield from (line.strip() for line in key.group(1).splitlines() if line.strip())


class CredentialProtection:
    def __init__(self, files=(), scanners=()):
        values = set()
        for file in files:
            content = file["text"]
            values.update(literals(content))
            if PurePosixPath(file["path"]).name.lower().startswith(".env"):
                values.update(match.group(1).strip().strip("\"'") for match in ENV_VALUE.finditer(content))
        for scanner in scanners:
            if scanner.get("name", "").lower().startswith("gitleaks"):
                for finding in scanner.get("original_output") or []:
                    secret = finding.get("Secret")
                    if isinstance(secret, str):
                        values.update(line.strip() for line in secret.splitlines())
        # Very short values and placeholders need assignment context to avoid hiding
        # ordinary words, JSON keys and other unrelated code.
        forms = {form for value in values if self.is_literal(value) and len(value) >= 4
                 and value.casefold() not in {"password", "passwd", "secret", "token", "api_key", "apikey",
                                               "api key", "clave api"}
                 for form in (value, json.dumps(value, ensure_ascii=False)[1:-1],
                              json.dumps(value, ensure_ascii=True)[1:-1])}
        self.pattern = re.compile("|".join(map(re.escape, sorted(forms, key=lambda v: (-len(v), v))))) if forms else None

    @staticmethod
    def is_literal(value):
        return bool(value and value != PROTECTED and not value.startswith(("${", "$(", "<", "{{")))

    def protect(self, text):
        def replace_assignment(match):
            value = match["value"]
            if not self.is_literal(value) or URL_PASSWORD.search(value) or PROTECTED in value:
                return match.group()
            return match.group()[:match.start("value") - match.start()] + PROTECTED + match["quote"]

        for assignment in (ESCAPED_ASSIGNMENT, ASSIGNMENT):
            text = assignment.sub(replace_assignment, text)
        if self.pattern:
            text = self.pattern.sub(PROTECTED, text)
        text = TOKEN.sub(PROTECTED, text)
        return URL_PASSWORD.sub(lambda match: match.group().replace(":" + match.group(1) + "@", ":" + PROTECTED + "@"), text)

    def publication(self, value):
        if isinstance(value, str):
            return self.protect(value)
        if isinstance(value, list):
            return [self.publication(item) for item in value]
        if isinstance(value, dict):
            return {key: PROTECTED if key == "Secret" and isinstance(item, str) and item else self.publication(item)
                    for key, item in value.items()}
        return value
