"""Existing JSON shapes and internal event v1; no migration of saved artifacts."""
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Literal, NotRequired, Required, TypedDict


class JobState(StrEnum):
    PREPARING = "preparando"
    ANALYZING = "analizando"
    COMPLETE = "completo"
    PARTIAL = "parcial"
    ERROR = "error"
    INSUFFICIENT = "informacion_insuficiente"


class QuestionState(StrEnum):
    ANSWERING = "respondiendo"
    COMPLETE = "completada"
    ERROR = "error"


ACTIVE_STATES = frozenset({JobState.PREPARING, JobState.ANALYZING})


class EvidenceFile(TypedDict):
    path: str
    text: str
    sha: NotRequired[str]


class EvidenceReference(TypedDict):
    path: str
    line: int
    quote: str


class EvidenceSnapshot(TypedDict, total=False):
    repository: Required[str]
    commit: Required[str]
    files: Required[list[EvidenceFile]]
    branch: str
    excluded: list[dict]
    bytes_read: int
    bytes_downloaded: int
    scanners: list[dict]
    limits: dict[str, int]
    analyzed_at: str
    runtime: dict
    simulation: bool
    source_revision: str
    coverage: dict
    preparation: dict


class JobRecord(TypedDict):
    id: str
    repository: str
    estado: str
    created: str
    error: NotRequired[str]


@dataclass(frozen=True)
class StateEvent:
    """Internal notification of a persisted state, not a new REST/SSE response."""
    run_id: str
    state: str
    scope: Literal["run", "question"] = "run"
    question_id: str | None = None
    at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    version: int = field(default=1, init=False)

    def __post_init__(self):
        if self.scope not in {"run", "question"}:
            raise ValueError("Unknown event scope")
        allowed = JobState if self.scope == "run" else QuestionState
        if self.state not in {item.value for item in allowed}:
            raise ValueError("Unknown event state")
        if self.scope == "question" and not self.question_id:
            raise ValueError("Question events require question_id")

    def to_dict(self):
        return asdict(self)
