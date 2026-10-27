"""A small, inspectable orchestration workflow for healthcare AI research.

This module intentionally uses deterministic placeholder agents rather than an
LLM or clinical database. It demonstrates orchestration boundaries, safety
review, human approval, execution simulation, and audit logging.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Iterable, Mapping
from uuid import uuid4


class WorkflowStatus(str, Enum):
    RECEIVED = "received"
    NEEDS_REVIEW = "needs_review"
    APPROVED = "approved"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"


@dataclass(frozen=True)
class PatientRequest:
    """Minimal synthetic request; do not put identifiable health data in logs."""

    request_id: str
    patient_ref: str
    question: str
    context: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Evidence:
    source_id: str
    title: str
    excerpt: str
    confidence: float
    provenance: str


@dataclass(frozen=True)
class CarePlanDraft:
    summary: str
    proposed_actions: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    uncertainty_notes: tuple[str, ...]


@dataclass(frozen=True)
class SafetyReview:
    approved_for_human_review: bool
    risk_flags: tuple[str, ...]
    required_checks: tuple[str, ...]
    rationale: str


@dataclass(frozen=True)
class WorkflowResult:
    workflow_id: str
    status: WorkflowStatus
    draft: CarePlanDraft | None
    safety_review: SafetyReview | None
    execution_result: str | None
    audit_events: tuple[Mapping[str, Any], ...]


class AuditLog:
    """Append-only in-memory audit log suitable for replacement by secure storage."""

    def __init__(self) -> None:
        self._events: list[dict[str, Any]] = []

    def record(self, event: str, workflow_id: str, **details: Any) -> None:
        self._events.append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event": event,
                "workflow_id": workflow_id,
                **details,
            }
        )

    @property
    def events(self) -> tuple[Mapping[str, Any], ...]:
        return tuple(self._events)


class IntakeAgent:
    def run(self, request: PatientRequest) -> PatientRequest:
        if not request.question.strip():
            raise ValueError("question must not be empty")
        if not request.patient_ref.strip():
            raise ValueError("patient_ref must not be empty")
        return request


class EvidenceAgent:
    """Deterministic stand-in for a governed retrieval system."""

    def __init__(self, knowledge_base: Iterable[Evidence]) -> None:
        self._knowledge_base = tuple(knowledge_base)

    def run(self, request: PatientRequest) -> tuple[Evidence, ...]:
        query_terms = set(request.question.lower().split())
        ranked = sorted(
            self._knowledge_base,
            key=lambda item: len(query_terms & set(item.excerpt.lower().split())),
            reverse=True,
        )
        return tuple(item for item in ranked if item.confidence >= 0.70)[:3]


class PlanningAgent:
    def run(self, request: PatientRequest, evidence: tuple[Evidence, ...]) -> CarePlanDraft:
        evidence_ids = tuple(item.source_id for item in evidence)
        actions = (
            "Summarize the request and retrieved evidence for a qualified reviewer.",
            "Verify relevant history, contraindications, and local clinical protocol.",
            "Escalate unresolved uncertainty rather than infer a diagnosis or treatment.",
        )
        notes = (
            "This is a research scaffold and does not make clinical decisions.",
            "Retrieved evidence must be independently verified before use.",
        )
        return CarePlanDraft(
            summary=f"Review request: {request.question}",
            proposed_actions=actions,
            evidence_ids=evidence_ids,
            uncertainty_notes=notes,
        )


class SafetyAgent:
    HIGH_RISK_TERMS = frozenset({"emergency", "suicide", "overdose", "chest pain", "bleeding"})

    def run(self, request: PatientRequest, draft: CarePlanDraft) -> SafetyReview:
        text = request.question.lower()
        flags = tuple(term for term in self.HIGH_RISK_TERMS if term in text)
        checks = ["qualified human review", "source and timestamp verification"]
        if flags:
            checks.append("immediate escalation to an appropriate emergency pathway")
        return SafetyReview(
            approved_for_human_review=True,
            risk_flags=flags,
            required_checks=tuple(checks),
            rationale="The workflow may prepare information, but it must not autonomously diagnose, prescribe, or reassure.",
        )


class HumanApprovalGate:
    def __init__(self, approval_fn: Callable[[CarePlanDraft, SafetyReview], bool] | None = None) -> None:
        self._approval_fn = approval_fn or (lambda _draft, _review: False)

    def approve(self, draft: CarePlanDraft, review: SafetyReview) -> bool:
        return review.approved_for_human_review and self._approval_fn(draft, review)


class ExecutionAgent:
    def run(self, draft: CarePlanDraft) -> str:
        return "Prepared a reviewer packet; no clinical action was executed."


class HealthcareOrchestrator:
    def __init__(
        self,
        knowledge_base: Iterable[Evidence],
        approval_fn: Callable[[CarePlanDraft, SafetyReview], bool] | None = None,
    ) -> None:
        self.intake = IntakeAgent()
        self.evidence = EvidenceAgent(knowledge_base)
        self.planner = PlanningAgent()
        self.safety = SafetyAgent()
        self.approval = HumanApprovalGate(approval_fn)
        self.executor = ExecutionAgent()

    def run(self, request: PatientRequest) -> WorkflowResult:
        workflow_id = str(uuid4())
        audit = AuditLog()
        audit.record("workflow_started", workflow_id, request_id=request.request_id)
        try:
            self.intake.run(request)
            audit.record("intake_validated", workflow_id)
            evidence = self.evidence.run(request)
            audit.record("evidence_retrieved", workflow_id, evidence_count=len(evidence))
            draft = self.planner.run(request, evidence)
            audit.record("draft_created", workflow_id, evidence_ids=draft.evidence_ids)
            review = self.safety.run(request, draft)
            audit.record("safety_review_completed", workflow_id, risk_flags=review.risk_flags)
            if not self.approval.approve(draft, review):
                audit.record("human_approval_required", workflow_id)
                return WorkflowResult(workflow_id, WorkflowStatus.NEEDS_REVIEW, draft, review, None, audit.events)
            audit.record("human_approval_received", workflow_id)
            execution_result = self.executor.run(draft)
            audit.record("execution_simulated", workflow_id)
            return WorkflowResult(workflow_id, WorkflowStatus.COMPLETED, draft, review, execution_result, audit.events)
        except (ValueError, TypeError) as exc:
            audit.record("workflow_failed", workflow_id, error=str(exc))
            return WorkflowResult(workflow_id, WorkflowStatus.FAILED, None, None, None, audit.events)


def result_to_dict(result: WorkflowResult) -> dict[str, Any]:
    """Serialize a result without requiring a third-party dependency."""
    data = asdict(result)
    data["status"] = result.status.value
    return data
